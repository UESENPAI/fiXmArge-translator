#!/usr/bin/env python3
"""Offline NF4 base/LoRA lexical and general-language regression smoke checks.

The default is a model-free plan. Exact candidate coverage and authored-sentence
string matches are diagnostics, not general translation accuracy.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fixmarge.infer import ModelRunner, REVIEWED_REVISIONS

MODEL = 'Qwen/Qwen3-4B-Instruct-2507'
REVISION = REVIEWED_REVISIONS[MODEL]
STRATA = {
    ('wordnet_translation', 'en-to-ja'), ('wordnet_translation', 'ja-to-en'),
    ('wordnet_definition', 'en-definition'), ('wordnet_definition', 'ja-definition'),
}
LICENSES = {'wnja:1.1': 'Japanese-WordNet + WordNet', 'oewn:2025': 'CC-BY-4.0 + WordNet'}
LIMITATIONS = [
    'This is a tiny regression smoke check, not an independently reviewed sentence-translation benchmark.',
    'Candidate-set equality and coverage measure the supplied WordNet lexical targets only; definition exact match is a separate formatting-sensitive diagnostic.',
    'Authored-sentence exact references are not exhaustive acceptable translations. A mismatch is not proof of an incorrect translation.',
    'No RAG, dictionary grounding, reference injection, optimizer, backward pass, adapter merge, or training occurs in this evaluator.',
    'The base outputs are generated before adapter attachment. Both passes share the same loaded NF4 base and identical prompts and generation limits.',
    'Only a small number of held-out groups is sampled. Train/test lemma or synonym overlap may remain even when group IDs are disjoint.',
    'No fiXmArge ability or improvement is assessed. Base-model file-hash verification belongs to the separate training-run audit.',
]
AUTHORED_SENTENCES = [
    ('en', 'ja', 'The cat is sleeping.', ['猫は寝ています。', '猫が寝ています。', '猫は眠っています。', '猫が眠っています。']),
    ('en', 'ja', 'I have two books.', ['私は本を2冊持っています。', '私は本を二冊持っています。', '本を2冊持っています。', '本を二冊持っています。']),
    ('ja', 'en', 'これは本です。', ['This is a book.']),
    ('ja', 'en', '猫が寝ています。', ['The cat is sleeping.', 'A cat is sleeping.', 'The cat is asleep.', 'A cat is asleep.']),
]


def normalized(text: str) -> str:
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()


def read_rows(path: Path) -> list[dict]:
    records = []
    with Path(path).open(encoding='utf-8-sig') as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                validate_row(row)
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f'{path}:{number}: {exc}') from exc
            records.append(row)
    if not records:
        raise ValueError('WordNet evaluation corpus is empty: ' + str(path))
    return records


def validate_row(row: dict) -> None:
    if not isinstance(row, dict) or not isinstance(row.get('metadata'), dict):
        raise ValueError('Each row needs metadata')
    metadata = row['metadata']
    if (metadata.get('task'), metadata.get('direction')) not in STRATA:
        raise ValueError('Only the four reviewed English/Japanese WordNet strata are evaluated')
    if metadata.get('source') not in LICENSES or metadata.get('rights_status') != 'open_license':
        raise ValueError('Expected verified WordNet source and recorded open-license basis')
    licence = metadata.get('license')
    expected = LICENSES[metadata['source']]
    if licence != expected and not (isinstance(licence, list) and expected in licence):
        raise ValueError('WordNet license metadata does not match its source')
    if not isinstance(metadata.get('group_id'), str) or not metadata['group_id']:
        raise ValueError('metadata.group_id is required')
    if any(metadata.get(key) not in ('en', 'ja') for key in ('source_language', 'target_language')):
        raise ValueError('Evaluation is restricted to English/Japanese records')
    messages = row.get('messages')
    if not isinstance(messages, list) or [message.get('role') if isinstance(message, dict) else None for message in messages] not in (
        ['user', 'assistant'], ['system', 'user', 'assistant']):
        raise ValueError('Expected one user turn and a final assistant reference')
    if any(not isinstance(message.get('content'), str) or not message['content'].strip() for message in messages):
        raise ValueError('Messages must have nonempty text')
    field = 'alternatives' if metadata['task'] == 'wordnet_translation' else 'definitions'
    targets = metadata.get(field)
    if not isinstance(targets, list) or not targets or any(not isinstance(value, str) or not value.strip() for value in targets):
        raise ValueError('metadata.' + field + ' must contain nonempty target strings')


def select_lexical(rows: list[dict], per_task: int = 1) -> list[dict]:
    if isinstance(per_task, bool) or not isinstance(per_task, int) or not 1 <= per_task <= 16:
        raise ValueError('per_task must be an integer between 1 and 16')
    groups = defaultdict(set)
    selected = []
    for row in rows:
        validate_row(row)
        metadata = row['metadata']
        stratum = metadata['task'], metadata['direction']
        if len(groups[stratum]) >= per_task or metadata['group_id'] in groups[stratum]:
            continue
        groups[stratum].add(metadata['group_id'])
        selected.append({
            'id': 'lexical-' + str(len(selected) + 1), 'kind': metadata['task'],
            'direction': metadata['direction'], 'metadata': metadata.copy(),
            'prompt': [{'role': message['role'], 'content': message['content']} for message in row['messages'][:-1]],
            'reference': row['messages'][-1]['content'],
            'targets': list(metadata['alternatives'] if metadata['task'] == 'wordnet_translation' else metadata['definitions']),
        })
    if not selected:
        raise ValueError('No eligible lexical cases were selected')
    return selected


def authored_cases() -> list[dict]:
    names = {'en': 'English', 'ja': 'Japanese'}
    return [
        {'id': 'authored-' + str(number), 'kind': 'self_authored_sentence',
         'direction': source + '-to-' + target,
         'prompt': [{'role': 'system', 'content': f'Translate the following {names[source]} sentence into {names[target]}. Return only the translation.'},
                    {'role': 'user', 'content': text}],
         'reference': accepted[0], 'targets': accepted[:],
         'metadata': {'source': 'self_authored_regression_v1', 'rights_status': 'self_authored',
                      'source_language': source, 'target_language': target,
                      'note': 'Newly authored smoke input and non-exhaustive literal reference set; not a reviewed benchmark.'}}
        for number, (source, target, text, accepted) in enumerate(AUTHORED_SENTENCES, 1)
    ]


def make_plan(rows: list[dict], *, per_task: int = 1, train_rows: list[dict] | None = None) -> dict:
    groups = {row['metadata']['group_id'] for row in rows}
    if train_rows is not None:
        for row in train_rows:
            validate_row(row)
        overlap = groups & {row['metadata']['group_id'] for row in train_rows}
        if overlap:
            raise ValueError('Train/evaluation group leakage: ' + ', '.join(sorted(overlap)[:8]))
    lexical = select_lexical(rows, per_task)
    return {'cases': lexical + authored_cases(),
            'selection': {'per_task_direction': per_task, 'lexical_cases': len(lexical), 'authored_sentence_cases': 4,
                          'lexical_strata': dict(Counter(case['kind'] + ':' + case['direction'] for case in lexical)),
                          'selected_unique_groups': len({case['metadata']['group_id'] for case in lexical}),
                          'dataset_unique_groups': len(groups), 'train_groups_checked': train_rows is not None,
                          'group_leakage_found': False if train_rows is not None else None}}


def answer_value(raw: str):
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw if isinstance(raw, str) else ''
    if isinstance(value, dict):
        for field in ('translation', 'answer', 'alternatives', 'definitions'):
            if field in value:
                return value[field]
        return ''
    return value


def candidate_set_metrics(raw: str, expected: list[str]) -> dict:
    answer = answer_value(raw)
    values = answer if isinstance(answer, list) and all(isinstance(value, str) for value in answer) else answer.split(' / ') if isinstance(answer, str) else []
    returned = {normalized(value) for value in values if normalized(value)}
    target = {normalized(value) for value in expected}
    matched = target & returned
    return {'exact_candidate_set': returned == target,
            'candidate_recall': len(matched) / len(target),
            'candidate_precision': len(matched) / len(returned) if returned else 0.0,
            'expected_candidates': sorted(target), 'returned_candidates': sorted(returned),
            'missing_candidates': sorted(target - returned), 'unexpected_candidates': sorted(returned - target)}


def score(case: dict, raw: str) -> dict:
    if case['kind'] == 'wordnet_translation':
        return candidate_set_metrics(raw, case['targets'])
    answer = answer_value(raw)
    answer = answer if isinstance(answer, str) else '\n'.join(answer) if isinstance(answer, list) and all(isinstance(value, str) for value in answer) else ''
    if case['kind'] == 'wordnet_definition':
        return {'exact_definition_reference': normalized(answer) == normalized(case['reference'])}
    return {'exact_authored_reference': any(normalized(answer) == normalized(target) for target in case['targets'])}


def evaluate_cases(cases: list[dict], runner) -> dict:
    records = []
    by_stratum = defaultdict(list)
    for case in cases:
        started = time.monotonic()
        raw = runner.generate(case['prompt'])
        metrics = score(case, raw)
        record = {**case, 'raw_output': raw, 'metrics': metrics, 'seconds': round(time.monotonic() - started, 3)}
        records.append(record)
        by_stratum[case['kind'] + ':' + case['direction']].append(metrics)
    aggregates = {}
    for stratum, values in by_stratum.items():
        aggregates[stratum] = {'cases': len(values)}
        for field in ('exact_candidate_set', 'candidate_recall', 'candidate_precision', 'exact_definition_reference', 'exact_authored_reference'):
            available = [value[field] for value in values if field in value]
            if available:
                aggregates[stratum][field + '_mean'] = sum(available) / len(available)
    return {'records': records, 'metrics_by_task_direction': aggregates}


def attach_local_adapter(runner, adapter: Path):
    from peft import PeftModel
    torch, tokenizer, base = runner._bundle
    adapted = PeftModel.from_pretrained(base, str(adapter), local_files_only=True, is_trainable=False)
    adapted.requires_grad_(False)
    adapted.eval()
    runner._bundle = (torch, tokenizer, adapted)


def validate_adapter(path: Path) -> dict:
    if not path.is_dir() or not (path / 'adapter_model.safetensors').is_file():
        raise ValueError('Expected a local safetensors LoRA adapter directory')
    config = json.loads((path / 'adapter_config.json').read_text(encoding='utf-8'))
    if config.get('peft_type') != 'LORA':
        raise ValueError('Only a local LoRA adapter is supported')
    if config.get('base_model_name_or_path') not in (None, MODEL):
        raise ValueError('Adapter base model does not match the pinned Qwen model')
    if config.get('revision') not in (None, REVISION):
        raise ValueError('Adapter revision does not match the pinned Qwen revision')
    return config


def compare(plan: dict, *, adapter: Path | None = None, device: str = 'cuda', max_new_tokens: int = 96,
            runner_factory=ModelRunner, adapter_loader=attach_local_adapter) -> dict:
    if device not in ('auto', 'cuda') or isinstance(max_new_tokens, bool) or not isinstance(max_new_tokens, int) or max_new_tokens < 1:
        raise ValueError('NF4 evaluation requires auto/cuda and a positive output limit')
    if adapter is not None:
        validate_adapter(adapter)
    runner = runner_factory(model_name=MODEL, revision=REVISION, adapter=None,
                            device=device, load_in_4bit=True, allow_download=False,
                            max_new_tokens=max_new_tokens)
    runner._bundle[2].requires_grad_(False)
    runner._bundle[2].eval()
    results = {'base': {'adapter_enabled': False, **evaluate_cases(plan['cases'], runner)}}
    if adapter is not None:
        adapter_loader(runner, adapter)
        results['adapted'] = {'adapter_enabled': True, **evaluate_cases(plan['cases'], runner)}
    return results


@contextmanager
def offline_http_guard():
    import requests
    from unittest.mock import patch
    attempts = []
    def reject(_session, method, url, *args, **kwargs):
        attempts.append({'method': method, 'url': url})
        raise RuntimeError('HTTP is blocked in the cached-model adapter evaluator')
    with patch.object(requests.sessions.Session, 'request', reject):
        yield attempts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--train', type=Path, help='Optional training split for group-leakage detection; omission is recorded')
    parser.add_argument('--adapter', type=Path, help='Local adapter directory; omitted for base-only evaluation')
    parser.add_argument('--per-task', type=int, default=1, help='Unique groups per task and direction, 1..16')
    parser.add_argument('--max-new-tokens', type=int, default=96)
    parser.add_argument('--device', choices=('cuda', 'auto'), default='cuda')
    parser.add_argument('--generate', action='store_true', help='Explicitly load the cached NF4 model and generate')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        rows = read_rows(args.dataset)
        train_rows = read_rows(args.train) if args.train else None
        plan = make_plan(rows, per_task=args.per_task, train_rows=train_rows)
        if args.max_new_tokens < 1:
            raise ValueError('max-new-tokens must be positive')
        output = args.output or ROOT / 'runs' / ('wordnet-adapter-eval-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
        if output.exists():
            raise ValueError('Output already exists; choose a new path: ' + str(output))
        report = {'execution': 'generate' if args.generate else 'dry-run', 'model': MODEL, 'revision': REVISION,
                  'load_in_4bit': True, 'quantization': 'NF4 with the same loaded base for both passes',
                  'generation': {'max_new_tokens': args.max_new_tokens, 'device': args.device},
                  'adapter': str(args.adapter) if args.adapter else None,
                  'selection': plan['selection'], 'cases': plan['cases'],
                  'dataset': {'path': str(args.dataset), 'sha256': hashlib.sha256(args.dataset.read_bytes()).hexdigest()},
                  'train': {'path': str(args.train), 'sha256': hashlib.sha256(args.train.read_bytes()).hexdigest()} if args.train else None,
                  'evaluation_performed_training': False, 'merge_performed': False,
                  'base_measured_before_adapter_attachment': True if args.generate else None,
                  'base_file_hash_verification': 'not performed here; separate training-run audit required',
                  'downloads': 0, 'http_attempts': [], 'limitations': LIMITATIONS[:], 'modes': {}}
        if args.generate:
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
            with offline_http_guard() as attempts:
                report['modes'] = compare(plan, adapter=args.adapter, device=args.device, max_new_tokens=args.max_new_tokens)
            report['http_attempts'] = attempts
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'output': str(output), 'execution': report['execution'], 'selection': report['selection'],
                          'metrics': {mode: value['metrics_by_task_direction'] for mode, value in report['modes'].items()}}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
