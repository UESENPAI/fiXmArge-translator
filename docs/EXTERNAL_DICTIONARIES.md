# fiXmArge · Coword

```json
{
  "scope": {
    "purpose": [
      "support_etymology_hypothesis",
      "related_definition_and_synonym_lookup"
    ],
    "fix_reference_translation_or_parallel_training_data": false,
    "etymology_similarity_proves_decipherment": false
  },
  "sources": {
    "JWN": {
      "version": "1.1",
      "format": "gzip_SQLite",
      "fields": [
        "ja_and_en_headwords",
        "provided_reading",
        "definitions",
        "same_synset_synonyms"
      ],
      "latest_at_2026_11_05": "2.1_released_2026-10-24",
      "baseline_reason": "stdlib_SQLite_conversion_without_wn_and_omw-en_2.0_dependency",
      "parity_with_latest_claimed": false,
      "upstream_known_limitations": [
        "data_errors_possible",
        "definition_example_translations_may_not_exactly_align_synset"
      ],
      "source_commit": "7ad6d75bda9a94fe208d6aa083b55baf891100b1"
    },
    "OEWN": {
      "version": "2025",
      "format": "gzip_WN_LMF_XML",
      "fields": [
        "en_headwords",
        "provided_pronunciation",
        "definitions",
        "synonyms"
      ]
    }
  },
  "hash_lock": {
    "publisher_SHA256_found": false,
    "first_download": "TOFU_not_independent_authenticity_signature",
    "records": [
      "SHA256",
      "file_size",
      "URL",
      "version"
    ],
    "first_complete_download_only": true,
    "next_runs": "enforce_match",
    "local_lock": "data/external/sources.lock.json",
    "fallback_lock": "configs/external-sources.lock.json",
    "other_PC": "same_configs_lock",
    "mismatch": "review_source_change_do_not_delete_lock_for_auto_refresh"
  },
  "CLI": {
    "python_min": "3.10",
    "dependencies": "stdlib_only",
    "dry_run": "source_and_output_JSON_no_download_no_write",
    "probe": "max_64_KiB_per_source_no_save_stop_even_if_server_ignores_Range",
    "probe_success_means_complete_download": false,
    "default": [
      "download_originals_and_notices",
      "lock_SHA256",
      "convert_JSONL",
      "build_lexicons.sqlite3"
    ],
    "offline": "existing_originals_and_notices_only_missing_files_fail",
    "prepare_only": "download_and_JSONL_without_index",
    "reindex_only": "existing_complete_JSONL_no_network",
    "source_filter": [
      "wnja",
      "oewn"
    ],
    "limit": "first_N_senses_per_source_does_not_shrink_download_JWN_order_may_yield_English_first",
    "full_manifest_limit": 0,
    "local_input": "no_license_download_local_input_true_operator_must_supply_notices"
  },
  "storage": {
    "root": "data/external",
    "Git": "ignored",
    "gzip": "fixed_temp_file_only_no_tar_zip_path_extraction",
    "max_download_MiB": 128,
    "max_decompressed_GiB": 1,
    "incomplete_part_files": "removed",
    "download_hash_conversion_errors": "fail_not_empty_success"
  },
  "JSONL": {
    "record_unit": "one_headword_one_sense",
    "merge_polysemy": false,
    "id": "source_word_sense_and_synset_based",
    "language": [
      "ja",
      "en"
    ],
    "lemma": "source_headword_not_automatic_inflection_analysis",
    "reading": "source_string_or_null_never_fabricated",
    "glosses": "source_language_definitions",
    "synonyms": "same_language_same_synset_not_universal_contextual_substitutes",
    "pos": [
      "n",
      "v",
      "a",
      "r",
      "s"
    ],
    "source": "source_ID_and_pinned_version",
    "license": "row_data_license_ID"
  },
  "limits": {
    "Japanese_kanji_kana_dictionary_complete": false,
    "inflection_to_lemma_analyzer": false,
    "JWN_PWN3_synset_equals_OEWN2025_ID": false,
    "cross_version_sense_alignment_created": false,
    "reading_etymology_comparison": "requires_separate_morphology_reading_source"
  },
  "actual_2026_11_05": {
    "JWN_en_senses": 206941,
    "JWN_ja_senses": 158058,
    "JWN_definitions": "all_present",
    "JWN_readings": "all_missing",
    "OEWN_en_senses": 185129,
    "OEWN_senses_with_pronunciation": 60904
  },
  "SQLite": {
    "tables": [
      "entries(id_TEXT_PRIMARY_KEY,language_TEXT,payload_TEXT)",
      "terms(key_TEXT,entry_id_TEXT)"
    ],
    "index": "terms(key)",
    "payload": "JSONL_object",
    "term_keys": [
      "lemma",
      "provided_reading",
      "synonyms"
    ],
    "en_normalization": "NFC_strip_casefold",
    "ja_normalization": "NFC_strip",
    "build": "bulk_insert_complete_sources_then_key_index_then_validated_atomic_staging_replace",
    "partial_index_visible": false,
    "single_source_update": "include_other_existing_complete_source_JSONL",
    "Windows_open_DB": "close_readers_before_replace",
    "limited_index": "rebuild_with_--limit_0_for_full_search"
  },
  "UniDic": {
    "version": "2.1.2",
    "status": "unverified_download",
    "actual_original_CSV_conversion": false,
    "importer_validation": "synthetic_fixtures_only",
    "kind": "morphological_reading_not_definition_dictionary",
    "official_HTTPS_HEAD": "Python_certificate_chain_failure_Windows_TLS_failure",
    "TLS_validation_disabled": false,
    "mirror_reported_bytes": 140517811,
    "mirror_size_is_official_signature_or_hash": false,
    "configured_max_download_MiB": 128,
    "source_downloaded": false,
    "source_hash_lock_created": false,
    "local_import_example_budget_MiB": 160,
    "local_import_example_executed": false,
    "ZIP_reject": [
      "path_traversal",
      "symlinks",
      "encryption",
      "decompressed_total_over_1_GiB"
    ],
    "execution_or_path_extraction": false,
    "read_directly": [
      "lex.csv",
      "BSD",
      "AUTHORS"
    ],
    "feature_columns": [
      "f[6]=lForm",
      "f[7]=lemma"
    ],
    "MeCab_prefix_columns": 4,
    "CSV_zero_based_columns": {
      "reading": 10,
      "lemma": 11
    },
    "field_names": "compare_dicrc_rewrite.def_with_official_FAQ_else_record_fixed_layout_dependency",
    "actual_README_dicrc_kanji_rows_review": "TODO",
    "dedup_key": [
      "lemma",
      "lForm",
      "POS"
    ],
    "language": "ja",
    "kind_field": "morphological_reading",
    "glosses": [],
    "synonyms": [],
    "source": "unidic:2.1.2",
    "license": "BSD-3-Clause",
    "lForm_equals_pron": false,
    "invented_definitions": false,
    "index_combined": "complete_staging_WordNet_plus_readings_then_replace",
    "common_reindex_only": "include_complete_UniDic_JSONL_if_present",
    "index_separate": "lexicons-readings.sqlite3_existing_DB_unchanged",
    "index_auto": "separate_if_reading_conversion_over_120_seconds",
    "separate_reading_DB_RAG_connection_and_actual_reading_integration": "TODO"
  },
  "license_notice_records": {
    "output": "data/external/licenses/",
    "Princeton_notice_method": "official_WordNet_3.0_full_text_checked_2026_11_05_preserved_in_code_to_avoid_HTTP_403_omission",
    "other_notice_method": "pinned_version_URL_download",
    "lock_fields": [
      "source_URL",
      "SHA256",
      "acquisition_method"
    ],
    "JSONL_attribution": "source_version_license_per_row",
    "redistribution_bundle": [
      "JSONL",
      "licenses_directory",
      "manifest"
    ],
    "JWN": "Japanese_WordNet_own_license_plus_Princeton_WordNet",
    "OEWN": "CC_BY_4_0_plus_Princeton_WordNet",
    "UniDic": "BSD_3_Clause_plus_AUTHORS"
  }
}
```

## ⚙️ · ConWas

### 01

```powershell
python scripts/prepare_external_lexicons.py --dry-run
python scripts/prepare_external_lexicons.py --probe --timeout 10
python scripts/prepare_external_lexicons.py
python scripts/prepare_external_lexicons.py --offline
```

### 02

```json
{"id":"wnja:123:00000000-n","language":"ja","lemma":"架空の例","reading":null,"glosses":["형식 설명용 예시이며 실제 사전 항목이 아님"],"synonyms":[],"pos":"n","source":"wnja:1.1","license":"Japanese-WordNet + WordNet"}
```

### 03

```powershell
python scripts/prepare_japanese_readings.py --dry-run
```

### 04

```powershell
python scripts/prepare_japanese_readings.py --input C:/path/unidic-mecab-2.1.2_src.zip --max-archive-mib 160 --index separate
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "wn",
    "omw-en:2.0",
    "7ad6d75bda9a94fe208d6aa083b55baf891100b1",
    "data/external/sources.lock.json",
    "configs/external-sources.lock.json",
    "BSD-3-Clause",
    "data/external/licenses/",
    "--dry-run",
    "--probe",
    "lexicons.sqlite3",
    "--offline",
    "--prepare-only",
    "--reindex-only",
    "--source wnja",
    "--source oewn",
    "--limit 100",
    "limit",
    "--source wnja --input C:/path/wnjpn.db.gz --out C:/path/output",
    "local_input: true",
    "data/external/",
    ".part",
    "id",
    "language",
    "ja",
    "en",
    "lemma",
    "reading",
    "null",
    "glosses",
    "synonyms",
    "pos",
    "n",
    "v",
    "a",
    "r",
    "s",
    "source",
    "license",
    "pron",
    "Pronunciation",
    "entries(id TEXT PRIMARY KEY, language TEXT, payload TEXT)",
    "terms(key TEXT, entry_id TEXT)",
    "terms(key)",
    "payload",
    "--limit",
    "--limit 0",
    "unverified_download",
    "scripts/prepare_japanese_readings.py",
    "lex.csv",
    "BSD",
    "AUTHORS",
    "dicrc",
    "rewrite.def",
    "f[6]=lForm",
    "f[7]=lemma",
    "unidic-2.1.2.jsonl",
    "(lemma,lForm,POS)",
    "language=ja",
    "kind=morphological_reading",
    "source=unidic:2.1.2",
    "license=BSD-3-Clause",
    "lForm",
    "--index combined",
    "--index separate",
    "lexicons-readings.sqlite3",
    "auto"
  ]
}
```

## 🔗 · WiD

- [↗ 01](https://bond-lab.github.io/wnja/eng/downloads.html)
- [↗ 02](https://en-word.net/downloads)
- [↗ 03](https://github.com/bond-lab/wnja/blob/v1.1/LICENSE)
- [↗ 04](https://wordnet.princeton.edu/license-and-commercial-use)
- [↗ 05](https://github.com/globalwordnet/english-wordnet/blob/2025-edition/LICENSE.md)
- [↗ 06](https://github.com/globalwordnet/english-wordnet/blob/2025-edition/WNDB_License.txt)
- [↗ 07](https://mirrors.mit.edu/gentoo-distfiles/distfiles/d4/)
- [↗ 08](https://ftp.iij.ad.jp/pub/osdn.jp/unidic/58338/)
- [↗ 09](https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn.db.gz)
- [↗ 10](https://en-word.net/static/english-wordnet-2025.xml.gz)
- [↗ 11](https://clrd.ninjal.ac.jp/unidic/back_number.html)
- [↗ 12](https://clrd.ninjal.ac.jp/unidic_archive/cwj/2.1.2/unidic-mecab-2.1.2_src.zip)
- [↗ 13](https://clrd.ninjal.ac.jp/unidic/copying/BSD)
- [↗ 14](https://clrd.ninjal.ac.jp/unidic/faq.html)

## ⚖️

- [Japanese WordNet v1.1 원문](https://github.com/bond-lab/wnja/blob/v1.1/LICENSE)은 어떤 목적의 사용·복사·수정·배포도 비용 없이 허용하면서 저작권·라이선스·면책 고지를 내부 수정본을 포함한 모든 사본에 유지하도록 한다. 정확한 식별자는 표준 `BSD-3-Clause`가 아니라 **Japanese WordNet 자체 라이선스**로 남긴다. NICT 명칭으로 홍보·보증을 암시하면 안 된다.

- [공식 배포 지침](https://bond-lab.github.io/wnja/eng/downloads.html)은 웹·앱에서 사용할 경우 Japanese WordNet 사이트 링크와 버전·저작권 표시를 제공하고, 데이터를 재배포할 때 라이선스도 함께 배포하도록 한다.

- [Princeton WordNet 3.0 원문](https://wordnet.princeton.edu/license-and-commercial-use)은 상업 사용을 포함한 사용·수정·재배포를 허용하며 저작권·면책 등 원 고지를 유지하도록 한다.

- [OEWN 2025 LICENSE.md](https://github.com/globalwordnet/english-wordnet/blob/2025-edition/LICENSE.md)는 CC BY 4.0과 기반 Princeton WordNet 라이선스를 명시한다. Princeton WordNet 및 Open English WordNet 팀에 출처 표시하고, 변경 사실을 표시하며, 라이선스 링크·고지를 유지한다. [같은 버전 WNDB_License.txt](https://github.com/globalwordnet/english-wordnet/blob/2025-edition/WNDB_License.txt)도 함께 보존한다.

파생 사전을 외부에 배포한다면 **JSONL뿐 아니라 이 고지 디렉터리와 manifest도 함께** 배포하고 위 attribution을 앱의 자료 출처에 표시한다. 이 외부 사전 허용 조건은 게임의 fiXmArge 원문·팬 사전·가사에 대한 권한을 대신하지 않는다.

이 출력의 재배포용 고지는 사용자가 별도로 준비해야 한다.

공식 문서는 현대어용 해당 버전을 GPL/LGPL/BSD 중 선택할 수 있다고 설명한다. 여기서는 BSD-3-Clause를 선택하며 배포본의 **BSD 및 AUTHORS 원문**을 함께 보존한다. 웹·앱에서 출처와 선택한 BSD 라이선스를 표시하고 저자의 보증·홍보를 암시하지 않는다.

공식 게임 자료를 모델 학습에 쓸 수 있는지는 이 외부 사전 라이선스와 별도로 판단해야 한다.
