import ast
from collections import OrderedDict
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
import retriever

CFG = tomllib.loads((ROOT / 'server/retrieval.toml').read_text())

def item(key, doc, text, score=1):
    return dict(chunk_id=key, document_id=doc, text=text, reranker_score=score)

class SelectionTests(unittest.TestCase):
    def choose(self, lanes, baseline=None, **overrides):
        cfg = {**CFG, **overrides}
        return retriever.select_candidates(lanes, baseline or [], cfg, lambda _: 10)

    def test_obligations_reserved_before_high_scoring_global_fill(self):
        a = item('a', 'd1', 'mechanism temperature species')
        b = item('b', 'd2', 'limitations field measurements')
        c = item('c', 'd3', 'general highly ranked summary', 10)
        selected, _ = self.choose([[a], [b]], [c], final_chunks=2)
        self.assertEqual([p['chunk_id'] for p in selected], ['a', 'b'])

    def test_budget_rejects_overflow(self):
        selected, used = self.choose([[item('a','d1','very long passage')]], maximum_context_tokens=5)
        self.assertEqual((selected, used), ([], 0))

    def test_shared_passage_can_support_multiple_candidate_lanes(self):
        p = item('a', 'd1', 'joint mechanism and findings')
        selected, used = self.choose([[p], [p]], final_chunks=1)
        self.assertEqual(len(selected), 1)
        self.assertEqual(used, 10)

    def test_duplicate_text_does_not_fill_other_slots(self):
        selected, _ = self.choose([], [item('a','d1','same long passage words'), item('b','d2','same long passage words')])
        self.assertEqual(len(selected), 1)

    def test_document_ceiling(self):
        selected, _ = self.choose([[item('a','d1','first distinct finding')],
            [item('b','d1','second entirely different result')]], obligation_max_chunks_per_document=1)
        self.assertEqual(len(selected), 1)

    def test_negative_reranker_excluded(self):
        selected, _ = self.choose([[item('a','d1','irrelevant evidence', -1)]])
        self.assertEqual(selected, [])

class BoundaryAndStorageTests(unittest.TestCase):
    def test_path_escape_blocked(self):
        with self.assertRaises(ValueError):
            retriever.local_path('../../outside')

    def test_fts_input_quoted(self):
        self.assertEqual(retriever.fts_query('climate OR "change"'), '"climate" OR "OR" OR "change"')
        self.assertEqual(retriever.fts_query('!!!'), '')

    def test_keyword_access_is_read_only_and_preserves_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with closing(sqlite3.connect(root/'lexical.sqlite3')) as db:
                with db:
                    db.execute('CREATE TABLE chunks(chunk_id TEXT PRIMARY KEY, payload_json TEXT)')
                    p = {'chunk_id':'a','document_id':'d1','text':'source text','title':'Verified title'}
                    db.execute('INSERT INTO chunks VALUES (?,?)', ('a', json.dumps(p)))
            engine = retriever.Retriever.__new__(retriever.Retriever)
            engine.active = {'lexical_db':'lexical.sqlite3'}
            with patch.object(retriever, 'ROOT', root):
                self.assertEqual(engine.payload('a'), p)
                with self.assertRaises(ValueError):
                    engine.payload('missing')
                with engine.db() as db:
                    with self.assertRaises(sqlite3.OperationalError):
                        db.execute('DELETE FROM chunks')

class PacketTests(unittest.TestCase):
    def engine(self):
        engine = retriever.Retriever.__new__(retriever.Retriever)
        engine.lock = threading.Lock()
        engine.packets = OrderedDict()
        engine.cfg = dict(CFG)
        engine.active = {'corpus_version':'synthetic-fixture'}
        engine.encoder = type('Encoder', (), {'encode':lambda self, s: s.split()})()
        engine.rank = lambda question, multiplier=1: [item('a', 'd1', 'adequate source passage')]
        return engine

    def test_ranked_candidate_is_not_semantic_approval(self):
        p = self.engine().retrieve('question', ['obligation'])
        self.assertEqual(p['obligations'][0]['status'], 'validation_unavailable')
        self.assertTrue(p['semantic_validation_required'])
        self.assertFalse(p['decoder_exact_token_count'])
        self.assertEqual(p['obligations'][0]['candidate_evidence_ids'], ['E1'])

    def test_rescue_uses_double_depth_once(self):
        engine = self.engine()
        p = engine.retrieve('question', ['obligation'])
        depths = []
        engine.rank = lambda question, multiplier=1: depths.append(multiplier) or [item('a','d1','source passage')]
        q = engine.retrieve('question', ['obligation'], p['packet_id'])
        self.assertEqual(depths, [2, 2])
        self.assertEqual(q['rescue_count'], 1)
        self.assertNotEqual(p['packet_id'], q['packet_id'])
        with self.assertRaises(ValueError):
            engine.retrieve('question', ['obligation'], p['packet_id'])
        with self.assertRaises(ValueError):
            engine.retrieve('question', ['obligation'], q['packet_id'])

    def test_foreign_question_cannot_rescue_packet(self):
        engine = self.engine()
        p = engine.retrieve('original', ['obligation'])
        with self.assertRaises(ValueError):
            engine.retrieve('changed', ['obligation'], p['packet_id'])

    def test_evicted_packet_is_not_reused(self):
        engine = self.engine()
        engine.cfg['packet_cache_size'] = 1
        p = engine.retrieve('first', ['obligation'])
        engine.retrieve('second', ['obligation'])
        with self.assertRaises(ValueError):
            engine.retrieve('first', ['obligation'], p['packet_id'])

    def test_obligations_are_bounded(self):
        with self.assertRaises(ValueError):
            self.engine().retrieve('question', ['item'] * 11)

class SourceAndConfigTests(unittest.TestCase):
    def test_source_syntax(self):
        for path in (ROOT / 'server').glob('*.py'):
            ast.parse(path.read_text(encoding='utf-8'))

    def test_client_and_canonical_config(self):
        c = tomllib.loads((ROOT/'client/config.example.toml').read_text())
        self.assertEqual(c['mcp_servers']['giis_rag']['url'], 'http://127.0.0.1:18765/mcp')
        self.assertTrue(CFG['enable_obligation_aware_retrieval'])
        self.assertEqual((CFG['final_chunks'],CFG['maximum_context_tokens']), (12,6144))

if __name__ == '__main__':
    unittest.main()
