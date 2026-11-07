"""Pinned, additive local dictionary imports for RAG, without training or fetching."""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any

from .prepare import canonical, group_id, split_gloss, stable_id

DISAGREEMENT_POLICY = (
    'Different normalized source sense sets are unresolved source-claim differences, '
    'not verified semantic contradictions or counts of new meanings. Existing claims are retained.'
)
PROTECTED_FIELDS = ('id', 'form', 'status', 'rights_status', 'group_id')


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _project_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError('Input paths must be nonempty project-relative strings')
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Input path leaves the project root')
    if not path.is_file():
        raise ValueError(f'Missing input file: {value}')
    return path


def _pinned(root: Path, record: dict, locks: dict[str, dict]) -> bytes:
    if not isinstance(record, dict) or not re.fullmatch('[0-9a-f]{64}', str(record.get('sha256', ''))):
        raise ValueError('Each input needs a pinned SHA256')
    path = _project_path(root, record.get('path'))
    content = path.read_bytes()
    if _sha256(content) != record['sha256']:
        raise ValueError(f'Input SHA256 mismatch: {record["path"]}')
    if 'bytes' in record and (type(record['bytes']) is not int or record['bytes'] != len(content)):
        raise ValueError(f'Input size mismatch: {record["path"]}')
    locks[record['path']] = {'sha256': _sha256(content), 'bytes': len(content)}
    return content


def _jsonl(content: bytes, name: str) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(content.decode('utf-8-sig').splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f'{name}:{number}: expected a JSON object')
        rows.append(item)
    return rows


def _manifest_check(root: Path, source: dict, locks: dict) -> None:
    reference = source.get('source_manifest')
    if reference is None:
        return
    manifest = json.loads(_pinned(root, reference, locks))
    items = manifest.get('items') if isinstance(manifest, dict) else None
    if not isinstance(items, list):
        raise ValueError('Source manifest needs an items list')
    matches = [item for item in items if isinstance(item, dict) and item.get('source_id') == source['id']]
    if len(matches) != 1:
        raise ValueError('Source manifest must contain exactly one matching source ID')
    item = matches[0]
    for key, expected in (('path', source['path']), ('sha256', source['sha256']),
                          ('source_url', source['source_url'])):
        if item.get(key) != expected:
            raise ValueError(f'Source manifest {key} mismatch for {source["id"]}')
    if source.get('revision') and item.get('revision') != source['revision']:
        raise ValueError(f'Source manifest revision mismatch for {source["id"]}')
    for key in ('review_status', 'rights_status'):
        if item.get(key) != source[key]:
            raise ValueError(f'Source manifest {key} mismatch for {source["id"]}')
    if 'bytes' in source and item.get('bytes') != source['bytes']:
        raise ValueError(f'Source manifest size mismatch for {source["id"]}')
    if source.get('expected_headers') and item.get('columns') != source['expected_headers']:
        raise ValueError(f'Source manifest columns mismatch for {source["id"]}')


def _claims(content: bytes, source: dict) -> tuple[list[dict], dict]:
    columns = source.get('columns', {})
    if not isinstance(columns, dict) or not isinstance(columns.get('form'), str) or not isinstance(columns.get('meaning'), str):
        raise ValueError('Each source needs form and meaning column names')
    result, skipped, metadata = [], [], {}
    if source['format'] == 'csv':
        reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig'), newline=''))
        if reader.fieldnames != source.get('expected_headers'):
            raise ValueError(f'CSV headers do not match registry: {source["id"]}')
        if any(name not in reader.fieldnames for name in columns.values()):
            raise ValueError('A configured CSV column is absent')
        records = [(number, row) for number, row in enumerate(reader, 2)]
        if any(set(row) != set(reader.fieldnames) or any(not isinstance(value, str) for value in row.values())
               for _, row in records):
            raise ValueError('CSV rows must match the declared columns')
        row_kind = 'csv_record_including_header_1based'
    elif source['format'] == 'claims_json':
        document = json.loads(content)
        if (not isinstance(document, dict) or document.get('schema_version') != 1
                or document.get('source_id') != source['id']
                or document.get('source_url') != source['source_url']
                or document.get('review_status') != source['review_status']
                or document.get('rights_status') != source['rights_status']
                or not isinstance(document.get('claims'), list)):
            raise ValueError('Claims JSON source identity or schema mismatch')
        metadata = {key: deepcopy(value) for key, value in document.items() if key != 'claims'}
        records = list(enumerate(document['claims'], 1))
        row_kind = 'claims_array_1based'
    else:
        raise ValueError('Dictionary format must be csv or claims_json')
    skip_forms = source.get('skip_forms', [])
    if not isinstance(skip_forms, list) or not all(isinstance(value, str) for value in skip_forms):
        raise ValueError('skip_forms must contain literal section labels')
    for number, row in records:
        if not isinstance(row, dict):
            raise ValueError('Source records must be objects')
        raw_form, meaning = row.get(columns['form']), row.get(columns['meaning'])
        if not isinstance(raw_form, str) or not raw_form.strip() or not isinstance(meaning, str) or not meaning.strip():
            raise ValueError(f'Missing form or meaning in {source["id"]} record {number}')
        if raw_form.strip() in skip_forms:
            skipped.append({'row': number, 'form': raw_form, 'reason': 'configured_section_label'})
            continue
        values = split_gloss(meaning) if source['language'] == 'en' else [meaning]
        result.append({'row': number, 'row_kind': row_kind, 'form': raw_form,
                       'senses': values, 'raw_row': deepcopy(row)})
    return result, {'total_records': len(records), 'skipped_records': skipped,
                    'source_snapshot_metadata': metadata}


def _sense_set(values: list[str], language: str) -> set[str]:
    # Case-only English variants are the same comparison key, but their exact
    # wording remains in senses/source_values. This is not semantic matching.
    return {canonical(value).casefold() if language == 'en' else canonical(value) for value in values}


def import_dictionaries(*, root: str | Path, registry: str | Path, output: str | Path) -> dict[str, Any]:
    """Build a fresh standalone lexicon/rules directory from pinned local files."""
    root = Path(root).resolve()
    registry = Path(registry)
    registry = registry if registry.is_absolute() else root / registry
    registry = registry.resolve()
    if not registry.is_relative_to(root) or not registry.is_file():
        raise ValueError('Registry must be an existing project file')
    output = Path(output)
    output = output if output.is_absolute() else root / output
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; choose a new directory')
    output = output.resolve()
    if not output.is_relative_to(root):
        raise ValueError('Output must remain inside the project root')
    content = registry.read_bytes()
    config = json.loads(content)
    if not isinstance(config, dict) or type(config.get('schema_version')) is not int or config['schema_version'] != 1:
        raise ValueError('Registry schema_version must be 1')
    base, sources = config.get('base'), config.get('sources')
    if not isinstance(base, dict) or not isinstance(sources, list) or not sources:
        raise ValueError('Registry needs a base and nonempty sources list')
    locks = {str(registry.relative_to(root)): {'sha256': _sha256(content), 'bytes': len(content)}}
    base_content = _pinned(root, base.get('lexicon'), locks)
    rules_content = _pinned(root, base.get('rules'), locks)
    _jsonl(rules_content, 'rules')
    rows = _jsonl(base_content, 'lexicon')
    entries, originals = {}, {}
    for entry in rows:
        form = entry.get('form')
        if not isinstance(form, str) or not form.strip() or canonical(form) in entries:
            raise ValueError('Base forms must be nonempty and canonically unique')
        if (not isinstance(entry.get('id'), str) or not isinstance(entry.get('senses'), dict)
                or not all(isinstance(entry['senses'].get(language, []), list)
                           and all(isinstance(value, str) for value in entry['senses'].get(language, []))
                           for language in ('en', 'ja', 'ko'))):
            raise ValueError('Malformed base entry')
        entries[canonical(form)] = deepcopy(entry)
        originals[canonical(form)] = deepcopy(entry)
    seen_sources, source_reports = set(), []
    for source in sources:
        if (not isinstance(source, dict) or not isinstance(source.get('id'), str) or not source['id']
                or source['id'] in seen_sources or source.get('language') not in ('en', 'ja', 'ko')
                or not isinstance(source.get('source_url'), str) or not source['source_url']
                or not isinstance(source.get('review_status'), str) or not source['review_status']
                or not isinstance(source.get('rights_status'), str) or not source['rights_status']):
            raise ValueError('Source identities, language, URL and statuses must be explicit and unique')
        seen_sources.add(source['id'])
        _manifest_check(root, source, locks)
        source_content = _pinned(root, source, locks)
        claims, source_report = _claims(source_content, source)
        groups = OrderedDict()
        for claim in claims:
            groups.setdefault(canonical(claim['form']), []).append(claim)
        added_forms, disagreements, appended = [], 0, 0
        for form, claims_for_form in groups.items():
            if form not in entries:
                entries[form] = {'id': stable_id(form), 'form': form, 'aliases': [],
                    'senses': {'ja': [], 'en': [], 'ko': []}, 'pos': [], 'readings': [],
                    'notes': [], 'etymology': [], 'sources': [], 'source_values': [],
                    'status': 'unreviewed', 'rights_status': source['rights_status'], 'group_id': group_id(form)}
                added_forms.append(form)
            entry = entries[form]
            language = source['language']
            current = entry['senses'].setdefault(language, [])
            previous = current[:]
            imported = list(dict.fromkeys(sense for claim in claims_for_form for sense in claim['senses']))
            if previous and _sense_set(previous, language) != _sense_set(imported, language):
                difference = {'language': language, 'source': source['id'], 'source_url': source['source_url'],
                    'source_sha256': source['sha256'], 'previous_senses': previous,
                    'imported_senses': imported, 'status': 'unresolved_source_claim_difference',
                    'semantic_contradiction_verified': False}
                if difference not in entry.setdefault('source_disagreements', []):
                    entry['source_disagreements'].append(difference)
                    disagreements += 1
                entry['has_conflict'] = True
            for sense in imported:
                if sense not in current:
                    current.append(sense)
                    appended += 1
            if language == 'ko' and not previous and 'ko_status' not in entry:
                entry['ko_status'] = 'unreviewed_fan_source_claims'
            if source['id'] not in entry.setdefault('sources', []):
                entry['sources'].append(source['id'])
            for claim in claims_for_form:
                if claim['form'] != entry['form'] and claim['form'] not in entry.setdefault('aliases', []):
                    entry['aliases'].append(claim['form'])
                value = {'source': source['id'], 'row': claim['row'], 'row_kind': claim['row_kind'],
                    'source_url': source['source_url'], 'snapshot_path': source['path'],
                    'snapshot_sha256': source['sha256'], 'status': source['review_status'],
                    'rights_status': source['rights_status'], 'language': language,
                    'values': {language: deepcopy(claim['senses'])}, 'raw_row': deepcopy(claim['raw_row'])}
                if source.get('revision'):
                    value['revision'] = source['revision']
                if source_report['source_snapshot_metadata']:
                    value['snapshot_metadata'] = deepcopy(source_report['source_snapshot_metadata'])
                if value not in entry.setdefault('source_values', []):
                    entry['source_values'].append(value)
                etymology_column = source.get('columns', {}).get('etymology')
                etymology = claim['raw_row'].get(etymology_column) if etymology_column else None
                if isinstance(etymology, str) and etymology.strip():
                    hint = {'text': etymology, 'status': 'fan_hypothesis', 'source': source['id'],
                            'row': claim['row'], 'snapshot_sha256': source['sha256']}
                    if hint not in entry.setdefault('etymology', []):
                        entry['etymology'].append(hint)
        source_reports.append({'id': source['id'], 'language': source['language'],
            'path': source['path'], 'sha256': source['sha256'], 'source_url': source['source_url'],
            'review_status': source['review_status'], 'rights_status': source['rights_status'],
            **source_report, 'imported_records': sum(len(values) for values in groups.values()),
            'distinct_canonical_forms': len(groups), 'new_forms': added_forms,
            'appended_literal_senses': appended, 'source_claim_differences': disagreements})
    for form, original in originals.items():
        merged = entries[form]
        if any(merged.get(key) != original.get(key) for key in PROTECTED_FIELDS):
            raise ValueError('Protected base identity or review/rights field changed')
        if merged.get('aliases', [])[:len(original.get('aliases', []))] != original.get('aliases', []):
            raise ValueError('Original aliases changed')
        if original.get('has_conflict') and not merged.get('has_conflict'):
            raise ValueError('Original source conflict was cleared')
        for language, senses in original['senses'].items():
            if merged['senses'].get(language, [])[:len(senses)] != senses:
                raise ValueError('Original meanings were changed')
    output.mkdir(parents=True, exist_ok=False)
    merged_rows = sorted(entries.values(), key=lambda entry: entry['form'])
    lexicon_bytes = ''.join(json.dumps(entry, ensure_ascii=False) + '\n' for entry in merged_rows).encode('utf-8')
    (output / 'lexicon.jsonl').write_bytes(lexicon_bytes)
    (output / 'rules.jsonl').write_bytes(rules_content)
    for relative, record in locks.items():
        actual = _project_path(root, relative).read_bytes()
        if _sha256(actual) != record['sha256']:
            raise ValueError('An input changed during import')
    (output / 'source-lock.json').write_text(json.dumps(locks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'schema_version': 1, 'status': 'completed', 'scope': 'local_additive_dictionary_RAG',
        'registry': str(registry.relative_to(root)), 'output': str(output.relative_to(root)),
        'base_entries': len(rows), 'merged_entries': len(merged_rows), 'new_entries': len(merged_rows) - len(rows),
        'base_Korean_entries': sum(bool(entry['senses'].get('ko')) for entry in rows),
        'merged_Korean_entries': sum(bool(entry['senses'].get('ko')) for entry in merged_rows),
        'base_unresolved_conflict_entries': sum(bool(entry.get('has_conflict')) for entry in rows),
        'merged_unresolved_claim_difference_or_conflict_entries': sum(bool(entry.get('has_conflict')) for entry in merged_rows),
        'source_disagreement_policy': DISAGREEMENT_POLICY, 'sources': source_reports,
        'all_input_hashes_verified_and_unchanged': True, 'input_files_modified': False,
        'base_identities_review_rights_and_meanings_preserved': True,
        'lexicon': {'bytes': len(lexicon_bytes), 'sha256': _sha256(lexicon_bytes)},
        'rules': {'bytes': len(rules_content), 'sha256': _sha256(rules_content)},
        'network_access': False, 'model_used': False, 'training_performed': False,
        'training_datasets_written': False, 'semantic_accuracy_verified': False,
        'source_review_or_publication_clearance_granted': False}
    (output / 'import_manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report
