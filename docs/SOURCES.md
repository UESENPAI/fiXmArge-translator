# fiXmArge · Coword

```json
{
  "checked": "2026-11-05",
  "source_verification_equals_training_or_redistribution_permission": false,
  "snapshots": [
    "data/source-lock.json",
    "configs/external-sources.lock.json"
  ],
  "models_at_initial_source_check": {
    "Qwen3_4B": {
      "revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
      "model_card_license_tokenizer_checked": true,
      "weights_downloaded_at_that_step": false
    },
    "Qwen3_1_7B": {
      "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
      "model_card_license_tokenizer_checked": true,
      "weights_downloaded_at_that_step": false
    },
    "MADLAD_400_3B_MT": "comparison_candidate_Qwen_trainer_not_supported_independent_eval_required"
  },
  "external_sources": {
    "JWN_1_1": {
      "normalized_senses": 364999,
      "actual_SQLite_lookup": true
    },
    "OEWN_2025": {
      "normalized_senses": 185129,
      "actual_lookup": true
    },
    "UniDic_2_1_2": {
      "original_downloaded": false,
      "synthetic_import_fixture_only": true
    }
  },
  "fix_sources": {
    "Hecate2": {
      "revision": "3df086be595c47a4dbbf97982feb2c2de0c9cf69",
      "rows": 331,
      "forms": 326,
      "transcription_errors": true
    },
    "Japanese_wordbook": {
      "rows": 337,
      "Read_Me_obtained": true,
      "reading_origin_and_etymology_hypotheses": "preserved"
    },
    "ZpDIC": {
      "entries": 363,
      "examples": 1,
      "scope": "some_senses_rules_directly_checked_not_full_dump"
    }
  },
  "normalization": {
    "source_and_license_per_external_record": true,
    "unit": "sense",
    "same_synset_ID_across_sources": "not_automatic_same_sense_merge",
    "missing_reading": "not_fabricated"
  },
  "OP_ED_sources": "data/evaluation_sources.json",
  "confidence_levels": "fan_research_hypothesized_etymology_and_official_parallel_separate",
  "source_rights_records": {
    "Qwen3_4B": "Apache_2_0",
    "Qwen3_1_7B": "Apache_2_0",
    "MADLAD_400_3B_MT": "Apache_2_0",
    "Japanese_WordNet": "Japanese_WordNet_and_Princeton_notices_required",
    "Open_English_WordNet": "CC_BY_4_0_and_Princeton_notices_required",
    "UniDic": "BSD_choice_AUTHORS_required_original_source_unverified",
    "Hecate2": "explicit_license_unconfirmed_local_research_not_default_training",
    "Japanese_wordbook": "unofficial_fan_research_default_training_excluded",
    "ZpDIC": "credits_Re,AER_Acacia_training_and_public_redistribution_permission_not_obtained",
    "game_guidelines": "section_6_official_content_AI_ML_training_use_or_supply_prohibited_section_9_fan_app_conditions_separate"
  }
}
```

## 🔗 · WiD

- [↗ 01](../data/source-lock.json)
- [↗ 02](../configs/external-sources.lock.json)
- [↗ 03](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- [↗ 04](https://huggingface.co/Qwen/Qwen3-1.7B)
- [↗ 05](https://huggingface.co/google/madlad400-3b-mt)
- [↗ 06](https://bond-lab.github.io/wnja/eng/downloads.html)
- [↗ 07](https://en-word.net/downloads)
- [↗ 08](https://clrd.ninjal.ac.jp/unidic/faq.html)
- [↗ 09](https://clrd.ninjal.ac.jp/unidic/copying/BSD)
- [↗ 10](https://github.com/Hecate2/fiXmArge-dictionary)
- [↗ 11](https://docs.google.com/spreadsheets/d/1ytGU7wmmOpmEegbIkkoFhcjkxeAKvC31B597HVFE9HI/edit)
- [↗ 12](https://zpdic.ziphil.com/dictionary/5729)
- [↗ 13](https://manosaba.com/guidelines)
- [↗ 14](../data/evaluation_sources.json)
- [↗ 15](RESEARCH.md)

## ⚖️

출처를 확인했다는 사실과 학습/재배포 허가를 확보했다는 사실은 다르다.
