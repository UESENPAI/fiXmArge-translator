# fiXmArge · ConWas

```json
{
  "package": {
    "type": "code_only_preview",
    "Gradio": "5.49.1",
    "Python": "3.12",
    "Space_creation_upload_hardware_changes": false,
    "browser_login_equals_WSL_auth": false,
    "output_default": "runs/space-staging",
    "nonempty_output": "reject_no_overwrite_or_delete_use_new_--output",
    "payload_files": 13,
    "manifest_files": 1,
    "allowlist": [
      "app.py",
      "__init__.py",
      "infer.py",
      "rag.py",
      "grounding.py",
      "sentence_diagnostics.py",
      "demo.py",
      "standard_dictionary.py",
      "Space_README_dependencies_deploy_ignore_rules_MIT_notice"
    ],
    "standard_dictionary": "code_only_no_data",
    "missing_required_module": "fail_before_staging",
    "directory_copy_Git_file_collection_user_file_search": false,
    "manifest": [
      "name",
      "size",
      "SHA256"
    ],
    "verification_rejects": [
      "extra_files",
      "hash_changes",
      "symlinks"
    ],
    "excluded": [
      "data/raw",
      "data/processed",
      "data/research",
      "data/training",
      "data/curation",
      "data/external",
      "runs",
      "weights",
      "cache",
      ".git",
      ".env",
      "tokens"
    ],
    "upload_review_target": "new_staging_not_whole_project",
    "allowlist_does_not_scan_embedded_source_secrets": true,
    "requirements": "requirements-train_direct_pins_plus_Gradio_5.49.1_not_full_transitive_lock_or_cloud_compatibility_proof",
    "prepare_and_verify": "stdlib_only_no_install_no_model_execution"
  },
  "CLI_auth": {
    "huggingface_hub": "0.35.3",
    "hf_auth_login": "interactive_local_terminal_token_prompt",
    "browser_cookies_imported": false,
    "token_in_chat_commandline_logs_repository": false,
    "auth_cache_included": false,
    "package_tool_authenticates_or_reads_token": false,
    "creation_upload": "separate_operations"
  },
  "operator_paths": {
    "FIXMARGE_DATA_DIR": "reviewed_private_lexicon.jsonl_rules.jsonl_directory",
    "FIXMARGE_EXTERNAL_DIR": "separately_prepared_en_ja_lexicons.sqlite3_directory_default_data/external_no_Korean_dictionary",
    "HF_HOME": "host_prepared_cache_root_WSL_path_not_automatically_mounted",
    "FIXMARGE_MODEL": "Qwen/Qwen3-4B-Instruct-2507_or_host_local_model",
    "FIXMARGE_DEVICE": "auto_default_or_cpu_or_cuda_actual_memory_speed_unverified",
    "FIXMARGE_ADAPTER_PATH": "optional_reviewed_local_adapter_with_adapter_config.json_not_bundled",
    "FIXMARGE_ALLOW_MODEL_DOWNLOAD": "unset_or_0_cache_only_1_explicit_opt_in"
  },
  "UI": {
    "layout": "input_and_result_first_closed_evidence_uncertainty_details",
    "button_default": "existing_model_sentence_proposal"
  },
  "runtime": {
    "storage_or_private_volumes_created": false,
    "data_copied": false,
    "setting_path_creates_files": false,
    "empty_cloud_cache_generation": "fails_without_explicit_download",
    "offline_flags": "operator_review_HF_HUB_OFFLINE_TRANSFORMERS_OFFLINE_if_enabling_download",
    "secrets": "Space_Settings_Secrets_only",
    "Variables": "public_non_sensitive_settings_only",
    "private_vs_protected_public_runtime": "different_access_scope",
    "actual_dictionary_cache_GPU_memory_cloud_startup_validation": "pending_per_host",
    "CPU_Qwen4B_memory_speed": "not_guaranteed",
    "YAML_hardware_storage_suggestions_or_preload": false,
    "automatic_paid_hardware_selection": false,
    "zero_cost_guarantee": false,
    "plan_price_hardware": "account_review_before_actual_creation",
    "latest_docs_vs_local_CLI_UI": "may_differ"
  }
}
```

## ⚙️ · ConWas

### 01

```bash
.venv/bin/python scripts/prepare_space.py
.venv/bin/python scripts/prepare_space.py --verify-only
.venv/bin/python -m json.tool runs/space-staging/manifest.json
```

### 02

```bash
HF_HOME=/home/user/.cache/codex-dev/huggingface .venv/bin/hf auth login
HF_HOME=/home/user/.cache/codex-dev/huggingface .venv/bin/hf auth whoami
```

## ⚙️ · Coword

```json
{
  "technical_literals": [
    "runs/space-staging",
    "--output runs/space-staging-next",
    "app.py",
    "src/fixmarge",
    "__init__",
    "infer",
    "rag",
    "grounding",
    "sentence_diagnostics",
    "demo",
    "standard_dictionary",
    "manifest.json",
    "standard_dictionary.py",
    "data/raw",
    "data/processed",
    "data/research",
    "data/training",
    "data/curation",
    "data/external",
    "runs",
    ".git",
    ".env",
    ".gitignore",
    "requirements.txt",
    "requirements-train.txt",
    "huggingface-hub==0.35.3",
    "hf auth login",
    "FIXMARGE_DATA_DIR",
    "lexicon.jsonl",
    "rules.jsonl",
    "FIXMARGE_EXTERNAL_DIR",
    "lexicons.sqlite3",
    "HF_HOME",
    "FIXMARGE_MODEL",
    "Qwen/Qwen3-4B-Instruct-2507",
    "FIXMARGE_DEVICE",
    "auto",
    "cpu",
    "cuda",
    "FIXMARGE_ADAPTER_PATH",
    "adapter_config.json",
    "FIXMARGE_ALLOW_MODEL_DOWNLOAD",
    "0",
    "1",
    "HF_HUB_OFFLINE",
    "TRANSFORMERS_OFFLINE"
  ]
}
```

## 🔗 · WiD

- [↗ 01](https://huggingface.co/docs/hub/spaces-config-reference)
- [↗ 02](https://huggingface.co/docs/hub/spaces-overview)
- [↗ 03](https://huggingface.co/docs/huggingface_hub/guides/cli)
