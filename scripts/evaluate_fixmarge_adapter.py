#!/usr/bin/env python3
"""Plan or run cache-only fiXmArge lexical source-agreement checks.

Seen training probes and held-out dictionary probes remain separate. Neither is
an independently validated fiXmArge sentence-translation accuracy benchmark.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from fixmarge.infer import ModelRunner
from fixmarge.lexical_facts import validate_local_fact_record
from evaluate_wordnet_adapter import (
    MODEL, REVISION, attach_local_adapter, authored_cases, normalized,
    offline_http_guard, validate_adapter, validate_row as validate_wordnet_row,
)
from train_qlora import validate_record

DIRECTIONS = ('fix-to-ja', 'ja-to-fix', 'fix-to-en', 'en-to-fix')
FACT_TASK = 'fix_lexical_correspondence'
LIMITATIONS = [
    'Candidate agreement measures the supplied unreviewed source dictionary, not independently validated translation accuracy.',
    'Training probes were seen during fitting and are not evidence of held-out generalization.',
    'Held-out probes exclude training groups, but shared language knowledge and related lexical senses can remain.',
    'The test cases are selected by a fixed content hash before inspecting any model output.',
    'All recorded source alternatives and canonical spelling are retained. A different valid paraphrase can fail the exact source agreement check.',
    'Authored English/Japanese sentence references are non-exhaustive regression examples, not fiXmArge sentence references.',
    'The base is measured before adapter attachment; both passes use identical prompts, NF4 precision and greedy generation settings.',
    'No dictionary answers, reference translations, RAG, optimizer, backward pass, merge or training are injected during generation.',
    'Local lexical experiment metadata does not establish source permission or public-release clearance.',
    'Original model and existing adapter file integrity are checked by the separate training-run audit.',
]


def read_rows(path: Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding='utf-8-sig') as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                validate_evaluation_row(row)
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f'{path}:{number}: {exc}') from exc
            rows.append(row)
    if not rows:
        raise ValueError('Empty evaluation split: ' + str(path))
    return rows


def validate_evaluation_row(row: dict) -> None:
    validate_record(row)
    metadata = row['metadata']
    if metadata['task'] == FACT_TASK:
        validate_local_fact_record(row)
        if metadata.get('direction') not in DIRECTIONS:
            raise ValueError('Only four fiXmArge/English/Japanese lexical directions are supported')
    else:
        # Mixed train/test files may contain the licensed replay rows. They are
        # checked, then excluded from the fiXmArge probe selection.
        validate_wordnet_row(row)


def select_probes(rows: list[dict], partition: str, per_direction: int) -> list[dict]:
    if partition not in ('train_seen', 'heldout_test'):
        raise ValueError('Unknown probe partition')
    if isinstance(per_direction, bool) or not isinstance(per_direction, int) or not 1 <= per_direction <= 16:
        raise ValueError('per_direction must be an integer between 1 and 16')
    ranked, prompt_references = [], {}
    for row in rows:
        validate_evaluation_row(row)
        if row['metadata']['task'] != FACT_TASK:
            continue
        prompt_key = json.dumps(row['messages'][:-1], ensure_ascii=False, sort_keys=True)
        reference = row['messages'][-1]['content']
        if prompt_key in prompt_references and prompt_references[prompt_key] != reference:
            raise ValueError('Conflicting source references for an identical lexical prompt')
        prompt_references[prompt_key] = reference
        key = json.dumps({'selection_version': 'fix-lexical-probes-v1', 'partition': partition,
                          'group_id': row['metadata']['group_id'],
                          'direction': row['metadata']['direction'],
                          'prompt': row['messages'][:-1]}, ensure_ascii=False, sort_keys=True)
        ranked.append((hashlib.sha256(key.encode()).hexdigest(), row))
    ranked.sort(key=lambda item: item[0])
    used = defaultdict(set)
    cases = []
    for rank, row in ranked:
        metadata = row['metadata']
        direction, group = metadata['direction'], metadata['group_id']
        if group in used[direction] or len(used[direction]) >= per_direction:
            continue
        used[direction].add(group)
        fact = metadata['fact']
        targets = fact['glosses'] if direction.startswith('fix-to-') else fact['forms']
        prompt = deepcopy(row['messages'][:-1])
        cases.append({'id': partition + '-' + direction + '-' + str(len(used[direction])),
                      'kind': FACT_TASK, 'partition': partition, 'direction': direction,
                      'metadata': deepcopy(metadata), 'prompt': prompt,
                      'prompt_sha256': hashlib.sha256(json.dumps(prompt, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
                      'reference': row['messages'][-1]['content'], 'targets': list(targets),
                      'selection_sha256': rank})
    missing = {direction: len(used[direction]) for direction in DIRECTIONS if len(used[direction]) != per_direction}
    if missing:
        raise ValueError('Insufficient distinct groups for all four directions: ' + json.dumps(missing))
    return sorted(cases, key=lambda case: (DIRECTIONS.index(case['direction']), case['selection_sha256']))


def make_plan(train_rows: list[dict], test_rows: list[dict], *, train_per_direction: int = 1,
              test_per_direction: int = 2, include_general_controls: bool = True) -> dict:
    for row in train_rows + test_rows:
        validate_evaluation_row(row)
    train_groups = {row['metadata']['group_id'] for row in train_rows}
    test_groups = {row['metadata']['group_id'] for row in test_rows}
    overlap = train_groups & test_groups
    if overlap:
        raise ValueError('Train/test group leakage: ' + ', '.join(sorted(overlap)[:8]))
    train_prompts = {json.dumps(row['messages'][:-1], ensure_ascii=False, sort_keys=True)
                     for row in train_rows if row['metadata']['task'] == FACT_TASK}
    test_prompts = {json.dumps(row['messages'][:-1], ensure_ascii=False, sort_keys=True)
                    for row in test_rows if row['metadata']['task'] == FACT_TASK}
    if train_prompts & test_prompts:
        raise ValueError('Identical fiXmArge prompts occur in train and test splits')
    seen = select_probes(train_rows, 'train_seen', train_per_direction)
    held_out = select_probes(test_rows, 'heldout_test', test_per_direction)
    controls = authored_cases() if include_general_controls else []
    for case in controls:
        case['partition'] = 'general_control'
        case['prompt_sha256'] = hashlib.sha256(json.dumps(case['prompt'], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return {'cases': seen + held_out + controls,
            'selection': {'selection_version': 'fix-lexical-probes-v1',
                          'train_seen_cases': len(seen), 'heldout_test_cases': len(held_out),
                          'selected_train_seen_unique_groups': len({case['metadata']['group_id'] for case in seen}),
                          'selected_heldout_unique_groups': len({case['metadata']['group_id'] for case in held_out}),
                          'general_control_cases': len(controls),
                          'train_unique_groups': len(train_groups), 'test_unique_groups': len(test_groups),
                          'train_test_group_overlap': 0, 'identical_fix_prompt_overlap': 0,
                          'cases_by_partition_direction': dict(Counter(case['partition'] + ':' + case['direction']
                                                                     for case in seen + held_out)),
                          'model_outputs_used_for_selection': False}}


def answer_candidates(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        value = raw
    if isinstance(value, dict):
        value = next((value[field] for field in ('alternatives', 'translation', 'answer', 'tentative_translation') if field in value), None)
    if isinstance(value, list):
        return value if all(isinstance(item, str) for item in value) else []
    if isinstance(value, str):
        # Only explicit spaced list separators are split; an internal slash in
        # a canonical form or a source gloss is not silently rewritten.
        return re.split(r'\s+/\s+|;\s+|\r?\n', value)
    return []


def source_candidate_agreement(raw: str, targets: list[str]) -> dict:
    returned = {normalized(value) for value in answer_candidates(raw) if normalized(value)}
    expected = {normalized(value) for value in targets}
    shared = returned & expected
    return {'source_dictionary_candidate_set_equal': returned == expected,
            'source_dictionary_candidate_coverage': len(shared) / len(expected),
            'returned_candidate_source_support': len(shared) / len(returned) if returned else 0.0,
            'expected_candidates': sorted(expected), 'returned_candidates': sorted(returned),
            'missing_candidates': sorted(expected - returned), 'unexpected_candidates': sorted(returned - expected)}


def measure(case: dict, raw: str) -> dict:
    if case['kind'] == FACT_TASK:
        return source_candidate_agreement(raw, case['targets'])
    candidates = answer_candidates(raw)
    answer = '\n'.join(candidates)
    return {'authored_reference_string_equal': any(normalized(answer) == normalized(target) for target in case['targets'])}


def evaluate_cases(cases: list[dict], runner, progress=None) -> dict:
    records, grouped = [], defaultdict(list)
    for case in cases:
        started = time.monotonic()
        raw = runner.generate(case['prompt'])
        metrics = measure(case, raw)
        record = {**deepcopy(case), 'raw_output': raw, 'metrics': metrics,
                  'seconds': round(time.monotonic() - started, 3)}
        records.append(record)
        grouped[case['partition'] + ':' + case['direction']].append(metrics)
        if progress:
            progress(record)
    aggregates = {}
    for stratum, values in grouped.items():
        aggregates[stratum] = {'cases': len(values)}
        for field in ('source_dictionary_candidate_set_equal', 'source_dictionary_candidate_coverage',
                      'returned_candidate_source_support', 'authored_reference_string_equal'):
            available = [value[field] for value in values if field in value]
            if available:
                aggregates[stratum][field + '_mean'] = sum(available) / len(available)
    return {'records': records, 'metrics_by_partition_direction': aggregates}


def compare(plan: dict, *, adapter: Path, device: str = 'cuda', max_new_tokens: int = 96,
            runner_factory=ModelRunner, adapter_loader=attach_local_adapter, progress=None) -> dict:
    if device not in ('auto', 'cuda') or isinstance(max_new_tokens, bool) or not isinstance(max_new_tokens, int) or max_new_tokens < 1:
        raise ValueError('NF4 evaluation requires auto/cuda and a positive output limit')
    validate_adapter(adapter)
    runner = runner_factory(model_name=MODEL, revision=REVISION, adapter=None, device=device,
                            load_in_4bit=True, allow_download=False, max_new_tokens=max_new_tokens)
    runner._bundle[2].requires_grad_(False)
    runner._bundle[2].eval()
    results = {}
    for mode in ('base', 'adapted'):
        if mode == 'adapted':
            adapter_loader(runner, adapter)
        hook = (lambda record: progress(mode, record)) if progress else None
        results[mode] = {'adapter_enabled': mode == 'adapted', **evaluate_cases(plan['cases'], runner, hook)}
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--train', type=Path, required=True)
    parser.add_argument('--test', type=Path, required=True)
    parser.add_argument('--adapter', type=Path)
    parser.add_argument('--train-per-direction', type=int, default=1)
    parser.add_argument('--test-per-direction', type=int, default=2)
    parser.add_argument('--without-general-controls', action='store_true')
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--device', choices=('cuda', 'auto'), default='cuda')
    parser.add_argument('--max-new-tokens', type=int, default=96)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        train, test = read_rows(args.train), read_rows(args.test)
        plan = make_plan(train, test, train_per_direction=args.train_per_direction,
                         test_per_direction=args.test_per_direction,
                         include_general_controls=not args.without_general_controls)
        if args.max_new_tokens < 1:
            raise ValueError('max-new-tokens must be positive')
        if args.generate and args.adapter is None:
            raise ValueError('--generate requires a local --adapter')
        if args.output.exists():
            raise ValueError('Output already exists; choose a new path')
        report = {'execution': 'generate' if args.generate else 'dry-run',
                  'created_at': datetime.now(timezone.utc).isoformat(), 'model': MODEL, 'revision': REVISION,
                  'adapter': str(args.adapter) if args.adapter else None,
                  'configuration': {'load_in_4bit': True, 'quantization': 'NF4', 'do_sample': False,
                                    'max_new_tokens': args.max_new_tokens, 'device': args.device,
                                    'allow_download': False, 'same_base_before_adapter_attachment': True},
                  'selection': plan['selection'], 'cases': plan['cases'],
                  'source_splits': {name: {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                                    for name, path in (('train', args.train), ('test', args.test))},
                  'assessment_scope': 'source_dictionary_candidate_agreement_not_translation_accuracy',
                  'sentence_translation_accuracy': None, 'training_performed': False, 'merge_performed': False,
                  'downloads': 0, 'http_attempts': [], 'limitations': LIMITATIONS[:], 'modes': {}}
        if args.generate:
            for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY'):
                os.environ[key] = '1'
            def progress(mode, record):
                print(json.dumps({'mode': mode, 'id': record['id'], 'seconds': record['seconds'],
                                  'raw_output': record['raw_output']}, ensure_ascii=False), flush=True)
            with offline_http_guard() as attempts:
                report['modes'] = compare(plan, adapter=args.adapter, device=args.device,
                                          max_new_tokens=args.max_new_tokens, progress=progress)
            report['http_attempts'] = attempts
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'output': str(args.output), 'execution': report['execution'],
                          'selection': report['selection'],
                          'metrics': {mode: value['metrics_by_partition_direction'] for mode, value in report['modes'].items()}},
                         ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
