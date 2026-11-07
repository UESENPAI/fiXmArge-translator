#!/usr/bin/env python3
"""Compare cached base/LoRA sentence proposals; never assign translation accuracy."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from fixmarge.demo import DemoService
from fixmarge.infer import ModelRunner, REVIEWED_REVISIONS
from fixmarge.sentence_diagnostics import build_sentence_prompt, inspect_sentence_generation
from evaluate_wordnet_adapter import attach_local_adapter, offline_http_guard, validate_adapter

MODEL = 'Qwen/Qwen3-4B-Instruct-2507'
TEXT = "sINeEy Iz'u Nii riEl"
REFERENCE = 'sINeEy は帰らない'


def digest_file(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def prepare_cases():
    service = DemoService()
    cases = []
    for target in ('ja', 'en', 'ko'):
        result = service.run(TEXT, 'fix', target, generate=False)
        lookup = service._rag.lookup(TEXT, 'fix-to-' + target)
        prompt = build_sentence_prompt(result['source_evidence'], lookup)
        rendered = json.dumps(prompt, ensure_ascii=False, sort_keys=True)
        assert REFERENCE not in rendered, 'Fan sentence interpretation leaked into the prompt'
        cases.append({'id': 'fix-to-' + target, 'source_text': TEXT,
                      'target_language': target, 'source_evidence': result['source_evidence'],
                      'prompt': prompt, 'prompt_sha256': hashlib.sha256(rendered.encode()).hexdigest(),
                      'lookup': lookup})
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adapter', type=Path, default=ROOT / 'artifacts/qwen3-4b-wordnet-en-ja-lora-v1')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--max-new-tokens', type=int, default=384)
    args = parser.parse_args()
    if args.max_new_tokens < 1:
        parser.error('--max-new-tokens must be positive')
    for name in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY'):
        os.environ[name] = '1'
    cases = prepare_cases()
    workbook = ROOT / 'data/raw/japanese_wordbook.xlsx'
    report = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'mode': 'generate' if args.generate else 'plan',
        'model': MODEL, 'revision': REVIEWED_REVISIONS[MODEL],
        'adapter': str(args.adapter),
        'configuration': {'precision': 'NF4', 'do_sample': False, 'seed': 0,
                          'max_new_tokens': args.max_new_tokens, 'allow_download': False,
                          'dictionary_context': 'identical_between_base_and_lora',
                          'base_pass': 'before_adapter_attachment'},
        'provenance': {'source': 'secondary_fan_wordbook', 'file': 'data/raw/japanese_wordbook.xlsx',
                       'sha256': digest_file(workbook), 'sheet': '単語帳', 'cell': 'G273',
                       'entry_id': 'fx-84a7955ffac17756',
                       'linked_primary_url': 'https://www.youtube.com/watch?v=AIeAZ_qtdJ4',
                       'primary_snapshot_present': False, 'official_parallel_translation_present': False,
                       'fan_interpretation': REFERENCE, 'fan_interpretation_in_prompt': False,
                       'independent_sentences': 1, 'target_directions': 3},
        'assessment': {'translation_accuracy': None, 'translation_improvement': 'not_established',
                       'sentence_verified': False, 'grammar_rules_retrieved': 0,
                       'limitations': ['secondary_quote_only', 'fan_interpretation_is_not_gold',
                                       'sINeEy_sense_is_tentative', 'Iz_u_and_Nii_source_conflicts',
                                       'three_directions_are_one_sentence_not_three_independent_sentences',
                                       'changed_output_does_not_establish_improvement',
                                       'same_output_does_not_prove_adapter_is_inactive',
                                       'NF4_runtime_not_full_precision_comparison']},
        'cases': cases, 'results': {}, 'downloads': 0, 'training_performed': False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    save()
    if not args.generate:
        print(json.dumps({'cases': len(cases), 'independent_sentences': 1, 'output': str(args.output)}), flush=True)
        return
    validate_adapter(args.adapter)
    snapshot = Path(os.environ['HF_HOME']) / 'hub/models--Qwen--Qwen3-4B-Instruct-2507/snapshots' / REVIEWED_REVISIONS[MODEL]
    assert snapshot.is_dir()
    weights_before = {path.name: digest_file(path) for path in sorted(snapshot.glob('*.safetensors'))}
    assert weights_before
    adapter_before = digest_file(args.adapter / 'adapter_model.safetensors')
    with offline_http_guard() as attempts:
        import torch
        torch.manual_seed(0)
        print('Loading cached frozen NF4 base', flush=True)
        started = time.monotonic()
        runner = ModelRunner(model_name=MODEL, revision=REVIEWED_REVISIONS[MODEL], adapter=None,
                             device='cuda', load_in_4bit=True, allow_download=False,
                             max_new_tokens=args.max_new_tokens)
        runner._bundle[2].requires_grad_(False)
        runner._bundle[2].eval()
        report['model_load_seconds'] = round(time.monotonic() - started, 3)
        for mode in ('base', 'lora'):
            if mode == 'lora':
                attach_local_adapter(runner, args.adapter)
                assert not any(p.requires_grad for p in runner._bundle[2].parameters())
            report['results'][mode] = []
            for case in cases:
                torch.manual_seed(0)
                started = time.monotonic()
                raw = runner.generate(case['prompt'])
                diagnostic = inspect_sentence_generation(raw, case['source_evidence'], case['lookup'])
                record = {'id': case['id'], 'prompt_sha256': case['prompt_sha256'],
                          'raw_output': raw, 'diagnostic': diagnostic,
                          'seconds': round(time.monotonic() - started, 3)}
                report['results'][mode].append(record)
                save()
                print(json.dumps({'mode': mode, 'id': case['id'], 'schema_valid': diagnostic['schema_valid'],
                                  'tentative_translation': diagnostic['tentative_translation'],
                                  'seconds': record['seconds']}, ensure_ascii=False), flush=True)
        assert not attempts
        report['http_attempts'] = attempts
        report['gpu'] = torch.cuda.get_device_name(0)
        report['peak_allocated_mib'] = round(torch.cuda.max_memory_allocated() / 2**20, 1)
    weights_after = {path.name: digest_file(path) for path in sorted(snapshot.glob('*.safetensors'))}
    assert weights_before == weights_after
    assert adapter_before == digest_file(args.adapter / 'adapter_model.safetensors')
    report['integrity'] = {'base_weight_sha256_unchanged': True, 'adapter_weight_sha256_unchanged': True,
                           'base_weights': weights_after, 'adapter_sha256': adapter_before,
                           'adapter_merged': False}
    report['differences'] = []
    for base, lora in zip(report['results']['base'], report['results']['lora']):
        assert base['id'] == lora['id'] and base['prompt_sha256'] == lora['prompt_sha256']
        report['differences'].append({'id': base['id'], 'raw_output_identical': base['raw_output'] == lora['raw_output'],
                                      'translation_identical': base['diagnostic']['tentative_translation'] == lora['diagnostic']['tentative_translation']})
    save()
    print(json.dumps({'output': str(args.output), 'differences': report['differences'],
                      'accuracy': None, 'improvement': 'not_established'}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
