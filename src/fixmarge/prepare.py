"""Build provenance-aware lexical SFT and RAG artifacts (stdlib only)."""
from __future__ import annotations
import argparse, csv, hashlib, json, posixpath, re, sqlite3, urllib.request, zipfile
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ytGU7wmmOpmEegbIkkoFhcjkxeAKvC31B597HVFE9HI/edit"
HECATE_REV = "3df086be595c47a4dbbf97982feb2c2de0c9cf69"
HECATE_URL = "https://raw.githubusercontent.com/Hecate2/fiXmArge-dictionary/"+HECATE_REV+"/%E9%AD%94%E5%A5%B3%E8%AA%9E%E8%BE%9E%E5%85%B8fiXmArge.csv"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
PUNCT = str.maketrans({"•":"·","・":"·","’":"'","‘":"'","ʼ":"'","‐":"-","‑":"-"})

def canonical(text):
    return re.sub(r"\s+", " ", str(text).translate(PUNCT)).strip()

def stable_id(form):
    return "fx-" + hashlib.sha256(canonical(form).encode()).hexdigest()[:16]

def group_id(form):
    # Casing is NOT folded in lexical storage; possible case variants share a split.
    return "lex-" + hashlib.sha256(canonical(form).casefold().encode()).hexdigest()[:16]

def dump_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def dump_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False)+"\n")

def xlsx_rows(path, sheet_name="単語帳"):
    """Read sparse source cells without changing the source workbook."""
    with zipfile.ZipFile(path) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = ["".join(si.itertext()) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("s:si", NS)]
        rel = {r.attrib["Id"]:r.attrib["Target"] for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        sheets = ET.fromstring(z.read("xl/workbook.xml")).findall("s:sheets/s:sheet", NS)
        found = next((s for s in sheets if s.attrib.get("name") == sheet_name), None)
        if found is None:
            raise ValueError("Missing source sheet: "+sheet_name)
        target = rel[found.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
        member = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/"+target)
        if not member.startswith("xl/") or member not in z.namelist():
            raise ValueError("Invalid worksheet relationship")
        for row in ET.fromstring(z.read(member)).findall("s:sheetData/s:row", NS):
            cells = {}
            for c in row.findall("s:c", NS):
                letters = re.match(r"[A-Z]+", c.attrib.get("r","")).group()
                index = 0
                for letter in letters:
                    index = index*26 + ord(letter)-64
                v = c.find("s:v", NS)
                inline = c.find("s:is", NS)
                value = (v.text or "") if v is not None else "".join(inline.itertext()) if inline is not None else ""
                if c.attrib.get("t") == "s":
                    value = strings[int(value)]
                cells[index-1] = value
            yield [cells.get(i,"") for i in range(max(cells, default=-1)+1)]

def read_wordbook(path):
    rows = iter(xlsx_rows(path))
    header = next(rows)
    for n, values in enumerate(rows, 2):
        item = dict(zip(header, values))
        form = item.get("単語・フレーズ","").strip()
        if form:
            yield {"form":form, "ja":item.get("意味","").strip(),
                   "reading":item.get("ヨミ","").strip(), "reading_origin":item.get("ヨミの由来",""),
                   "pos":item.get("品詞",""), "etymology":item.get("メタ語源",""),
                   "notes":item.get("備考",""), "row":n}

def split_gloss(text):
    pieces=[]; part=[]; depth=0
    for char in text:
        if char in "(（[": depth+=1
        elif char in ")）]": depth=max(0,depth-1)
        if char in "/／;；" and not depth:
            if "".join(part).strip(): pieces.append("".join(part).strip())
            part=[]
        else: part.append(char)
    if "".join(part).strip(): pieces.append("".join(part).strip())
    return pieces

def fetch(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent":"fiXmArge-translator/0.1 source-preparation"})
    with urllib.request.urlopen(request, timeout=45) as r:
        content = r.read(30_000_001)
    if len(content)>30_000_000:
        raise ValueError("Source exceeds 30MB limit")
    path.write_bytes(content)

def prepare(root, download=False):
    raw = root/"data/raw"
    if download:
        if not (raw/"hecate.csv").exists():
            fetch(HECATE_URL, raw/"hecate.csv")
        if not (raw/"japanese_wordbook.xlsx").exists():
            fetch(SHEET_URL.split("/edit")[0]+"/export?format=xlsx", raw/"japanese_wordbook.xlsx")
    entries = {}
    observations = []
    conflicts = []
    counts = {}
    def get(form):
        key = canonical(form)
        if key not in entries:
            entries[key] = {"id":stable_id(key), "form":key, "aliases":[], "senses":{"ja":[],"en":[],"ko":[],"zh-Hans":[],"zh-Hant":[]},
                "pos":[], "readings":[], "notes":[], "etymology":[], "sources":[], "source_values":[],
                "status":"unreviewed", "rights_status":"not_cleared", "group_id":group_id(key)}
        ent = entries[key]
        if form != key and form not in ent["aliases"]: ent["aliases"].append(form)
        return ent
    def add(ent, field, value):
        if value and value not in ent[field]: ent[field].append(value)
    hecate = raw/"hecate.csv"
    source_rows=[]
    if hecate.exists():
        with hecate.open(encoding="utf-8-sig", newline="") as f:
            source_rows = list(csv.DictReader(f))
    counts["hecate_rows"] = len(source_rows)
    for n, r in enumerate(source_rows,2):
        if not r.get("fiXmArge","").strip(): continue
        ent = get(r["fiXmArge"].strip())
        vals = {"ja":r.get("日本語",""),"en":r.get("English",""),"zh-Hans":r.get("简体中文",""),"zh-Hant":r.get("繁体中文","")}
        for lang, value in vals.items():
            for gloss in split_gloss(value):
                if gloss not in ent["senses"][lang]: ent["senses"][lang].append(gloss)
        add(ent,"readings",r.get("日本語発音","").strip())
        add(ent,"sources","hecate-csv")
        ent["source_values"].append({"source":"hecate-csv","row":n,"values":vals,"status":"unreviewed_transcription"})
    book = raw/"japanese_wordbook.xlsx"
    if book.exists():
        book_rows = list(read_wordbook(book))
        counts["wordbook_rows"] = len(book_rows)
        for r in book_rows:
            ent=get(r["form"])
            add(ent,"sources","japanese-wordbook")
            if r["ja"]:
                # Keep conflicts explicit; a fan hypothesis must not silently override a transcription.
                current=ent["senses"]["ja"]
                if current and r["ja"] not in current and not any(r["ja"] in x for x in current):
                    conflicts.append({"form":ent["form"],"field":"ja","hecate":current[:],"wordbook":r["ja"],"resolution":"review_required"})
                if r["ja"] not in current: current.append(r["ja"])
            add(ent,"readings",r["reading"])
            add(ent,"pos",r["pos"])
            if r["notes"]: add(ent,"notes",r["notes"])
            if r["etymology"]:
                ent["etymology"].append({"text":r["etymology"],"status":"fan_hypothesis","source":"japanese-wordbook"})
            ent["source_values"].append({"source":"japanese-wordbook","row":r["row"],"ja":r["ja"],"reading":r["reading"],"reading_origin":r["reading_origin"],"status":"fan_research"})
    curation = root/"data/curation/corrections.json"
    overrides=json.loads(curation.read_text(encoding="utf-8")) if curation.exists() else []
    for fix in overrides:
        ent=get(fix["form"])
        for lang, glosses in fix.get("senses",{}).items():
            old=ent["senses"].get(lang,[])
            if old != glosses:
                observations.append({"form":ent["form"],"field":lang,"previous":old,"preferred":glosses,"source":fix["source"]})
            ent["senses"][lang]=glosses
        ent["status"]="source_crosschecked"
        add(ent,"sources",fix["source"])
        for pos in fix.get("pos",[]): add(ent,"pos",pos)
        for note in fix.get("notes",[]): add(ent,"notes",note)
    ko_path=root/"data/curation/ko_glosses.json"
    if ko_path.exists():
        for form, info in json.loads(ko_path.read_text(encoding="utf-8")).items():
            if canonical(form) not in entries: continue
            ent=get(form)
            ent["senses"]["ko"]=info["glosses"]
            ent["ko_status"]=info.get("status","machine_translated_draft")
            for note in info.get("notes",[]): add(ent,"notes",note)
    # Crosschecked meanings take priority over automatic Korean drafts.
    for fix in overrides:
        for lang,glosses in fix.get("senses",{}).items():
            get(fix["form"])["senses"][lang]=glosses
    reviews_path=root/"data/curation/conflict_review.json"
    reviews=json.loads(reviews_path.read_text(encoding="utf-8")) if reviews_path.exists() else {}
    resolved={canonical(f["form"]) for f in overrides}
    for form,review in reviews.items():
        ent=get(form)
        ent["review"]={"resolution":review["resolution"],"note":review.get("note","")}
        if review["resolution"]!="unresolved":
            resolved.add(canonical(form))
            for lang,glosses in review.get("senses",{}).items(): ent["senses"][lang]=glosses
            ent["status"]="source_reviewed"
    unresolved={c["form"] for c in conflicts if c["form"] not in resolved}
    for form in unresolved: entries[form]["has_conflict"]=True
    for ent in entries.values():
        # Only the requested three target languages are active retrieval senses.
        # The original Chinese fields remain unchanged in source_values for audit.
        ent["senses"]={lang:list(dict.fromkeys(g for value in ent["senses"][lang] for g in (split_gloss(value) if lang=="en" else [value]))) for lang in ("ja","en","ko")}
    rules_path=root/"data/curation/rules.jsonl"
    rules=[json.loads(line) for line in rules_path.read_text(encoding="utf-8").splitlines() if line.strip()] if rules_path.exists() else []
    for rule in rules: rule["rights_status"]="game_derived_not_eligible"
    processed=root/"data/processed"
    lexicon=sorted(entries.values(),key=lambda r:r["form"])
    # Variant spellings and identical reverse prompts must remain in one split.
    parent={e["id"]:e["id"] for e in lexicon}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(x,y):
        x,y=find(x),find(y)
        if x!=y: parent[max(x,y)]=min(x,y)
    seen={}
    for e in lexicon:
        keys=[("form",canonical(e["form"]).casefold())]
        keys += [(lang,"; ".join(e["senses"][lang])) for lang in ("ja","en","ko") if e["senses"][lang]]
        for key in keys:
            if key in seen: union(e["id"],seen[key])
            else: seen[key]=e["id"]
    for e in lexicon: e["group_id"]="family-"+find(e["id"])
    for e in lexicon: e["rights_status"]="game_derived_not_eligible"
    dump_jsonl(processed/"lexicon.jsonl",lexicon)
    dump_jsonl(processed/"rules.jsonl",rules)
    samples=[]; reverse={}
    for ent in lexicon:
        if ent.get("has_conflict"): continue
        for lang in ("ja","en","ko"):
            glosses=ent["senses"][lang]
            if not glosses: continue
            target="; ".join(glosses)
            meta={"group_id":ent["group_id"],"source":",".join(ent["sources"]),"status":ent.get("ko_status","unreviewed") if lang=="ko" else ent["status"],
                  "task":"lexical_translation","language":lang,"synthetic":True,"rights_status":ent["rights_status"],"entry_id":ent["id"]}
            # Lexical exercises, not claims about complete sentence grammar.
            samples.append({"messages":[{"role":"system","content":"Translate the quoted dictionary headword only. Preserve meaning; do not invent grammar or missing words."},
                {"role":"user","content":f"fiXmArge -> {lang}: {ent['form']}"},{"role":"assistant","content":target}],"metadata":{**meta,"direction":f"fix-to-{lang}"}})
            key=(lang,target)
            if key not in reverse: reverse[key]={"forms":[],"meta":{**meta,"direction":f"{lang}-to-fix"}}
            reverse[key]["forms"].append(ent["form"])
    for (lang,target),item in reverse.items():
        forms=sorted(set(item["forms"]))
        samples.append({"messages":[{"role":"system","content":"Return attested fiXmArge dictionary headwords for this lexical gloss. If multiple spellings or words match, list all alternatives. Preserve letter case, spaces, and punctuation."},
            {"role":"user","content":f"{lang} -> fiXmArge: {target}"},{"role":"assistant","content":" / ".join(forms)}],"metadata":{**item["meta"],"alternatives":forms}})
    for rule in rules:
        marker_entry=entries.get(canonical(rule["marker"]))
        samples.append({"messages":[{"role":"user","content":f"Explain the documented fiXmArge marker {rule['marker']} in Korean."},
            {"role":"assistant","content":rule["description_ko"]}],"metadata":{"group_id":marker_entry["group_id"] if marker_entry else "rule-"+rule["id"],"source":rule["source"],"status":rule["status"],
            "task":"rule_explanation","synthetic":True,"rights_status":"not_cleared"}})
    parallel_path=raw/"parallel.jsonl"
    real_count=0
    if parallel_path.exists():
        for line in parallel_path.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            p=json.loads(line)
            required=("source_text","target_text","source_language","target_language","document_id","source_id")
            if any(not p.get(k) for k in required): raise ValueError("Parallel sample missing required fields")
            if p.get("status") not in {"reviewed","official_parallel"}: continue
            samples.append({"messages":[{"role":"user","content":f"Translate {p['source_language']} -> {p['target_language']}: {p['source_text']}"},
                {"role":"assistant","content":p["target_text"]}],"metadata":{"group_id":"doc-"+p["document_id"],"source":p["source_id"],
                "status":p["status"],"task":"sentence_translation","synthetic":False,"rights_status":p.get("rights_status","not_cleared")}})
            real_count+=1
    train=[]; val=[]; research_train=[]; research_val=[]
    eligible_statuses={"self_authored","open_license","permission_granted"}
    for s in samples:
        n=int(hashlib.sha256(s["metadata"]["group_id"].encode()).hexdigest()[:8],16)%10
        if s["metadata"].get("rights_status") in eligible_statuses:
            (val if n==0 else train).append(s)
        else:
            (research_val if n==0 else research_train).append(s)
    dump_jsonl(root/"data/training/train.jsonl",train)
    dump_jsonl(root/"data/training/validation.jsonl",val)
    dump_jsonl(root/"data/research/train_candidates.jsonl",research_train)
    dump_jsonl(root/"data/research/validation_candidates.jsonl",research_val)
    docs=[]
    for e in lexicon:
        text=json.dumps({"form":e["form"],"senses":e["senses"],"readings":e["readings"],"etymology":e["etymology"],"notes":e["notes"]},ensure_ascii=False)
        docs.append({"id":e["id"],"text":text,"metadata":{"kind":"lexicon","source":e["sources"],"status":e["status"],"rights_status":e["rights_status"]}})
    for r in rules: docs.append({"id":r["id"],"text":r["marker"]+": "+r["description_ko"],"metadata":{"kind":"rule","source":r["source"],"status":r["status"]}})
    dump_jsonl(processed/"rag_documents.jsonl",docs)
    db=sqlite3.connect(processed/"rag.sqlite3")
    try:
        db.execute("DROP TABLE IF EXISTS documents")
        db.execute("CREATE TABLE documents(id TEXT PRIMARY KEY, text TEXT NOT NULL, metadata TEXT NOT NULL)")
        db.executemany("INSERT INTO documents VALUES(?,?,?)",[(d["id"],d["text"],json.dumps(d["metadata"],ensure_ascii=False)) for d in docs])
        db.commit()
    finally: db.close()
    locks={}
    for path in sorted(raw.glob("*")):
        if path.is_file(): locks[path.name]={"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bytes":path.stat().st_size}
    dump_json(processed/"source-lock.json",locks)
    dump_json(processed/"conflicts.json",{"candidates":conflicts,"unresolved":[c for c in conflicts if c["form"] in unresolved],"corrections":observations,"reviews":reviews})
    report={"source_counts":counts,"lexicon_entries":len(lexicon),"ko_entries":sum(bool(e["senses"]["ko"]) for e in lexicon),
        "unresolved_conflict_forms":len(unresolved),"excluded_conflict_forms":sorted(unresolved),"rules":len(rules),"rag_documents":len(docs),
        "train_samples":len(train),"validation_samples":len(val),"real_parallel_samples":real_count,
        "research_train_candidates":len(research_train),"research_validation_candidates":len(research_val),
        "train_group_count":len({s["metadata"]["group_id"] for s in train}),"validation_group_count":len({s["metadata"]["group_id"] for s in val}),
        "limitations":["Lexical/template exercises are not a sentence translation benchmark.","Fan hypotheses and inferred readings remain labeled.",
            "fiXmArge source redistribution/model-training permission is not established by the base-model license.",
            "Conflicting entries are retained for retrieval with provenance but excluded from SFT."],
        "release_status":"blocked_no_eligible_corpus" if not train else "eligible_records_only",
        "official_guideline":{"url":"https://manosaba.com/guidelines","section":6,"updated":"2026-10-21",
            "finding":"Official text, music, scenarios and other official content are explicitly prohibited as generative-AI/ML training data. Game-derived candidate records are excluded by default."}}
    dump_json(processed/"report.json",report)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--download-research-sources",action="store_true",help="Fetch fan dictionary snapshots for research only. They are NOT eligible training data; official guideline section 6 prohibits official-content ML training.")
    a=p.parse_args()
    print(json.dumps(prepare(a.root.resolve(),a.download_research_sources),ensure_ascii=False,indent=2))

if __name__=="__main__": main()
