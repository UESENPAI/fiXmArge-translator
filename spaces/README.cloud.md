---
title: fiXmArge · ConWas
emoji: "🌐"
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: "5.49.1"
python_version: "3.12"
app_file: app.py
pinned: false
---
# fiXmArge · ConWas

```json
{
  "product": {
    "product_routes": [
      "fix-to-ko",
      "ko-to-fix",
      "fix-to-ja",
      "ja-to-fix",
      "fix-to-en",
      "en-to-fix"
    ],
    "default_route": "fix-to-ko",
    "same_language_routes": "blocked",
    "natural_language_only_routes": "blocked",
    "fix_training_performed": false,
    "sentence_translation_improvement": "not_demonstrated",
    "sentence_grammar_verified": false
  },
  "cloud": {
    "space_created": false,
    "creation_HTTP_status": 402,
    "eligibility_authority": "Hugging_Face_server",
    "eligibility_verified_email_and_account_age_sufficient_to_predict": false,
    "hardware": "zero-a10g",
    "visibility": "private",
    "sdk": "gradio",
    "gradio_version": "5.49.1",
    "python_version": "3.12",
    "paid_hardware_or_subscription_or_storage_selected": false,
    "automatic_hardware_or_visibility_fallback": false,
    "cloud_startup_and_generation_verified": false,
    "existing_staging_and_ZIP": "historical_source_snapshot_rebuild_required",
    "staging_nonempty_output": "reject_without_overwrite",
    "wordnet_resources_in_bundle": true,
    "fix_lexicon_in_bundle": false,
    "FIXMARGE_DATA_DIR": "operator_reviewed_local_lexicon.jsonl_and_rules.jsonl_required",
    "missing_empty_invalid_lexicon_or_missing_rules": "stop_before_adapter_download_and_model_preload",
    "natural_language_fallback": false
  },
  "model": {
    "base_model": "Qwen/Qwen3-4B-Instruct-2507",
    "base_revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
    "adapter_repo": "uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge",
    "adapter_weights_revision": "c17943bf523779fb2dd75078148a50816dd52ed7",
    "adapter_path": "artifacts/qwen3-4b-wordnet-en-ja-lora-v1",
    "base_frozen": true,
    "merged_into_base": false,
    "base_files_before_after_sha256_equal": 12
  },
  "training": {
    "status": "completed",
    "date": "2026-11-06",
    "optimizer_steps": 256,
    "epochs": 1,
    "train_rows": 4096,
    "validation_rows": 256,
    "test_rows": 256,
    "seed": 42,
    "target_language_ratio_en_ja": "1:1",
    "trainable_lora_parameters": 16515072,
    "runtime_seconds": 2079.02,
    "selected_checkpoint": "checkpoint-256",
    "validation_loss_base": 5.2263,
    "validation_loss_adapter": 1.9733,
    "loss_scope": "dictionary_lexical_and_definition_tasks",
    "sentence_translation_accuracy": "not_measured",
    "train_batch_size": 4,
    "gradient_accumulation_steps": 4,
    "eval_batch_size": 4,
    "learning_rate": 2e-05,
    "lora_r": 8,
    "lora_alpha": 16,
    "max_sequence_length": 384,
    "observed_max_tokenizer_length": 163,
    "test_used_for_training_or_checkpoint_selection": false
  },
  "UI": {
    "input_and_result": "first_side_by_side",
    "details": "closed_evidence_uncertainty_raw_model"
  },
  "model_load": {
    "adapter_config_and_SHA256_checked_at_start": true,
    "merge": false,
    "precision": "BF16",
    "device": "CUDA",
    "cloud_cache": "independent_of_local_WSL",
    "request_GPU": "spaces.GPU(duration=60)",
    "queue_and_account_limits": true
  },
  "variables": {
    "FIXMARGE_CLOUD": "1",
    "FIXMARGE_DATA_DIR": "reviewed_fix_lexicon.jsonl_and_rules.jsonl_directory",
    "HF_TOKEN": "Space_Secret_only_private_adapter_read_permission"
  },
  "token_in_code_variables_logs": false,
  "training_limitations": {
    "loss_equals_sentence_accuracy": false,
    "rare_word_definition_errors": true,
    "candidate_repetition": true,
    "fix_trained": false
  }
}
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "Qwen/Qwen3-4B-Instruct-2507",
    "cdbee75f17c01a7cc42f958dc650907174af0554",
    "c17943bf523779fb2dd75078148a50816dd52ed7",
    "data/external/README.md",
    "data/external/NOTICE.txt",
    "data/external/licenses/",
    "FIXMARGE_CLOUD=1",
    "FIXMARGE_DATA_DIR",
    "lexicon.jsonl",
    "rules.jsonl",
    "HF_TOKEN",
    "zero-a10g",
    "spaces.GPU(duration=60)"
  ]
}
```

## 🔗 · WiD

- [↗ 01](https://huggingface.co/uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge)

## ⚖️

사전 출처·원문 라이선스·변환 고지는 `data/external/README.md`, `data/external/NOTICE.txt`, `data/external/licenses/`에 포함됩니다. 백본은 Apache 2.0이며, 다운로드한 어댑터의 원문 LICENSE·NOTICE도 보존합니다. 새 앱 코드는 MIT입니다. 코드 라이선스가 별도 모델·데이터 조건을 대신하지 않습니다.
