import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from fixmarge.prepare import canonical, group_id, read_wordbook, stable_id, split_gloss

class PrepareTests(unittest.TestCase):
    def test_case_preserved_but_grouped_against_leakage(self):
        self.assertNotEqual(stable_id("cOnzAI"), stable_id("cOnzAi"))
        self.assertEqual(group_id("cOnzAI"), group_id("cOnzAi"))
    def test_punctuation_canonical_and_whitespace(self):
        self.assertEqual(canonical("  pray・lee  "), "pray·lee")
        self.assertEqual(canonical("Syu   Tain"), "Syu Tain")
    def test_parenthesized_slash_is_not_a_sense_separator(self):
        self.assertEqual(split_gloss("of (possession/belonging); related"), ["of (possession/belonging)", "related"])
    def test_actual_group_split_and_provenance(self):
        root=Path(__file__).resolve().parents[1]
        paths=[root/"data/training"/p for p in ("train.jsonl","validation.jsonl")]
        if not all(p.exists() for p in paths): self.skipTest("Run prepare_data.py for source integration test")
        train,val=[[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] for p in paths]
        self.assertTrue(all(r["metadata"].get("rights_status") in {"self_authored","open_license","permission_granted"} for r in train+val))
        if not train and not val:
            paths=[root/"data/research"/p for p in ("train_candidates.jsonl","validation_candidates.jsonl")]
            train,val=[[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] for p in paths]
        self.assertFalse({x["metadata"]["group_id"] for x in train}&{x["metadata"]["group_id"] for x in val})
        lex=[json.loads(x) for x in (root/"data/processed/lexicon.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertTrue(all(e["sources"] and e["source_values"] for e in lex))
        conflicts={e["id"] for e in lex if e.get("has_conflict")}
        self.assertFalse({x["metadata"].get("entry_id") for x in train+val}&conflicts)
        self.assertTrue(all(x["metadata"]["synthetic"] for x in train+val if x["metadata"]["task"]=="lexical_translation"))
        prompts={}
        for record in train+val:
            prompt=record["messages"][-2]["content"]
            answer=record["messages"][-1]["content"]
            if prompt in prompts: self.assertEqual(prompts[prompt],answer)
            prompts[prompt]=answer
        by_form={e["form"]:e for e in lex}
        rules=[json.loads(x) for x in (root/"data/processed/rules.jsonl").read_text(encoding="utf-8").splitlines()]
        for rule in rules:
            if rule["marker"] not in by_form: continue
            expected=by_form[rule["marker"]]["group_id"]
            prompt=f"Explain the documented fiXmArge marker {rule['marker']} in Korean."
            record=next(r for r in train+val if r["messages"][0]["content"]==prompt)
            self.assertEqual(record["metadata"]["group_id"],expected)

if __name__=="__main__": unittest.main()
