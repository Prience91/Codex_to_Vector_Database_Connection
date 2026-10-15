"""Folder-contained CPU retrieval; semantic decisions belong to the client agent."""
import argparse
from collections import OrderedDict, Counter
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
import time
import tomllib
import uuid

ROOT = Path(os.environ.get('GIIS_ROOT', Path(__file__).resolve().parent.parent)).resolve()

def local_path(value):
    p = (ROOT / value).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError('Path escapes GIIS_RAG')
    return p

def read_json(name):
    return json.loads(local_path(name).read_text(encoding='utf-8-sig'))

def fts_query(query):
    return ' OR '.join('"' + t + '"' for t in re.findall(r'[\w-]+', query)[:32])

def select_candidates(lanes, baseline, cfg, count_tokens):
    selected, ids, per_doc, used = [], set(), Counter(), 0
    def add(item):
        nonlocal used
        if item['chunk_id'] in ids:
            return True
        doc = item['document_id']
        if len(selected) >= cfg['final_chunks'] or per_doc[doc] >= cfg['obligation_max_chunks_per_document']:
            return False
        if item['reranker_score'] < cfg['min_reranker_score']:
            return False
        words = set(re.findall(r'\w+', item['text'].casefold()))
        for prior in selected:
            other = set(re.findall(r'\w+', prior['text'].casefold()))
            if len(words & other) / max(len(words | other), 1) >= cfg.get('context_deduplication_similarity', 0.85):
                return False
        cost = count_tokens(json.dumps(item, ensure_ascii=False))
        if used + cost > cfg['maximum_context_tokens']:
            return False
        selected.append(item)
        ids.add(item['chunk_id'])
        per_doc[doc] += 1
        used += cost
        return True
    # Each obligation gets first refusal before general relevance fills the bundle.
    for lane in lanes:
        for item in lane:
            if add(item):
                break
    pool = {i['chunk_id']: i for i in baseline + [i for lane in lanes for i in lane]}
    while pool and len(selected) < cfg['final_chunks']:
        key = max(pool, key=lambda k: pool[k]['reranker_score'] -
                  cfg.get('source_diversity_penalty', 0.08) * per_doc[pool[k]['document_id']])
        add(pool.pop(key))
    return selected, used

class Retriever:
    def __init__(self):
        self.lock = threading.Lock()
        self.packets = OrderedDict()
        self.cfg = tomllib.loads(local_path('server/retrieval.toml').read_text())
        if self.cfg.get('enable_obligation_aware_retrieval') is not True:
            raise ValueError('This service requires obligation-aware retrieval')
        ready = read_json('READY.json')
        if hashlib.sha256(local_path('source_manifest.json').read_bytes()).hexdigest() != ready['source_manifest_sha256']:
            raise ValueError('Transfer manifest mismatch')
        self.active = read_json('active_index.json')
        import chromadb
        import tiktoken
        import torch
        from sentence_transformers import SentenceTransformer, CrossEncoder
        torch.set_num_threads(4)
        self.encoder = tiktoken.get_encoding(self.cfg['context_token_encoding'])
        self.model = SentenceTransformer(str(local_path(self.active['embedding_model_path'])), device='cpu', local_files_only=True)
        self.reranker = CrossEncoder(str(local_path(self.cfg['reranker_path'])), device='cpu', local_files_only=True)
        self.client = chromadb.PersistentClient(path=str(local_path(self.active['chroma_dir'])))
        self.collection = self.client.get_collection(self.active['collection_name'], embedding_function=None)
        if self.collection.count() != self.active['chunk_count']:
            raise ValueError('Collection count mismatch')

    @contextmanager
    def db(self):
        db = sqlite3.connect(local_path(self.active['lexical_db']).as_uri() + '?mode=ro', uri=True)
        try:
            db.execute('PRAGMA query_only=ON')
            yield db
        finally:
            db.close()

    def payload(self, chunk_id):
        with self.db() as db:
            row = db.execute('SELECT payload_json FROM chunks WHERE chunk_id=?', (chunk_id,)).fetchone()
        if not row:
            raise ValueError('Chunk absent from keyword index')
        return json.loads(row[0])

    def rank(self, query, multiplier=1):
        if not query.strip() or len(query) > 4000:
            raise ValueError('Query must contain 1–4000 characters')
        vector = self.model.encode([query], normalize_embeddings=True).tolist()
        if len(vector[0]) != 384:
            raise ValueError('Embedding dimension mismatch')
        dense = self.collection.query(query_embeddings=vector,
            n_results=self.cfg['dense_candidates'] * multiplier, include=['distances'])
        good = [(key, 1-float(distance)) for key, distance in zip(dense['ids'][0], dense['distances'][0])
                if 1-float(distance) >= self.cfg['min_dense_similarity']]
        if not good:
            return []
        phrase = fts_query(query)
        with self.db() as db:
            lexical = db.execute('SELECT f.chunk_id FROM chunks_fts f WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT ?',
                (phrase, self.cfg['lexical_candidates'] * multiplier)).fetchall() if phrase else []
        scores, similarities = {}, dict(good)
        for lane in ([key for key, _ in good], [row[0] for row in lexical]):
            for pos, key in enumerate(lane, 1):
                scores[key] = scores.get(key, 0) + 1/(self.cfg['rrf_k'] + pos)
        keys = sorted(scores, key=scores.get, reverse=True)[:self.cfg['rerank_candidates'] * multiplier]
        items = [self.payload(key) for key in keys]
        ranks = self.reranker.predict([(query, p['text']) for p in items])
        for item, score in zip(items, ranks):
            item['reranker_score'] = float(score)
            item['fusion_score'] = scores[item['chunk_id']]
            item['dense_similarity'] = similarities.get(item['chunk_id'])
        return sorted(items, key=lambda p: p['reranker_score'], reverse=True)

    def retrieve(self, question, obligations=None, rescue_packet_id=None):
        obligations = obligations or []
        if len(obligations) > 10 or any(not isinstance(o, str) or not o.strip() or len(o) > 1500 for o in obligations):
            raise ValueError('Use up to ten nonempty obligations, each at most 1500 characters')
        with self.lock:
            multiplier, rescue_count = 1, 0
            if rescue_packet_id:
                old = self.packets.get(rescue_packet_id)
                if not old or old['question'] != question or old['rescue_count']:
                    raise ValueError('Rescue requires matching live packet and is permitted once')
                old['rescue_count'] = 1
                multiplier, rescue_count = self.cfg['obligation_candidate_multiplier'], 1
            baseline = self.rank(question, multiplier)
            lanes = [self.rank(o, multiplier) for o in obligations]
            selected, tokens = select_candidates(lanes, baseline, self.cfg, lambda text: len(self.encoder.encode(text)))
            for i, item in enumerate(selected, 1):
                item['evidence_id'] = f'E{i}'
            mapping = []
            for obligation, lane in zip(obligations, lanes):
                keys = {i['chunk_id'] for i in lane}
                mapping.append({'obligation_index': len(mapping) + 1,
                    'obligation': obligation, 'status': 'pending_client_validation',
                    'candidate_evidence_ids': [p['evidence_id'] for p in selected if p['chunk_id'] in keys]})
            packet = {'schema_version': 'giis.evidence_packet.v2',
                'packet_id': uuid.uuid4().hex, 'question': question, 'obligations': mapping,
                'evidence': selected, 'rescue_count': rescue_count, 'corpus_version': self.active['corpus_version'],
                'context_tokens': tokens, 'token_encoding': self.cfg['context_token_encoding'],
                'decoder_exact_token_count': False, 'semantic_validation_required': True,
                'semantic_validation_owner': 'codex_client',
                'semantic_validation_status': 'pending_client_validation',
                'semantic_validation_performed': False,
                'coverage_record_required': True,
                'answer_policy': 'mcp_evidence_only',
                'connection_policy': 'refuse_substantive_answer_if_mcp_unavailable',
                'planning_status': 'client_planned' if obligations else 'preliminary_search',
                'reranker': 'cross-encoder/ms-marco-MiniLM-L-6-v2'}
            self.packets[packet['packet_id']] = packet
            while len(self.packets) > self.cfg['packet_cache_size']:
                self.packets.popitem(last=False)
            return packet

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true', required=True)
    parser.parse_args()
    import resource
    start = time.monotonic()
    retriever = Retriever()
    packet = retriever.retrieve('How does climate change affect biodiversity?')
    if not packet['evidence']:
        raise SystemExit('Smoke query returned no qualifying evidence')
    print(json.dumps({'status': 'basic_retrieval_passed', 'seconds': time.monotonic()-start,
        'peak_rss_mib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        'chunks': retriever.collection.count(), 'passages': len(packet['evidence']),
        'top_title': packet['evidence'][0].get('title'), 'semantic_coverage_certified': False}, indent=2))
