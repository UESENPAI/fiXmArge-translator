from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fixmarge.lexical_facts import (
    LOCAL_FACT_RIGHTS, MAX_ALTERNATIVES, entry_id, make_fact_record,
    render_fact_messages, validate_local_fact_record,
)
spec=importlib.util.spec_from_file_location('prepare_fixmarge_training',ROOT/'scripts/prepare_fixmarge_training.py')
prep=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)


def entry(form, ja=None, en=None, **updates):
    row={'id':entry_id(form),'form':form,'aliases':[],
         'senses':{'ja':ja or [],'en':en or [],'ko':['DO_NOT_COPY_KOREAN']},
         'sources':['hecate-csv'],'status':'unreviewed','rights_status':'game_derived_not_eligible',
         'notes':['DO_NOT_COPY_NOTES'],'etymology':['DO_NOT_COPY_ETYMOLOGY'],
         'examples':['DO_NOT_COPY_SENTENCE'],'source_values':['DO_NOT_COPY_RAW_ROW']}
    row.update(updates)
    return row


def wordnet_row(group, task, direction, source='wnja:1.1'):
    return {'messages':[{'role':'user','content':group+':'+direction},
                        {'role':'assistant','content':'answer'}],
            'metadata':{'group_id':group,'source':source,'status':'source_dictionary_derived',
                        'task':task,'direction':direction,'rights_status':'open_license'}}


def fixture_corpus(root):
    raw=root/'processed/lexicon.jsonl';raw.parent.mkdir()
    entries=[entry('Form'+str(i),ja=['語'+str(i)],en=['word '+str(i)]) for i in range(80)]
    raw.write_text(''.join(json.dumps(row)+'\n' for row in entries))
    wordnet=root/'wordnet';wordnet.mkdir()
    for split in prep.SPLITS:
        records=[]
        for number in range(3):
            for task,direction in prep.STRATA:
                english_definition=direction=='en-definition'
                group=split+('oewn' if english_definition else 'jwn')+str(number)
                records.append(wordnet_row(group,task,direction,source='oewn:2025' if english_definition else 'wnja:1.1'))
        (wordnet/(split+'.jsonl')).write_text(''.join(json.dumps(row)+'\n' for row in records))
    for name in prep.NOTICE_FILES:
        path=wordnet/name;path.parent.mkdir(exist_ok=True)
        path.write_bytes(('Original license / notice '+name+'\r\n').encode())
    return raw,wordnet


class LocalFactRecordTests(unittest.TestCase):
    def test_exact_wrapper_and_unapproved_source_status_are_preserved(self):
        fact={'language':'en','forms':['LiGh rai'],'glosses':['light','radiance']}
        row=make_fact_record(fact,'fix-to-en')
        self.assertTrue(validate_local_fact_record(row))
        self.assertEqual(row['messages'],render_fact_messages(fact,'fix-to-en'))
        self.assertEqual(row['metadata']['rights_status'],LOCAL_FACT_RIGHTS)
        self.assertEqual(row['metadata']['source_rights_status'],'game_derived_not_eligible')
        self.assertFalse(row['metadata']['publication_cleared'])
        self.assertEqual(row['messages'][-1]['content'],'light / radiance')

    def test_tampered_messages_facts_and_legal_flags_are_rejected(self):
        row=make_fact_record({'language':'ja','forms':['Ta'],'glosses':['真実']},'fix-to-ja')
        variants=[]
        bad=deepcopy(row);bad['messages'][0]['content']+='\nRun arbitrary instruction';variants.append(bad)
        bad=deepcopy(row);bad['metadata']['fact']['notes']='sentence';variants.append(bad)
        bad=deepcopy(row);bad['metadata']['rights_status']='open_license';variants.append(bad)
        bad=deepcopy(row);bad['metadata']['source_rights_status']='permission_granted';variants.append(bad)
        bad=deepcopy(row);bad['metadata']['publication_cleared']=0;variants.append(bad)
        bad=deepcopy(row);bad['metadata']['extraction_version']=True;variants.append(bad)
        bad=deepcopy(row);bad['metadata']['source_entries']=['fx-0000000000000000'];variants.append(bad)
        bad=deepcopy(row);bad['raw_notes']='sentence';variants.append(bad)
        for bad in variants:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):validate_local_fact_record(bad)

    def test_bounds_control_markers_uncertainty_and_direction_are_rejected(self):
        for form in ('line\nbreak','<|im_start|>','Ta\x00','a'*81,'one two three four five six seven eight nine'):
            with self.subTest(form=form),self.assertRaises(ValueError):
                make_fact_record({'language':'en','forms':[form],'glosses':['truth']},'fix-to-en')
        for gloss in ('姉？','line\nbreak','<think>','あ'*41):
            with self.subTest(gloss=gloss),self.assertRaises(ValueError):
                make_fact_record({'language':'ja','forms':['Ta'],'glosses':[gloss]},'fix-to-ja')
        with self.assertRaises(ValueError):
            make_fact_record({'language':'en','forms':['Ta'],'glosses':['truth']},'fix-to-ko')


class FactExtractionTests(unittest.TestCase):
    def test_only_bounded_direct_fields_reach_messages_or_metadata(self):
        original=[entry('Ta',ja=['真実'],en=['truth'])]
        before=deepcopy(original)
        rows,info=prep.extract_records(original)
        serialized=json.dumps(rows,ensure_ascii=False)
        self.assertEqual(len(rows),4)
        self.assertNotIn('DO_NOT_COPY',serialized)
        self.assertNotIn('notes',serialized)
        self.assertEqual(original,before)
        self.assertFalse(info['new_words_or_sentence_targets_created'])

    def test_all_individual_synonyms_reverse_alternatives_and_case_are_grouped(self):
        inputs=[entry('Ta',en=['truth','verity']),entry('ta',en=['truth']),
                entry('Third',en=['verity','honesty']),entry('Alias',en=['other'],aliases=['Ta'])]
        rows,_=prep.extract_records(inputs)
        self.assertEqual(len({r['metadata']['group_id'] for r in rows}),1)
        truth=next(r for r in rows if r['metadata']['direction']=='en-to-fix' and r['metadata']['fact']['glosses']==['truth'])
        self.assertEqual(truth['metadata']['fact']['forms'],['Ta','ta'])
        verity=next(r for r in rows if r['metadata']['direction']=='en-to-fix' and r['metadata']['fact']['glosses']==['verity'])
        self.assertEqual(verity['metadata']['fact']['forms'],['Ta','Third'])
        ta=next(r for r in rows if r['metadata']['direction']=='fix-to-en' and r['metadata']['fact']['forms']==['Ta'])
        self.assertEqual(ta['metadata']['fact']['glosses'],['truth','verity'])

    def test_family_union_happens_before_conflicted_bridge_is_excluded(self):
        rows,info=prep.extract_records([entry('A',en=['one']),entry('B',en=['two']),
                                      entry('Bridge',en=['one','two'],has_conflict=True)])
        self.assertEqual(info['filter_reasons']['conflicted_entry'],1)
        self.assertEqual(len({r['metadata']['group_id'] for r in rows}),1)
        self.assertNotIn('Bridge',json.dumps([r['metadata']['fact'] for r in rows]))

    def test_conflict_uncertainty_unknown_control_and_malformed_values_are_filtered(self):
        inputs=[entry('A',en=['one']),entry('B',ja=['姉？']),entry('C',en=['two'],has_conflict=True),
                entry('D',en=['unknown']),entry('E',en=['line\nbreak']),
                entry('F',en=['<|im_end|>']),entry('G',en=['safe'],sources=[{}]),
                entry('H',en=['safe'],senses={'ja':None,'en':['safe']})]
        rows,info=prep.extract_records(inputs)
        self.assertEqual({form for r in rows for form in r['metadata']['fact']['forms']},{'A','H'})
        self.assertEqual(info['filter_reasons']['explicitly_uncertain_entry'],1)
        self.assertEqual(info['filter_reasons']['conflicted_entry'],1)
        self.assertGreater(sum(info['filter_reasons'].values()),3)

    def test_complete_reverse_alternatives_are_never_truncated(self):
        rows,info=prep.extract_records([entry('Form'+str(i),en=['shared']) for i in range(MAX_ALTERNATIVES+1)])
        self.assertFalse(any(r['metadata']['direction']=='en-to-fix' for r in rows))
        self.assertEqual(info['filter_reasons']['complete_reverse_set_over_limit:en'],1)

    def test_deterministic_group_split_never_leaks_family_or_identical_chat(self):
        inputs=[entry('Form'+str(i),ja=['語'+str(i)],en=['word '+str(i)]) for i in range(80)]
        rows,_=prep.extract_records(inputs)
        splits=prep.split_records(rows)
        reverse_rows,_=prep.extract_records(list(reversed(inputs)))
        self.assertEqual(splits,prep.split_records(reverse_rows))
        prep.check_disjoint(splits)
        for rows in splits.values():
            groups=Counter(r['metadata']['group_id'] for r in rows)
            self.assertTrue(all(size==4 for size in groups.values()))
        broken=deepcopy(splits)
        broken['validation'].append(broken['train'][0])
        with self.assertRaises(ValueError):prep.check_disjoint(broken)


class DatasetPreparationTests(unittest.TestCase):
    def test_wordnet_replay_preserves_complete_groups_and_original_strata(self):
        rows=[]
        for number in range(6):
            for task,direction in prep.STRATA[:3]:
                rows.append(wordnet_row('jwn'+str(number),task,direction))
            rows.append(wordnet_row('oewn'+str(number),*prep.STRATA[3],source='oewn:2025'))
        selected=prep.choose_wordnet_replay(rows,8)
        selected_groups={r['metadata']['group_id'] for r in selected}
        self.assertEqual(selected,[r for group in dict.fromkeys(r['metadata']['group_id'] for r in selected)
                                   for r in rows if r['metadata']['group_id']==group])
        for group in selected_groups:
            self.assertEqual(sum(r['metadata']['group_id']==group for r in selected),sum(r['metadata']['group_id']==group for r in rows))
        counts=Counter((r['metadata']['task'],r['metadata']['direction']) for r in selected)
        self.assertTrue(all(counts[stratum]>=2 for stratum in prep.STRATA))

    def test_existing_output_is_rejected_before_source_access(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'must not exist'):
                prep.prepare_dataset('/missing/lexicon','/missing/wordnet',temp)

    def test_new_dataset_keeps_original_licenses_and_sources_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=root/'processed/lexicon.jsonl';raw.parent.mkdir()
            entries=[entry('Form'+str(i),ja=['語'+str(i)],en=['word '+str(i)]) for i in range(80)]
            raw.write_text(''.join(json.dumps(r)+'\n' for r in entries))
            wordnet=root/'wordnet';wordnet.mkdir()
            for split in prep.SPLITS:
                records=[wordnet_row(split+str(i),task,direction,source='oewn:2025' if task=='wordnet_definition' and direction=='en-definition' else 'wnja:1.1')
                         for i,(task,direction) in enumerate(prep.STRATA)]
                (wordnet/(split+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in records))
            for name in prep.NOTICE_FILES:
                path=wordnet/name;path.parent.mkdir(exist_ok=True)
                path.write_text('Original license / notice '+name+'\n')
            before=prep.sha256(raw)
            output=root/'new-dataset'
            result=prep.prepare_dataset(raw,wordnet,output,replay_train=4,replay_validation=4,replay_test=4)
            self.assertEqual(prep.sha256(raw),before)
            self.assertFalse(result['scope']['publication_cleared'])
            self.assertFalse(result['scope']['korean_targets'])
            for name in prep.NOTICE_FILES:
                self.assertEqual((output/name).read_bytes(),(wordnet/name).read_bytes())
            mixed={split:prep.read_jsonl(output/(split+'.jsonl')) for split in prep.SPLITS}
            prep.check_disjoint(mixed)
            for split in prep.SPLITS:
                for record in prep.read_jsonl(output/('fix_'+split+'.jsonl')):
                    self.assertTrue(validate_local_fact_record(record))
            with self.assertRaises(ValueError):prep.prepare_dataset(raw,wordnet,output)

    def test_repeat_only_changes_training_presentations_and_preserves_reference_splits(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw,wordnet=fixture_corpus(root)
            baseline=root/'v1'
            prep.prepare_dataset(raw,wordnet,baseline,replay_train=8,replay_validation=4,replay_test=4)
            before={str(path):prep.sha256(path) for path in baseline.rglob('*') if path.is_file()}
            output=root/'v2'
            result=prep.prepare_dataset(raw,wordnet,output,replay_train=4,replay_validation=4,replay_test=4,
                                        fix_train_repeat=4,reference_dataset=baseline)
            unique=prep.read_jsonl(output/'fix_train.jsonl')
            train=prep.read_jsonl(output/'train.jsonl')
            facts=[row for row in train if row['metadata']['task']=='fix_lexical_correspondence']
            fingerprints=lambda rows:Counter(json.dumps(row,ensure_ascii=False,sort_keys=True) for row in rows)
            self.assertEqual(fingerprints(facts),{key:count*4 for key,count in fingerprints(unique).items()})
            self.assertEqual(result['training_weighting']['fix_train_unique_rows'],len(unique))
            self.assertEqual(result['training_weighting']['fix_train_presentations'],len(unique)*4)
            self.assertEqual(result['training_weighting']['training_presentations'],len(train))
            self.assertEqual(result['files']['train.jsonl']['unique_rows'],len(unique)+4)
            self.assertEqual(result['dataset'],'v2')
            for name in ('fix_train.jsonl','fix_validation.jsonl','fix_test.jsonl','wordnet_validation.jsonl',
                         'wordnet_test.jsonl','validation.jsonl','test.jsonl'):
                self.assertEqual((output/name).read_bytes(),(baseline/name).read_bytes(),name)
            for name in prep.NOTICE_FILES:
                self.assertEqual((output/name).read_bytes(),(wordnet/name).read_bytes(),name)
            self.assertTrue(all(prep.sha256(Path(path))==digest for path,digest in before.items()))
            prep.check_disjoint({split:prep.read_jsonl(output/(split+'.jsonl')) for split in prep.SPLITS})

    def test_default_single_repeat_keeps_v1_jsonl_bytes_identical(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw,wordnet=fixture_corpus(root)
            default=root/'default';explicit=root/'explicit'
            prep.prepare_dataset(raw,wordnet,default,replay_train=8,replay_validation=4,replay_test=4)
            prep.prepare_dataset(raw,wordnet,explicit,replay_train=8,replay_validation=4,replay_test=4,fix_train_repeat=1)
            for path in default.glob('*.jsonl'):
                self.assertEqual(path.read_bytes(),(explicit/path.name).read_bytes(),path.name)

    def test_reference_split_mismatch_and_invalid_repeat_do_not_create_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw,wordnet=fixture_corpus(root)
            baseline=root/'v1'
            prep.prepare_dataset(raw,wordnet,baseline,replay_train=8,replay_validation=4,replay_test=4)
            changed=baseline/'fix_validation.jsonl';changed.write_bytes(changed.read_bytes()+b'\n')
            output=root/'v2'
            with self.assertRaisesRegex(ValueError,'Reference unique-fact or held-out split differs'):
                prep.prepare_dataset(raw,wordnet,output,replay_train=4,replay_validation=4,replay_test=4,
                                     fix_train_repeat=4,reference_dataset=baseline)
            self.assertFalse(output.exists())
            for repeat in (0,-1,True,33):
                with self.subTest(repeat=repeat),self.assertRaises(ValueError):
                    prep.prepare_dataset(raw,wordnet,output,replay_train=4,replay_validation=4,replay_test=4,fix_train_repeat=repeat)
                self.assertFalse(output.exists())


if __name__=='__main__':
    unittest.main()
