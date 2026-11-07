"""Model-free checks for the held-out WordNet adapter evaluator."""
from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
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
from scripts import evaluate_wordnet_adapter as evaluate


def row(group, direction='en-to-ja', targets=None):
    translation = '-to-' in direction
    source, target = direction.split('-to-') if translation else (direction.split('-')[0],) * 2
    task = 'wordnet_translation' if translation else 'wordnet_definition'
    source_id = 'oewn:2025' if direction == 'en-definition' else 'wnja:1.1'
    if targets is None:
        targets = ['対象一', '対象二'] if translation else ['an independently recorded fixture definition']
    reference = ' / '.join(targets) if translation else '\n'.join(targets)
    return {'messages': [{'role': 'system', 'content': 'Return the requested lexical answer only.'},
                         {'role': 'user', 'content': 'Fixture lexical query: source-word'},
                         {'role': 'assistant', 'content': reference}],
            'metadata': {'group_id': group, 'source': source_id, 'rights_status': 'open_license',
                         'status': 'fixture', 'license': evaluate.LICENSES[source_id],
                         'source_urls': ['https://example.org/source-record'],
                         'task': task, 'direction': direction,
                         'source_language': source, 'target_language': target,
                         ('alternatives' if translation else 'definitions'): targets}}


def corpus():
    return [row('translation-en', 'en-to-ja'), row('translation-ja', 'ja-to-en', ['truth', 'verity']),
            row('definition-en', 'en-definition'), row('definition-ja', 'ja-definition', ['事実に関する定義'])]


class WordNetAdapterEvaluationTests(unittest.TestCase):
    def test_selection_is_group_unique_per_stratum_and_removes_reference_answers(self):
        rows = corpus()
        rows.insert(1, row('translation-en', 'en-to-ja', ['duplicate-group-answer']))
        before = deepcopy(rows)
        plan = evaluate.make_plan(rows, per_task=1, train_rows=[row('different-training-group')])
        self.assertEqual(plan['selection']['lexical_cases'], 4)
        self.assertEqual(plan['selection']['authored_sentence_cases'], 4)
        self.assertEqual(plan['selection']['selected_unique_groups'], 4)
        self.assertEqual(len(plan['cases']), 8)
        self.assertTrue(plan['selection']['train_groups_checked'])
        for case in plan['cases'][:4]:
            self.assertEqual([message['role'] for message in case['prompt']], ['system', 'user'])
            self.assertNotIn(case['reference'], json.dumps(case['prompt'], ensure_ascii=False))
            self.assertEqual(case['metadata']['license'], evaluate.LICENSES[case['metadata']['source']])
            self.assertEqual(case['metadata']['source_urls'], ['https://example.org/source-record'])
        self.assertEqual(rows, before)

    def test_train_group_leakage_and_non_wordnet_data_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'group leakage'):
            evaluate.make_plan(corpus(), train_rows=[row('translation-en')])
        ineligible = row('game-derived')
        ineligible['metadata']['source'] = 'hecate-csv'
        ineligible['metadata']['rights_status'] = 'game_derived_not_eligible'
        with self.assertRaisesRegex(ValueError, 'WordNet source'):
            evaluate.make_plan([ineligible])
        no_license = row('unverified-license')
        no_license['metadata']['license'] = 'public access'
        with self.assertRaisesRegex(ValueError, 'license metadata'):
            evaluate.make_plan([no_license])

    def test_candidate_set_metrics_require_whole_candidates_and_penalize_extra_answers(self):
        exact = evaluate.candidate_set_metrics('ねこ / ネコ', ['ネコ', 'ねこ'])
        self.assertTrue(exact['exact_candidate_set'])
        self.assertEqual(exact['candidate_recall'], 1)
        partial = evaluate.candidate_set_metrics('ねこ / unexpected', ['ネコ', 'ねこ'])
        self.assertFalse(partial['exact_candidate_set'])
        self.assertEqual(partial['candidate_recall'], 0.5)
        self.assertEqual(partial['candidate_precision'], 0.5)
        self.assertEqual(partial['missing_candidates'], ['ネコ'])
        self.assertEqual(partial['unexpected_candidates'], ['unexpected'])
        self.assertEqual(evaluate.candidate_set_metrics('bobcat', ['cat'])['candidate_recall'], 0)
        self.assertTrue(evaluate.candidate_set_metrics('["truth", "verity"]', ['verity', 'truth'])['exact_candidate_set'])
        self.assertFalse(evaluate.candidate_set_metrics('null', ['truth'])['exact_candidate_set'])

    def test_definition_and_sentence_exact_diagnostics_are_separate(self):
        definition = evaluate.select_lexical([row('definition', 'en-definition')])[0]
        self.assertEqual(evaluate.score(definition, definition['reference']), {'exact_definition_reference': True})
        authored = evaluate.authored_cases()
        self.assertEqual(len(authored), 4)
        self.assertEqual([case['direction'] for case in authored], ['en-to-ja', 'en-to-ja', 'ja-to-en', 'ja-to-en'])
        self.assertTrue(evaluate.score(authored[0], authored[0]['targets'][1])['exact_authored_reference'])
        self.assertFalse(evaluate.score(authored[0], 'a different possible paraphrase')['exact_authored_reference'])
        self.assertEqual(authored[0]['metadata']['rights_status'], 'self_authored')

    def test_base_and_adapter_passes_reuse_one_nf4_runner_with_identical_prompts(self):
        plan = evaluate.make_plan(corpus())
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
            self.assertIs(same_runner._bundle[2], base)
            self.assertEqual(len(events), len(plan['cases']))
            same_runner.mode = 'adapted'
        loader = Mock(side_effect=attach)
        with tempfile.TemporaryDirectory() as temporary:
            adapter = self.adapter_directory(Path(temporary))
            result = evaluate.compare(plan, adapter=adapter, runner_factory=factory, adapter_loader=loader)
        factory.assert_called_once()
        options = factory.call_args.kwargs
        self.assertEqual(options['model_name'], evaluate.MODEL)
        self.assertEqual(options['revision'], evaluate.REVISION)
        self.assertIsNone(options['adapter'])
        self.assertFalse(options['allow_download'])
        self.assertTrue(options['load_in_4bit'])
        self.assertEqual(options['max_new_tokens'], 96)
        loader.assert_called_once()
        self.assertEqual([mode for mode, _ in events], ['base'] * 8 + ['adapted'] * 8)
        self.assertEqual([prompt for _, prompt in events[:8]], [prompt for _, prompt in events[8:]])
        self.assertEqual(result['base']['records'][0]['raw_output'], 'raw base')
        self.assertEqual(result['adapted']['records'][0]['raw_output'], 'raw adapted')
        self.assertFalse(result['base']['adapter_enabled'])
        self.assertTrue(result['adapted']['adapter_enabled'])
        base.requires_grad_.assert_called_once_with(False)
        base.eval.assert_called_once()

    @staticmethod
    def adapter_directory(path):
        (path / 'adapter_config.json').write_text(json.dumps({'peft_type': 'LORA', 'base_model_name_or_path': evaluate.MODEL,
                                                            'revision': evaluate.REVISION}))
        (path / 'adapter_model.safetensors').write_bytes(b'not-real-weights-test-only')
        return path

    def test_adapter_attachment_is_local_frozen_and_does_not_merge_or_reload_base(self):
        base, adapted = Mock(), Mock()
        loader = Mock(return_value=adapted)
        runner = SimpleNamespace(_bundle=('torch', 'tokenizer', base))
        module = SimpleNamespace(PeftModel=SimpleNamespace(from_pretrained=loader))
        with patch.dict(sys.modules, {'peft': module}):
            evaluate.attach_local_adapter(runner, Path('/fixture/adapter'))
        loader.assert_called_once_with(base, '/fixture/adapter', local_files_only=True, is_trainable=False)
        adapted.requires_grad_.assert_called_once_with(False)
        adapted.eval.assert_called_once()
        adapted.merge_and_unload.assert_not_called()
        self.assertEqual(runner._bundle, ('torch', 'tokenizer', adapted))

    def test_wrong_adapter_base_fails_before_model_loading(self):
        with tempfile.TemporaryDirectory() as temporary:
            adapter = self.adapter_directory(Path(temporary))
            configuration = json.loads((adapter / 'adapter_config.json').read_text())
            configuration['base_model_name_or_path'] = 'another/model'
            (adapter / 'adapter_config.json').write_text(json.dumps(configuration))
            factory = Mock()
            with self.assertRaisesRegex(ValueError, 'base model'):
                evaluate.compare(evaluate.make_plan(corpus()), adapter=adapter, runner_factory=factory)
            factory.assert_not_called()

    def test_dry_run_never_loads_models_or_peft_and_does_not_overwrite_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            dataset, train, output = folder / 'test.jsonl', folder / 'train.jsonl', folder / 'report.json'
            dataset.write_text(''.join(json.dumps(value, ensure_ascii=False) + '\n' for value in corpus()))
            train.write_text(json.dumps(row('training-only')) + '\n')
            with patch.object(evaluate, 'compare') as compare, patch.object(evaluate, 'ModelRunner') as model:
                with redirect_stdout(io.StringIO()):
                    code = evaluate.main(['--dataset', str(dataset), '--train', str(train), '--output', str(output)])
            self.assertEqual(code, 0)
            compare.assert_not_called()
            model.assert_not_called()
            report = json.loads(output.read_text())
            self.assertEqual(report['execution'], 'dry-run')
            self.assertEqual(report['selection']['lexical_cases'], 4)
            self.assertEqual(report['modes'], {})
            self.assertEqual(report['downloads'], 0)
            before = output.read_bytes()
            with redirect_stderr(io.StringIO()):
                self.assertEqual(evaluate.main(['--dataset', str(dataset), '--output', str(output)]), 2)
            self.assertEqual(output.read_bytes(), before)

    def test_sampling_limits_and_missing_training_audit_are_explicit(self):
        for count in (0, 17, True):
            with self.subTest(count=count), self.assertRaisesRegex(ValueError, 'per_task'):
                evaluate.make_plan(corpus(), per_task=count)
        plan = evaluate.make_plan(corpus())
        self.assertFalse(plan['selection']['train_groups_checked'])
        self.assertIsNone(plan['selection']['group_leakage_found'])


if __name__ == '__main__':
    unittest.main()
