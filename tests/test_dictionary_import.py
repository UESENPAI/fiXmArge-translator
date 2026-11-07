"""Pinned local dictionary ingestion preserves claims and never changes sources."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fixmarge.dictionary_import import import_dictionaries
from fixmarge.prepare import stable_id
from scripts import import_rag_dictionaries


def sha(content):
    return hashlib.sha256(content).hexdigest()


def base_entry(form, en=(), *, conflict=False):
    return {'id': stable_id(form), 'form': form, 'aliases': [],
            'senses': {'en': list(en), 'ja': [], 'ko': []},
            'status': 'unreviewed', 'rights_status': 'game_derived_not_eligible',
            'group_id': 'existing-family-' + form, 'sources': ['original'],
            'source_values': [{'source': 'original', 'row': 2}], 'has_conflict': conflict}


class DictionaryImportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self._fixture(self.root)

    def _fixture(self, root):
        for folder in ('data/processed', 'data/raw/candidates', 'data/research', 'configs'):
            (root / folder).mkdir(parents=True, exist_ok=True)
        self.base = [base_entry('sinruits', ['truth']), base_entry('niNeEr', ['older brother'], conflict=True),
                     base_entry('merc·lee', ['mercy']), base_entry('shi-des', ['death'])]
        (root / 'data/processed/lexicon.jsonl').write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in self.base))
        (root / 'data/processed/rules.jsonl').write_bytes(b'')
        self.rows = [('Conjuctions', 'Japanese Conjunction', ''),
                     ('sinruits', 'Reality', "English 'sin'+'fruits'?"),
                     ('DaRk rai', 'Dark', 'fan hypothesis'),
                     ('DaRk rai', 'Dark', 'fan hypothesis'),
                     ('kee’on', 'A word; another (a/b)', 'unreviewed etymology')]
        self.claim_document = {'schema_version': 1, 'source_id': 'ko-fixture', 'source_url': 'https://source.test/ko',
            'review_status': 'unreviewed_source_claims', 'rights_status': 'not_cleared',
            'source_author': 'fan author', 'method': 'source words preserved',
            'claims': [{'form': 'merc•lee', 'ko': '자비'}, {'form': 'shi-des', 'ko': '죽음, 마지막'}]}
        self._write_registry(root)

    def _pinned(self, root, name):
        content = (root / name).read_bytes()
        return {'path': name, 'sha256': sha(content), 'bytes': len(content)}

    def _write_registry(self, root=None):
        root = root or self.root
        buffer = io.StringIO(newline='')
        writer = csv.writer(buffer)
        writer.writerow(['Majo-ish', 'Meaning', 'Origination'])
        writer.writerows(self.rows)
        (root / 'data/raw/candidates/en.csv').write_text(buffer.getvalue(), newline='')
        (root / 'data/research/ko.json').write_text(json.dumps(self.claim_document, ensure_ascii=False))
        english = {'id': 'en-fixture', 'format': 'csv', 'language': 'en',
            **self._pinned(root, 'data/raw/candidates/en.csv'),
            'source_url': 'https://source.test/en', 'revision': 'pinned-commit',
            'expected_headers': ['Majo-ish', 'Meaning', 'Origination'],
            'columns': {'form': 'Majo-ish', 'meaning': 'Meaning', 'etymology': 'Origination'},
            'skip_forms': ['Conjuctions'], 'review_status': 'unreviewed_source_candidate', 'rights_status': 'not_cleared'}
        source_manifest = {'items': [{'source_id': english['id'], 'source_url': english['source_url'],
            'path': english['path'], 'sha256': english['sha256'], 'bytes': english['bytes'],
            'revision': english['revision'], 'columns': english['expected_headers'],
            'review_status': english['review_status'], 'rights_status': english['rights_status']}]}
        (root / 'data/raw/candidates/manifest.json').write_text(json.dumps(source_manifest))
        english['source_manifest'] = self._pinned(root, 'data/raw/candidates/manifest.json')
        self.config = {'schema_version': 1, 'base': {
            'lexicon': self._pinned(root, 'data/processed/lexicon.jsonl'),
            'rules': self._pinned(root, 'data/processed/rules.jsonl')}, 'sources': [english,
            {'id': 'ko-fixture', 'format': 'claims_json', 'language': 'ko',
             **self._pinned(root, 'data/research/ko.json'), 'source_url': 'https://source.test/ko',
             'columns': {'form': 'form', 'meaning': 'ko'},
             'review_status': 'unreviewed_source_claims', 'rights_status': 'not_cleared'}]}
        self._save_config(root)

    def _save_config(self, root=None):
        (root or self.root).joinpath('configs/imports.json').write_text(json.dumps(self.config))

    def run_import(self, name='output'):
        return import_dictionaries(root=self.root, registry='configs/imports.json', output=name)

    def imported(self, name='output'):
        return {e['form']: e for e in map(json.loads, (self.root / name / 'lexicon.jsonl').read_text().splitlines())}

    def test_additive_import_preserves_base_fields_meanings_conflicts_and_all_inputs(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        report = self.run_import()
        rows = self.imported()
        self.assertEqual((report['base_entries'], report['merged_entries'], report['new_entries']), (4, 6, 2))
        self.assertEqual(rows['sinruits']['senses']['en'], ['truth', 'Reality'])
        for original in self.base:
            merged = rows[original['form']]
            for key in ('id', 'form', 'status', 'rights_status', 'group_id'):
                self.assertEqual(merged[key], original[key])
            for language, values in original['senses'].items():
                self.assertEqual(merged['senses'][language][:len(values)], values)
        self.assertEqual(rows['niNeEr'], next(e for e in self.base if e['form'] == 'niNeEr'))
        difference = rows['sinruits']['source_disagreements'][0]
        self.assertEqual(difference['previous_senses'], ['truth'])
        self.assertEqual(difference['imported_senses'], ['Reality'])
        self.assertFalse(difference['semantic_contradiction_verified'])
        self.assertTrue(rows['sinruits']['has_conflict'])
        self.assertTrue(report['all_input_hashes_verified_and_unchanged'])
        self.assertFalse(report['training_performed'])
        self.assertFalse(report['network_access'])
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)
        locks = json.loads((self.root / 'output/source-lock.json').read_text())
        self.assertIn('data/raw/candidates/en.csv', locks)
        self.assertIn('data/research/ko.json', locks)
        self.assertEqual((self.root / 'output/rules.jsonl').read_bytes(), b'')

    def test_duplicate_rows_keep_two_provenance_records_without_duplicate_senses(self):
        self.run_import()
        rows = self.imported()
        self.assertEqual(rows['DaRk rai']['senses']['en'], ['Dark'])
        self.assertEqual([v['row'] for v in rows['DaRk rai']['source_values']], [4, 5])
        self.assertFalse(rows['DaRk rai'].get('has_conflict', False))
        self.assertEqual(rows["kee'on"]['aliases'], ['kee’on'])
        self.assertEqual(rows["kee'on"]['senses']['en'], ['A word', 'another (a/b)'])
        self.assertEqual(rows["kee'on"]['etymology'][0]['status'], 'fan_hypothesis')
        self.assertEqual(rows["kee'on"]['source_values'][0]['raw_row']['Majo-ish'], 'kee’on')

    def test_case_only_english_change_is_not_a_semantic_difference(self):
        self.rows[1] = ('sinruits', 'Truth', '')
        self._write_registry()
        self.run_import()
        merged = self.imported()['sinruits']
        self.assertEqual(merged['senses']['en'], ['truth', 'Truth'])
        self.assertFalse(merged['has_conflict'])
        self.assertNotIn('source_disagreements', merged)
        self.assertEqual(merged['source_values'][-1]['raw_row']['Meaning'], 'Truth')

    def test_base_source_and_manifest_hash_mismatches_reject_before_output_creation(self):
        paths = ['data/processed/lexicon.jsonl', 'data/raw/candidates/en.csv', 'data/raw/candidates/manifest.json']
        for name in paths:
            with self.subTest(path=name):
                path = self.root / name
                old = path.read_bytes()
                path.write_bytes(old + b' ')
                with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
                    self.run_import()
                self.assertFalse((self.root / 'output').exists())
                path.write_bytes(old)

    def test_existing_empty_or_nonempty_output_is_never_overwritten(self):
        out = self.root / 'output'
        out.mkdir()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.run_import()
        sentinel = out / 'sentinel'
        sentinel.write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.run_import()
        self.assertEqual(sentinel.read_bytes(), b'keep')

    def test_bad_headers_and_pinned_manifest_identity_are_rejected(self):
        self.config['sources'][0]['expected_headers'] = ['wrong']
        self._save_config()
        with self.assertRaisesRegex(ValueError, 'columns mismatch'):
            self.run_import()
        self._write_registry()
        self.config['sources'][0]['revision'] = 'incorrect-revision'
        self._save_config()
        with self.assertRaisesRegex(ValueError, 'revision mismatch'):
            self.run_import()
        self._write_registry()
        self.config['sources'][1]['id'] = 'wrong-source'
        self._save_config()
        with self.assertRaisesRegex(ValueError, 'identity or schema mismatch'):
            self.run_import()
        self.assertFalse((self.root / 'output').exists())

    def test_korean_original_wording_source_metadata_and_bullet_alias_are_preserved(self):
        report = self.run_import()
        rows = self.imported()
        self.assertEqual(rows['shi-des']['senses']['ko'], ['죽음, 마지막'])
        self.assertEqual(rows['merc·lee']['senses']['ko'], ['자비'])
        self.assertIn('merc•lee', rows['merc·lee']['aliases'])
        value = rows['shi-des']['source_values'][-1]
        self.assertEqual(value['source'], 'ko-fixture')
        self.assertEqual(value['source_url'], self.claim_document['source_url'])
        self.assertEqual(value['snapshot_metadata']['source_author'], 'fan author')
        self.assertEqual(value['status'], 'unreviewed_source_claims')
        self.assertEqual(rows['shi-des']['ko_status'], 'unreviewed_fan_source_claims')
        self.assertEqual(rows['shi-des']['status'], 'unreviewed')
        self.assertEqual(report['merged_Korean_entries'], 2)
        self.assertFalse(report['source_review_or_publication_clearance_granted'])

    def test_new_json_source_registration_uses_same_cli_without_network_or_training(self):
        future = deepcopy(self.claim_document)
        future.update(source_id='future-ja', source_url='https://source.test/ja',
                      claims=[{'form': 'FutureWord', 'ja': '未来'}])
        (self.root / 'data/research/future.json').write_text(json.dumps(future, ensure_ascii=False))
        self.config['sources'].append({'id': 'future-ja', 'format': 'claims_json', 'language': 'ja',
            **self._pinned(self.root, 'data/research/future.json'), 'source_url': future['source_url'],
            'columns': {'form': 'form', 'meaning': 'ja'},
            'review_status': future['review_status'], 'rights_status': future['rights_status']})
        self._save_config()
        stdout = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=AssertionError('No source fetch permitted')), redirect_stdout(stdout):
            code = import_rag_dictionaries.main(['--root', str(self.root), '--registry', 'configs/imports.json', '--output', 'output'])
        self.assertEqual(code, 0)
        self.assertEqual(self.imported()['FutureWord']['senses']['ja'], ['未来'])
        self.assertFalse(json.loads(stdout.getvalue())['training_performed'])
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            import_rag_dictionaries.main(['--root', str(self.root)])


if __name__ == '__main__':
    unittest.main()
