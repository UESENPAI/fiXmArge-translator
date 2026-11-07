# fiXmArge · ConWas

```json
{
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
  "package": {
    "code_and_document_files": 14,
    "resource_files": 8,
    "payload_files": 22,
    "manifest": "deploy-manifest.json",
    "resources": [
      "data/external/lexicons.sqlite3",
      "four_original_license_notices",
      "NOTICE.txt",
      "README.md",
      "resource-manifest.json"
    ],
    "excluded": [
      "game_derived_fix_dictionary",
      "research_training_curation_data",
      "model_adapter_weights",
      "cache",
      "credentials"
    ],
    "project_root_bulk_upload": false,
    "legacy_prepare_space_code_only_payload_files": 13
  },
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
  "variables": {
    "FIXMARGE_CLOUD": "1",
    "FIXMARGE_EXTERNAL_DIR": "optional_bundled_data/external_override",
    "FIXMARGE_DATA_DIR": "reviewed_fix_lexicon_and_rules_directory"
  },
  "authentication": {
    "HF_TOKEN": "Space_Secrets_only_private_adapter_read_permission",
    "token_in_code_variables_manifest_chat_logs": false,
    "browser_login_equals_local_SDK_CLI_auth": false,
    "local_CLI": [
      "hf_auth_login",
      "hf_auth_whoami"
    ]
  },
  "startup": {
    "condition": "SPACE_ID_present_and_FIXMARGE_CLOUD_1",
    "downloads": "pinned_base_and_pinned_private_adapter_to_cloud_cache",
    "WSL_cache_uploaded": false,
    "adapter_file_allowlist": [
      "adapter_config.json",
      "adapter_model.safetensors",
      "training_manifest.json",
      "README.md",
      "LICENSE",
      "NOTICE"
    ],
    "adapter_file_count": 6,
    "checks": [
      "configuration",
      "training_metadata",
      "adapter_weight_SHA256"
    ],
    "backbone_merge": false,
    "precision": "BF16",
    "device": "CUDA",
    "preload": "startup",
    "NF4_or_bitsandbytes": false,
    "request_wrapper": "spaces.GPU(duration=60)",
    "limits": [
      "queue",
      "account_usage"
    ]
  },
  "deployment": {
    "CLI": "local_prepare_and_hash_verify_only",
    "SDK_helpers": "separate_explicit_operations_after_eligibility_dictionary_and_new_package_validation",
    "create_private_space": "private_ZeroGPU_only",
    "set_public_variables": "reviewed_Variables_only",
    "set_runtime_read_secret": "SDK_get_token_to_Secrets_only",
    "upload_deployment": "explicit_reviewed_manifest_SHA256_individual_CommitOperationAdd_then_commit_Git_LFS_hash_verify",
    "unapproved_remote_files": "stop_no_delete_no_bulk_upload",
    "helpers_called_by_CLI_or_ZIP_creation": false
  }
}
```

## ⚙️ · ConWas

### 01

```bash
.venv/bin/python scripts/deploy_space.py --source-root /home/user/code/fiXmArge-translator --resource-map /home/user/code/fiXmArge-translator/runs/space-resources-en-ja/file-map.json --output /home/user/code/fiXmArge-translator/runs/space-deployment-six-directions-new
.venv/bin/python scripts/deploy_space.py --output /home/user/code/fiXmArge-translator/runs/space-deployment-six-directions-new --verify-only
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "uesenpai/fixmarge-translator",
    "deploy-manifest.json",
    "data/external/lexicons.sqlite3",
    "NOTICE.txt",
    "README.md",
    "resource-manifest.json",
    "FIXMARGE_DATA_DIR",
    "lexicon.jsonl",
    "rules.jsonl",
    "FIXMARGE_CLOUD=1",
    "data/external",
    "FIXMARGE_EXTERNAL_DIR",
    "HF_TOKEN",
    "hf auth login",
    "hf auth whoami",
    "SPACE_ID",
    "Qwen/Qwen3-4B-Instruct-2507",
    "cdbee75f17c01a7cc42f958dc650907174af0554",
    "uesenpai/qwen3-4b-wordnet-en-ja-lora-v1_fiXmArge",
    "c17943bf523779fb2dd75078148a50816dd52ed7",
    "adapter_config.json",
    "adapter_model.safetensors",
    "training_manifest.json",
    "LICENSE",
    "NOTICE",
    "spaces.GPU(duration=60)",
    "/home/user/code/fiXmArge-translator",
    "scripts/prepare_space.py",
    "scripts/deploy_space.py",
    "create_private_space",
    "set_public_variables",
    "set_runtime_read_secret",
    "get_token()",
    "upload_deployment",
    "CommitOperationAdd"
  ]
}
```

## ⚖️

코드의 MIT 라이선스는 모델·사전의 개별 조건을 대신하지 않습니다.
