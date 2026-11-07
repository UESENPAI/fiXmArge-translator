"""Model-free checks for separated seen/held-out fiXmArge lexical probes."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from scripts import evaluate_fixmarge_adapter as evaluate
from fixmarge.lexical_facts import entry_id, make_fact_record


def fact_row(family, direction, forms=None, glosses=None):
    language = 'ja' if 'ja' in direction else 'en'
    forms = forms or ['kOht-' + family]
    glosses = glosses or (['記録-' + family + '-一', '記録-' + family + '-二'] if language == 'ja'
                         else ['gloss-' + family + '-one', 'gloss-' + family + '-two'])
    if direction.endswith('-to-fix'):
        glosses = glosses[:1]
    return make_fact_record({'language': language, 'forms': forms, 'glosses': glosses}, direction,
                            group_id='fixfact-' + entry_id('family-' + family))


def corpus(prefix, families=3):
    return [fact_row(prefix + str(number), direction)
            for number in range(families) for direction in evaluate.DIRECTIONS]


def wordnet_row(group):
    return {'messages': [{'role': 'user', 'content': 'Recorded dictionary query'},
                         {'role': 'assistant', 'content': '記録'}],
            'metadata': {'group_id': group, 'source': 'wnja:1.1', 'status': 'fixture',
                         'task': 'wordnet_translation', 'direction': 'en-to-ja',
                         'source_language': 'en', 'target_language': 'ja',
                         'rights_status': 'open_license', 'license': 'Japanese-WordNet + WordNet',
                         'alternatives': ['記録']}}


class FixmargeAdapterEvaluationTests(unittest.TestCase):
    def test_all_directions_separate_seen_and_heldout_with_output_independent_selection(self):
        train, test = corpus('train'), corpus('test')
        before = deepcopy((train, test))
        plan = evaluate.make_plan(train, test)
        self.assertEqual(plan['selection']['train_seen_cases'], 4)
        self.assertEqual(plan['selection']['heldout_test_cases'], 8)
        self.assertEqual(plan['selection']['general_control_cases'], 4)
        self.assertEqual(len(plan['cases']), 16)
        self.assertFalse(plan['selection']['model_outputs_used_for_selection'])
        self.assertEqual(plan['selection']['train_test_group_overlap'], 0)
        self.assertEqual(plan['selection']['selected_heldout_unique_groups'], len({
            case['metadata']['group_id'] for case in plan['cases'] if case['partition'] == 'heldout_test'}))
        train_groups = {row['metadata']['group_id'] for row in train}
        counts = {}
        for case in plan['cases']:
            counts[case['partition']] = counts.get(case['partition'], 0) + 1
            self.assertNotIn('assistant', [message['role'] for message in case['prompt']])
            if case['partition'] == 'heldout_test':
                self.assertNotIn(case['metadata']['group_id'], train_groups)
            if case['kind'] == evaluate.FACT_TASK:
                rendered = json.dumps(case['prompt'], ensure_ascii=False)
                for target in case['targets']:
                    self.assertNotIn(target, rendered)
                self.assertEqual(case['metadata']['source_rights_status'], 'game_derived_not_eligible')
        self.assertEqual(counts, {'train_seen': 4, 'heldout_test': 8, 'general_control': 4})
        self.assertEqual((train, test), before)
        shuffled = evaluate.make_plan(list(reversed(train)), list(reversed(test)))
        self.assertEqual(plan, shuffled)

    def test_reverse_alternatives_and_canonical_case_spaces_are_retained(self):
        rows = corpus('test')
        replacement = fact_row('test0', 'en-to-fix', forms=['LiGh rai', 'kOht'], glosses=['light'])
        rows = [replacement if row['metadata']['group_id'] == replacement['metadata']['group_id']
                and row['metadata']['direction'] == 'en-to-fix' else row for row in rows]
        selected = evaluate.select_probes(rows, 'heldout_test', 3)
        case = next(case for case in selected if case['reference'] == 'LiGh rai / kOht')
        self.assertEqual(case['targets'], ['LiGh rai', 'kOht'])
        self.assertNotIn('LiGh rai', json.dumps(case['prompt']))
        self.assertTrue(evaluate.measure(case, 'kOht / LiGh rai')['source_dictionary_candidate_set_equal'])
        self.assertFalse(evaluate.measure(case, 'kOht / light rai')['source_dictionary_candidate_set_equal'])
        self.assertFalse(evaluate.measure(case, 'kOht / LiGhrai')['source_dictionary_candidate_set_equal'])

    def test_training_group_and_duplicate_prompt_leaks_are_rejected(self):
        train, test = corpus('train'), corpus('test')
        leaking = deepcopy(test)
        leaking[0]['metadata']['group_id'] = train[0]['metadata']['group_id']
        with self.assertRaisesRegex(ValueError, 'group leakage'):
            evaluate.make_plan(train, leaking)
        duplicate = deepcopy(train[0])
        duplicate['metadata']['group_id'] = 'fixfact-' + entry_id('different-family')
        with self.assertRaisesRegex(ValueError, 'Identical fiXmArge prompts'):
            evaluate.make_plan(train, test + [duplicate])

    def test_conflicting_references_for_one_prompt_cannot_depend_on_input_order(self):
        train = corpus('train')
        conflict = fact_row('train0', 'fix-to-ja', glosses=['別の語義'])
        with self.assertRaisesRegex(ValueError, 'Conflicting source references'):
            evaluate.make_plan(train + [conflict], corpus('test'))

    def test_mixed_wordnet_rows_are_validated_but_not_mislabelled_as_fix_probes(self):
        plan = evaluate.make_plan(corpus('train') + [wordnet_row('wn-train')],
                                  corpus('test') + [wordnet_row('wn-test')])
        self.assertEqual(plan['selection']['train_seen_cases'], 4)
        self.assertTrue(all(case['metadata']['task'] == evaluate.FACT_TASK
                            for case in plan['cases'] if case['partition'] != 'general_control'))
        invalid = wordnet_row('wrong-source')
        invalid['metadata']['source'] = 'unverified_fan_text'
        with self.assertRaisesRegex(ValueError, 'WordNet source'):
            evaluate.make_plan(corpus('train') + [invalid], corpus('test'))

    def test_bounded_fact_tampering_and_incomplete_directions_are_rejected(self):
        rows = corpus('test')
        rows[0]['messages'][-1]['content'] = 'An arbitrary substituted sentence.'
        with self.assertRaisesRegex(ValueError, 'exactly reconstruct'):
            evaluate.make_plan(corpus('train'), rows)
        with self.assertRaisesRegex(ValueError, 'all four directions'):
            evaluate.make_plan(corpus('train'), [fact_row('test', 'fix-to-ja')])
        for value in (True, 0, 17):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'per_direction'):
                evaluate.select_probes(corpus('test'), 'heldout_test', value)

    def test_agreement_uses_complete_source_candidates_not_substrings_or_accuracy(self):
        exact = evaluate.source_candidate_agreement('first; second', ['second', 'first'])
        self.assertTrue(exact['source_dictionary_candidate_set_equal'])
        partial = evaluate.source_candidate_agreement('first / unexpected', ['first', 'second'])
        self.assertEqual(partial['source_dictionary_candidate_coverage'], 0.5)
        self.assertEqual(partial['returned_candidate_source_support'], 0.5)
        self.assertEqual(partial['missing_candidates'], ['second'])
        self.assertEqual(partial['unexpected_candidates'], ['unexpected'])
        self.assertEqual(evaluate.source_candidate_agreement('bobcat', ['cat'])['source_dictionary_candidate_coverage'], 0)
        self.assertTrue(evaluate.source_candidate_agreement('["LiGh rai", "kOht"]', ['kOht', 'LiGh rai'])['source_dictionary_candidate_set_equal'])
        self.assertFalse(evaluate.source_candidate_agreement('null', ['truth'])['source_dictionary_candidate_set_equal'])
        self.assertFalse(any('accuracy' in key for key in exact))
        self.assertEqual(evaluate.answer_candidates('male/female'), ['male/female'])

    def test_authored_controls_are_distinct_from_dictionary_agreement(self):
        case = evaluate.authored_cases()[0]
        case['partition'] = 'general_control'
        self.assertEqual(evaluate.measure(case, case['targets'][1]), {'authored_reference_string_equal': True})
        self.assertEqual(evaluate.measure(case, 'another potentially valid wording'), {'authored_reference_string_equal': False})
        plan = evaluate.make_plan(corpus('train'), corpus('test'), include_general_controls=False)
        self.assertEqual(plan['selection']['general_control_cases'], 0)
        self.assertEqual(len(plan['cases']), 12)

    @staticmethod
    def adapter_directory(path):
        path.mkdir(exist_ok=True)
        (path / 'adapter_config.json').write_text(json.dumps({'peft_type': 'LORA',
             'base_model_name_or_path': evaluate.MODEL, 'revision': evaluate.REVISION}))
        (path / 'adapter_model.safetensors').write_bytes(b'fake-safetensors-fixture')
        return path

    def test_same_frozen_nf4_base_is_measured_before_local_adapter_attachment(self):
        plan = evaluate.make_plan(corpus('train'), corpus('test'), include_general_controls=False)
        events = []
        base = Mock()
        runner = SimpleNamespace(_bundle=('torch-fixture', 'tokenizer-fixture', base), mode='base')
        def generate(prompt):
            events.append((runner.mode, deepcopy(prompt)))
            return 'raw ' + runner.mode
        runner.generate = generate
        factory = Mock(return_value=runner)
        def attach(same_runner, path):
            self.assertIs(same_runner, runner)
            self.assertEqual(len(events), len(plan['cases']))
            same_runner.mode = 'adapted'
        loader = Mock(side_effect=attach)
        with tempfile.TemporaryDirectory() as temporary:
            result = evaluate.compare(plan, adapter=self.adapter_directory(Path(temporary)),
                                      runner_factory=factory, adapter_loader=loader)
        factory.assert_called_once_with(model_name=evaluate.MODEL, revision=evaluate.REVISION, adapter=None,
                                       device='cuda', load_in_4bit=True, allow_download=False, max_new_tokens=96)
        loader.assert_called_once()
        length = len(plan['cases'])
        self.assertEqual([mode for mode, _ in events], ['base'] * length + ['adapted'] * length)
        self.assertEqual([prompt for _, prompt in events[:length]], [prompt for _, prompt in events[length:]])
        self.assertFalse(result['base']['adapter_enabled'])
        self.assertTrue(result['adapted']['adapter_enabled'])
        self.assertIn('train_seen:fix-to-ja', result['base']['metrics_by_partition_direction'])
        self.assertIn('heldout_test:fix-to-ja', result['base']['metrics_by_partition_direction'])
        base.requires_grad_.assert_called_once_with(False)
        base.eval.assert_called_once()

    def test_wrong_adapter_is_rejected_before_loading_any_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            adapter = self.adapter_directory(Path(temporary))
            (adapter / 'adapter_config.json').write_text(json.dumps({'peft_type': 'LORA', 'base_model_name_or_path': 'wrong/model'}))
            factory = Mock()
            with self.assertRaisesRegex(ValueError, 'base model'):
                evaluate.compare(evaluate.make_plan(corpus('train'), corpus('test')), adapter=adapter,
                                 runner_factory=factory)
            factory.assert_not_called()

    def test_dry_run_does_not_load_models_or_overwrite_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            train, test, output = root / 'train.jsonl', root / 'test.jsonl', root / 'plan.json'
            for path, rows in ((train, corpus('train')), (test, corpus('test'))):
                path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            with patch.object(evaluate, 'compare') as compare, patch.object(evaluate, 'ModelRunner') as runner:
                with redirect_stdout(io.StringIO()):
                    code = evaluate.main(['--train', str(train), '--test', str(test), '--output', str(output)])
            self.assertEqual(code, 0)
            compare.assert_not_called()
            runner.assert_not_called()
            report = json.loads(output.read_text())
            self.assertEqual(report['execution'], 'dry-run')
            self.assertEqual(report['assessment_scope'], 'source_dictionary_candidate_agreement_not_translation_accuracy')
            self.assertIsNone(report['sentence_translation_accuracy'])
            self.assertEqual(report['downloads'], 0)
            original = output.read_bytes()
            with redirect_stderr(io.StringIO()):
                code = evaluate.main(['--train', str(train), '--test', str(test), '--output', str(output)])
            self.assertEqual(code, 2)
            self.assertEqual(output.read_bytes(), original)
            with redirect_stderr(io.StringIO()), patch.object(evaluate, 'compare') as compare:
                code = evaluate.main(['--train', str(train), '--test', str(test), '--output', str(root / 'missing-adapter.json'), '--generate'])
            self.assertEqual(code, 2)
            compare.assert_not_called()
            self.assertFalse((root / 'missing-adapter.json').exists())


if __name__ == '__main__':
    unittest.main()
