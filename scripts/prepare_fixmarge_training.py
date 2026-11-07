#!/usr/bin/env python3
"""Prepare a new local bounded-fiXmArge/WordNet dataset without downloads."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fixmarge.lexical_facts import (
    SOURCE_IDS, SOURCE_RIGHTS, LOCAL_FACT_RIGHTS, MAX_ALTERNATIVES,
    bounded_text, entry_id, variant_key, make_fact_record, validate_local_fact_record,
)

SPLITS = ('train', 'validation', 'test')
STRATA = (('wordnet_translation','en-to-ja'), ('wordnet_translation','ja-to-en'),
          ('wordnet_definition','en-definition'), ('wordnet_definition','ja-definition'))
NOTICE_FILES = ('NOTICE.txt', 'licenses/Japanese-WordNet.txt', 'licenses/OEWN-WNDB-License.txt',
                'licenses/Princeton-WordNet.txt', 'licenses/Open-English-WordNet.md')
UNKNOWN_GLOSSES = {'不明', '意味不明', '不詳', '未詳', '未確定', '未判明', 'unknown', '-', '—'}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path):
    rows = []
    with Path(path).open(encoding='utf-8-sig') as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise ValueError(f'{path}:{number}: invalid JSON') from exc
            if not isinstance(row, dict):
                raise ValueError(f'{path}:{number}: expected object')
            rows.append(row)
    return rows


def extract_records(entries):
    """Union source families before filters; retain bounded direct fields only."""
    rejected = Counter()
    nodes = {}
    for item in entries:
        try:
            if not isinstance(item, dict):
                raise ValueError('entry_not_object')
            form = bounded_text(item.get('form'))
            if item.get('id') != entry_id(form):
                raise ValueError('entry_id_mismatch')
            if form in nodes:
                raise ValueError('duplicate_canonical_form')
            nodes[form] = item
        except ValueError as exc:
            rejected['entry_shape:' + str(exc)] += 1
    parent = {form: form for form in nodes}
    def find(form):
        while parent[form] != form:
            parent[form] = parent[parent[form]]
            form = parent[form]
        return form
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[max(a,b)] = min(a,b)
    seen = {}
    for form, item in sorted(nodes.items()):
        keys = [('form', variant_key(form))]
        aliases = item.get('aliases', [])
        if isinstance(aliases, list):
            for alias in aliases:
                try:
                    keys.append(('form', variant_key(bounded_text(alias))))
                except ValueError:
                    rejected['alias_not_bounded_for_grouping'] += 1
        senses = item.get('senses', {})
        if isinstance(senses, dict):
            for language in ('ja','en'):
                values = senses.get(language, [])
                if isinstance(values, list):
                    for gloss in values:
                        # Group before uncertainty/conflict filtering. No source prose enters records.
                        if isinstance(gloss, str) and gloss and len(gloss) <= 1000:
                            keys.append(('gloss', language, variant_key(gloss)))
        for key in keys:
            if key in seen:
                union(form, seen[key])
            else:
                seen[key] = form
    components = defaultdict(list)
    for form in nodes:
        components[find(form)].append(form)
    family = {form:'fixfact-' + min(entry_id(value) for value in values)
              for values in components.values() for form in values}
    clean = {}
    for form, item in sorted(nodes.items()):
        if item.get('has_conflict'):
            rejected['conflicted_entry'] += 1
            continue
        sources = item.get('sources')
        if (item.get('rights_status') != SOURCE_RIGHTS or not isinstance(sources, list) or not sources
                or any(not isinstance(source, str) or source not in SOURCE_IDS for source in sources)):
            rejected['unsupported_source_or_source_status'] += 1
            continue
        senses = item.get('senses')
        if not isinstance(senses, dict):
            rejected['invalid_senses'] += 1
            continue
        if any(isinstance(gloss, str) and ('?' in gloss or '？' in gloss)
               for language in ('ja','en')
               for gloss in (senses.get(language, []) if isinstance(senses.get(language, []), list) else [])):
            rejected['explicitly_uncertain_entry'] += 1
            continue
        kept = {}
        for language in ('ja','en'):
            glosses = senses.get(language, [])
            if not isinstance(glosses, list):
                rejected['invalid_gloss_list:' + language] += 1
                continue
            safe = []
            for gloss in glosses:
                try:
                    bounded_text(gloss, language=language)
                    if gloss.casefold() in UNKNOWN_GLOSSES:
                        raise ValueError('unknown_gloss_placeholder')
                    safe.append(gloss)
                except ValueError as exc:
                    rejected['gloss_filtered:' + language + ':' + str(exc)] += 1
            safe = sorted(set(safe))
            if len(safe) > MAX_ALTERNATIVES:
                rejected['complete_gloss_set_over_limit:' + language] += 1
            elif safe:
                kept[language] = safe
        if kept:
            clean[form] = {'glosses':kept, 'source_ids':sorted(set(sources)), 'family':family[form]}
        else:
            rejected['entry_without_bounded_ja_en_gloss'] += 1
    rows = []
    reverse = defaultdict(list)
    for form, item in sorted(clean.items()):
        for language, glosses in sorted(item['glosses'].items()):
            rows.append(make_fact_record({'language':language, 'forms':[form], 'glosses':glosses},
                        'fix-to-' + language, group_id=item['family'], source_ids=item['source_ids']))
            for gloss in glosses:
                reverse[language, gloss].append(form)
    for (language, gloss), forms in sorted(reverse.items()):
        forms = sorted(set(forms))
        if len(forms) > MAX_ALTERNATIVES:
            rejected['complete_reverse_set_over_limit:' + language] += 1
            continue
        groups = {clean[form]['family'] for form in forms}
        if len(groups) != 1:
            raise ValueError('Shared individual gloss was not assigned to one family')
        sources = sorted({source for form in forms for source in clean[form]['source_ids']})
        rows.append(make_fact_record({'language':language, 'forms':forms, 'glosses':[gloss]},
                    language + '-to-fix', group_id=next(iter(groups)), source_ids=sources))
    for row in rows:
        validate_local_fact_record(row)
    info = {'input_entries':len(entries), 'groupable_entries':len(nodes), 'included_entries':len(clean),
            'group_components_before_filtering':len(components),
            'included_families':len({value['family'] for value in clean.values()}),
            'included_entry_languages':dict(Counter(language for value in clean.values() for language in value['glosses'])),
            'filter_reasons':dict(sorted(rejected.items())),
            'excluded_fields':['notes','etymology','examples','readings','pos','source_values','ko','zh-Hans','zh-Hant'],
            'new_words_or_sentence_targets_created':False}
    return rows, info


def split_records(rows, seed=42):
    result = {split:[] for split in SPLITS}
    for row in rows:
        group = row['metadata']['group_id']
        bucket = int(hashlib.sha256(f'{seed}:{group}'.encode()).hexdigest()[:8], 16) % 10
        split = 'train' if bucket < 8 else 'validation' if bucket == 8 else 'test'
        result[split].append(row)
    check_disjoint(result)
    return result


def check_disjoint(splits):
    group_sets = {name:{row['metadata']['group_id'] for row in rows} for name,rows in splits.items()}
    fingerprints = {name:{json.dumps(row['messages'],ensure_ascii=False,sort_keys=True) for row in rows}
                    for name,rows in splits.items()}
    names = list(splits)
    for i, left in enumerate(names):
        for right in names[i+1:]:
            if group_sets[left] & group_sets[right] or fingerprints[left] & fingerprints[right]:
                raise ValueError('Group or identical-prompt-answer leakage across splits')


def choose_wordnet_replay(rows, requested, *, seed=42, split='train'):
    groups = defaultdict(list)
    for row in rows:
        meta = row.get('metadata', {})
        stratum = meta.get('task'), meta.get('direction')
        if (stratum not in STRATA or meta.get('rights_status') != 'open_license'
                or meta.get('source') not in ('wnja:1.1','oewn:2025')
                or not isinstance(meta.get('group_id'), str) or not meta['group_id']):
            raise ValueError('Replay source must be the existing licensed four-stratum WordNet corpus')
        groups[meta['group_id']].append(row)
    targets = {key:requested//len(STRATA)+(index < requested%len(STRATA)) for index,key in enumerate(STRATA)}
    counts = Counter()
    selected = []
    ordered = sorted(groups, key=lambda value: hashlib.sha256(f'{seed}:{split}:{value}'.encode()).hexdigest())
    for group in ordered:
        records = groups[group]
        strata = Counter((r['metadata']['task'],r['metadata']['direction']) for r in records)
        if any(counts[key] < targets[key] for key in strata):
            selected.extend(records)
            counts.update(strata)
    if any(counts[key] < targets[key] for key in STRATA):
        raise ValueError('Not enough source groups for balanced WordNet replay')
    return selected


def prepare_dataset(lexicon, wordnet, output, *, seed=42, replay_train=1024, replay_validation=128, replay_test=128,
                    fix_train_repeat=1, reference_dataset=None):
    lexicon, wordnet, output = Path(lexicon).resolve(), Path(wordnet).resolve(), Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('Output must not exist; original data and prior runs are never overwritten')
    output = output.resolve()
    for protected in (lexicon.parent, wordnet):
        if output == protected or protected in output.parents or output in protected.parents:
            raise ValueError('Output overlaps an original data directory')
    if any(type(value) is not int or value < 1 for value in (replay_train,replay_validation,replay_test)):
        raise ValueError('Positive WordNet replay sizes are required')
    if type(fix_train_repeat) is not int or not 1 <= fix_train_repeat <= 32:
        raise ValueError('fix_train_repeat must be an integer between 1 and 32')
    reference = Path(reference_dataset).resolve() if reference_dataset is not None else None
    if reference is not None and (output == reference or reference in output.parents or output in reference.parents):
        raise ValueError('Output overlaps the reference dataset')
    required = [lexicon] + [wordnet/(split+'.jsonl') for split in SPLITS] + [wordnet/name for name in NOTICE_FILES]
    if any(not path.is_file() or path.is_symlink() for path in required):
        raise ValueError('Existing local source corpora, NOTICE and four license texts are required')
    before = {str(path):sha256(path) for path in required}
    raw = read_jsonl(lexicon)
    facts, filters = extract_records(raw)
    fixed = split_records(facts,seed)
    if any(not fixed[split] for split in SPLITS):
        raise ValueError('All three grouped fiXmArge splits require at least one record')
    originals = {split:read_jsonl(wordnet/(split+'.jsonl')) for split in SPLITS}
    check_disjoint(originals)
    sizes = {'train':replay_train,'validation':replay_validation,'test':replay_test}
    replay = {split:choose_wordnet_replay(originals[split],sizes[split],seed=seed,split=split) for split in SPLITS}
    check_disjoint(replay)
    mixed = {}
    for number, split in enumerate(SPLITS):
        presentations = fixed[split] * (fix_train_repeat if split == 'train' else 1)
        mixed[split] = presentations + replay[split]
        random.Random(seed+number).shuffle(mixed[split])
    check_disjoint(mixed)
    reference_files = {}
    def serialized(rows):
        return ''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows).encode('utf-8')
    if reference is not None:
        expected = {'fix_'+split+'.jsonl':fixed[split] for split in SPLITS}
        expected.update({'wordnet_'+split+'.jsonl':replay[split] for split in ('validation','test')})
        expected.update({split+'.jsonl':mixed[split] for split in ('validation','test')})
        for name,rows in expected.items():
            path=reference/name
            if not path.is_file() or path.is_symlink() or path.read_bytes()!=serialized(rows):
                raise ValueError('Reference unique-fact or held-out split differs: '+name)
            reference_files[str(path)]=sha256(path)
        reference_train=reference/'wordnet_train.jsonl'
        if not reference_train.is_file() or reference_train.is_symlink():
            raise ValueError('Reference WordNet training subset is required')
        original_train={json.dumps(row,ensure_ascii=False,sort_keys=True) for row in read_jsonl(reference_train)}
        if any(json.dumps(row,ensure_ascii=False,sort_keys=True) not in original_train for row in replay['train']):
            raise ValueError('WordNet replay selection is not within the original training subset')
        reference_files[str(reference_train)]=sha256(reference_train)
        before.update(reference_files)
    output.mkdir(parents=True,exist_ok=False)
    files = {}
    for prefix, splits in (('',mixed),('fix_',fixed),('wordnet_',replay)):
        for split, rows in splits.items():
            path = output/(prefix+split+'.jsonl')
            path.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
            files[path.name] = {'rows':len(rows),'unique_rows':len({json.dumps(row,ensure_ascii=False,sort_keys=True) for row in rows}),'bytes':path.stat().st_size,'sha256':sha256(path),
                                'groups':len({r['metadata']['group_id'] for r in rows}),
                                'tasks':dict(Counter(r['metadata']['task'] for r in rows)),
                                'directions':dict(Counter(r['metadata'].get('direction') for r in rows))}
    for name in NOTICE_FILES:
        destination = output/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(wordnet/name,destination)
        files[name] = {'bytes':destination.stat().st_size,'sha256':sha256(destination),'original_text_preserved':True}
    scope = {
        'local_experiment_only':True,'publication_cleared':False,'new_rights_status':LOCAL_FACT_RIGHTS,
        'source_rights_status':SOURCE_RIGHTS,'source_permission_or_open_license_claimed':False,
        'selection':'bounded_canonical_headwords_and_direct_short_ja_en_gloss_fields_only',
        'sentence_supervision':False,'korean_targets':False,'new_grammar_or_translations_generated':False,
        'source_raw_notes_examples_lyrics_copied':False,
    }
    (output/'local-fact-scope.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n')
    files['local-fact-scope.json']={'bytes':(output/'local-fact-scope.json').stat().st_size,'sha256':sha256(output/'local-fact-scope.json')}
    if any(sha256(Path(path)) != digest for path,digest in before.items()):
        raise ValueError('An original source changed during dataset preparation')
    manifest = {'schema_version':1,'dataset':output.name,'seed':seed,'scope':scope,
                'extraction':filters,'split_policy':'SHA256(seed:family)%10 train0-7 validation8 test9',
                'grouping':'All shared individual JA/EN glosses and case/punctuation/alias variants unioned before filters',
                'wordnet_replay':'Whole existing original groups, balanced four strata; requested sizes may be exceeded to retain groups',
                'requested_wordnet_rows':sizes,'source_files':before,
                'training_weighting':{'fix_train_repeat':fix_train_repeat,
                    'fix_train_unique_rows':len(fixed['train']),
                    'fix_train_presentations':len(fixed['train'])*fix_train_repeat,
                    'wordnet_train_rows':len(replay['train']),
                    'training_unique_rows':files['train.jsonl']['unique_rows'],
                    'training_presentations':len(mixed['train']),
                    'validation_or_test_repetition':False,
                    'fixed_component_files':'unique_unweighted_records'},
                'reference_split_files_sha256':reference_files,
                'presentation_counts_by_split':{split:{'fix':len(fixed[split])*(fix_train_repeat if split=='train' else 1),
                    'wordnet':len(replay[split]),'total':len(mixed[split])} for split in SPLITS},
                'original_files_sha256_unchanged':True,'cross_split_group_or_identical_chat_overlap':0,
                'licenses_and_notice_preserved_verbatim':True,'files':files}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lexicon',type=Path,default=ROOT/'data/processed/lexicon.jsonl')
    parser.add_argument('--wordnet',type=Path,default=ROOT/'data/training/wordnet-en-ja-v1')
    parser.add_argument('--output',type=Path,default=ROOT/'data/training/fixmarge-wordnet-v1')
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--fix-train-repeat',type=int,default=1)
    parser.add_argument('--wordnet-train-limit',type=int,default=1024)
    parser.add_argument('--reference-dataset',type=Path)
    args=parser.parse_args()
    try:
        result=prepare_dataset(args.lexicon,args.wordnet,args.output,seed=args.seed,
                               fix_train_repeat=args.fix_train_repeat,replay_train=args.wordnet_train_limit,
                               reference_dataset=args.reference_dataset)
    except (OSError,ValueError,TypeError) as exc:
        parser.exit(2,str(exc)+'\n')
    print(json.dumps({'output':str(args.output),'rows':{name:result['files'][name+'.jsonl']['rows'] for name in SPLITS},
                      'fix_rows':{name:result['files']['fix_'+name+'.jsonl']['rows'] for name in SPLITS},
                      'training_weighting':result['training_weighting'],
                      'filters':result['extraction']['filter_reasons']},ensure_ascii=False))


if __name__=='__main__':
    main()
