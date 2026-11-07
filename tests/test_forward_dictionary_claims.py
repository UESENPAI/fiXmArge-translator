"""Forward dictionary claims retain unresolved alternatives without changing facts."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from fixmarge.demo import DemoService, present_result
from fixmarge.rag import LexiconRAG


def entry(identifier, form='ClaiM', *, en=(), ja=(), ko=(), conflict=True):
    return {'id': identifier, 'form': form, 'aliases': [],
            'senses': {'en': list(en), 'ja': list(ja), 'ko': list(ko)},
            'has_conflict': conflict, 'status': 'unreviewed', 'sources': ['fixture'],
            'rights_status': 'game_derived_not_eligible'}


def sentence(text=None, identifiers=()):
    return json.dumps({'tentative_translation': text, 'evidence_ids': list(identifiers),
                       'uncertainties': ['Dictionary conflict and grammar remain unresolved.']}, ensure_ascii=False)


def korean(*values):
    return json.dumps({'glosses': [{'entry_id': identifier, 'korean': words}
                                   for identifier, words in values]}, ensure_ascii=False)


class ForwardDictionaryClaimsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.external = Path(temporary.name) / 'no-external-index'
        self.entries = [entry('truth', en=['truth'], ja=['真実'], ko=['진실']),
                        entry('reality', en=['reality'], ja=['現実'], ko=['현실'])]

    def service(self, entries, outputs=()):
        rag = LexiconRAG(entries=entries, rules=[], external_dir=self.external)
        runner = Mock()
        runner.generate.side_effect = list(outputs)
        factory = Mock(return_value=runner)
        service = DemoService(rag_factory=Mock(return_value=rag), runner_factory=factory,
                              standard_lookup=Mock(return_value={
                                  'available': False, 'entries': [], 'attributions': []}),
                              external_dir=self.external)
        return service, rag, runner, factory

    def missing_korean_entries(self):
        return [entry('truth', en=['truth'], ja=['真実']),
                entry('reality', en=['reality'], ja=['現実'])]

    def test_forward_claims_keep_all_ko_en_ja_alternatives_and_leave_null_contract_unchanged(self):
        original = deepcopy(self.entries)
        expected = {'ko': ['진실', '현실'], 'en': ['truth', 'reality'], 'ja': ['真実', '現実']}
        for target, alternatives in expected.items():
            with self.subTest(target=target):
                service, rag, runner, factory = self.service(self.entries)
                before = deepcopy(rag.lookup('ClaiM', 'fix-to-' + target))
                self.assertIsNone(before['lexical_contract']['expected_translation'])
                self.assertEqual(before['lexical_contract']['abstention_reasons'], ['source_conflict'])
                result = service.run('ClaiM', 'fix', target, generate=True)
                self.assertEqual(result['answer_source'], 'dictionary_claims')
                self.assertEqual(result['answer_kind'], 'unresolved_dictionary_alternatives')
                self.assertNotIn('dictionary_answer', result)
                self.assertNotIn('diagnostic', result)
                answer = result['dictionary_claims_answer']
                self.assertEqual(answer['translation'], '; '.join(alternatives))
                self.assertEqual([a['text'] for a in answer['alternatives']], alternatives)
                self.assertEqual(set(answer['evidence_ids']), {'truth', 'reality'})
                self.assertEqual(set(answer['source_conflict_entry_ids']), {'truth', 'reality'})
                self.assertFalse(answer['conflicts_resolved'])
                self.assertFalse(answer['model_generated'])
                self.assertFalse(answer['sentence_verified'])
                self.assertFalse(result['generation_performed'])
                self.assertEqual(present_result(result)[0], '⚠ ' + '; '.join(alternatives))
                self.assertEqual(rag.lookup('ClaiM', 'fix-to-' + target), before)
                runner.generate.assert_not_called()
                factory.assert_not_called()
        self.assertEqual(self.entries, original)
        self.assertFalse(self.external.exists())

    def test_question_mark_case_ambiguity_and_partial_input_do_not_bypass_model_diagnostics(self):
        cases = [
            ('ClaiM', [entry('uncertain', en=['older sister?'], ja=['姉？'])]),
            ('CLAIM', [entry('first', form='Claim', en=['truth']),
                       entry('second', form='cLaim', en=['reality'])]),
            ('ClaiM missing', deepcopy(self.entries)),
        ]
        for text, entries in cases:
            with self.subTest(text=text):
                raw = sentence()
                service, rag, runner, _ = self.service(entries, [raw])
                before = deepcopy(rag.lookup(text, 'fix-to-en'))
                result = service.run(text, 'fix', 'en', generate=True)
                self.assertNotIn('dictionary_claims_answer', result)
                self.assertNotIn('dictionary_answer', result)
                self.assertEqual(result['answer_source'], 'model_with_dictionary')
                self.assertEqual(result['diagnostic']['raw_output'], raw)
                self.assertEqual(runner.generate.call_count, 1)
                self.assertFalse(result['sentence_verified'])
                self.assertEqual(rag.lookup(text, 'fix-to-en'), before)

    def test_reverse_conflicted_lookup_keeps_the_existing_model_path(self):
        entries = [entry('first', form='FirstForm', en=['truth']),
                   entry('second', form='SecondForm', en=['truth'])]
        original = deepcopy(entries)
        raw = sentence(None, ['first', 'second'])
        service, rag, runner, _ = self.service(entries, [raw])
        before = deepcopy(rag.lookup('truth', 'en-to-fix'))
        self.assertIsNone(before['lexical_contract']['expected_translation'])
        result = service.run('truth', 'en', 'fix', generate=True)
        self.assertNotIn('dictionary_claims_answer', result)
        self.assertEqual(result['answer_source'], 'model_with_dictionary')
        self.assertEqual(result['diagnostic']['raw_output'], raw)
        self.assertEqual(runner.generate.call_count, 1)
        self.assertEqual(rag.lookup('truth', 'en-to-fix'), before)
        self.assertEqual(entries, original)

    def test_korean_conflict_with_two_machine_alternatives_keeps_all_claims_in_one_call(self):
        entries = self.missing_korean_entries()
        original = deepcopy(entries)
        raw = korean(('truth', ['진실']), ('reality', ['현실']))
        service, rag, runner, _ = self.service(entries, [raw])
        before = deepcopy(rag.lookup('ClaiM', 'fix-to-ko'))
        result = service.run('ClaiM', 'fix', 'ko', generate=True)
        self.assertEqual(runner.generate.call_count, 1)
        self.assertEqual(result['answer_source'], 'model_with_dictionary')
        self.assertEqual(result['answer_kind'], 'korean_lexical_paraphrase')
        self.assertNotIn('dictionary_claims_answer', result)
        self.assertNotIn('dictionary_answer', result)
        self.assertNotIn('diagnostic', result)
        answer = result['korean_bridge_answer']
        self.assertEqual(answer['translation'], '진실; 현실')
        self.assertEqual(set(answer['source_conflict_entry_ids']), {'truth', 'reality'})
        self.assertFalse(answer['conflicts_resolved'])
        self.assertTrue(answer['machine_generated'])
        self.assertFalse(answer['gloss_alignment_verified'])
        self.assertFalse(result['sentence_verified'])
        self.assertIsNone(before['lexical_contract']['expected_translation'])
        self.assertEqual(rag.lookup('ClaiM', 'fix-to-ko'), before)
        self.assertEqual(entries, original)

    def test_korean_one_alternative_missing_source_or_explicit_uncertainty_needs_sentence_stage(self):
        ordinary = self.missing_korean_entries()
        uncertain = deepcopy(ordinary)
        uncertain[0]['senses']['en'] = ['truth?']
        cases = [
            (ordinary, korean(('truth', ['진실']), ('reality', ['진실']))),
            (ordinary, korean(('truth', ['진실', '현실']))),
            (uncertain, korean(('truth', ['진실?']), ('reality', ['현실']))),
        ]
        raw_sentence = sentence('진실일까?', ['truth', 'reality'])
        for entries, raw_bridge in cases:
            with self.subTest(raw_bridge=raw_bridge, entries=entries):
                original = deepcopy(entries)
                service, _, runner, _ = self.service(entries, [raw_bridge, raw_sentence])
                result = service.run('ClaiM', 'fix', 'ko', generate=True)
                self.assertEqual(runner.generate.call_count, 2)
                self.assertNotIn('korean_bridge_answer', result)
                self.assertNotIn('dictionary_claims_answer', result)
                self.assertEqual(result['diagnostic']['raw_output'], raw_sentence)
                self.assertTrue(result['source_evidence']['conflicting_spans'])
                self.assertFalse(result['sentence_verified'])
                self.assertEqual(entries, original)


if __name__ == '__main__':
    unittest.main()
