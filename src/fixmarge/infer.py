"""Evidence-first lookup CLI; model loading is an explicit optional action."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from typing import Any

from .rag import DIRECTIONS, LexiconRAG, build_prompt
from .grounding import ground_generation

REVIEWED_REVISIONS = {
    "Qwen/Qwen3-4B-Instruct-2507": "cdbee75f17c01a7cc42f958dc650907174af0554",
    "Qwen/Qwen3-1.7B": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
}


def resolve_revision(model_name: str, revision: str | None) -> str | None:
    return revision or REVIEWED_REVISIONS.get(model_name)


def generation_settings(torch: Any, device: str, load_in_4bit: bool) -> tuple[str, Any]:
    """Resolve hardware without loading a tokenizer, model, or adapter."""
    if device not in ("auto", "cpu", "cuda"):
        raise ValueError("device must be auto, cpu, or cuda")
    cuda_available = bool(torch.cuda.is_available())
    resolved = "cuda" if device == "auto" and cuda_available else "cpu" if device == "auto" else device
    if resolved == "cuda" and not cuda_available:
        raise RuntimeError("CUDA was requested but PyTorch cannot access CUDA. Check the CUDA-enabled PyTorch installation or use --device cpu.")
    if load_in_4bit and resolved != "cuda":
        raise RuntimeError("--load-in-4bit requires an available CUDA GPU in this project; omit it for CPU inference.")
    dtype = torch.float32
    if resolved == "cuda":
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    return resolved, dtype


def _load_bundle(*, model_name: str, adapter: str | None, allow_download: bool,
                 device: str = "auto", load_in_4bit: bool = False,
                 revision: str | None = None, device_map: str = "auto") -> tuple[Any, Any, Any]:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("Model generation requires PyTorch and Transformers. Install requirements-train.txt with a matching CUDA PyTorch wheel, or use the default dry run.") from exc
    local_only = not allow_download
    try:
        resolved_device, dtype = generation_settings(torch, device, load_in_4bit)
        selected_revision = resolve_revision(model_name, revision)
        common = {"local_files_only": local_only, "trust_remote_code": False}
        if selected_revision:
            common["revision"] = selected_revision
        tokenizer = AutoTokenizer.from_pretrained(model_name, **common)
        model_options = {**common, "torch_dtype": dtype, "use_safetensors": True}
        use_accelerate = importlib.util.find_spec("accelerate") is not None
        if resolved_device == "cuda" and use_accelerate:
            model_options["device_map"] = device_map
        if load_in_4bit:
            if not use_accelerate or importlib.util.find_spec("bitsandbytes") is None:
                raise RuntimeError("NF4 inference requires accelerate and bitsandbytes. Install requirements-train.txt and verify its CUDA support.")
            from transformers import BitsAndBytesConfig
            model_options["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=dtype)
        model = AutoModelForCausalLM.from_pretrained(model_name, **model_options)
        if "device_map" not in model_options:
            model = model.to(resolved_device)
        if adapter:
            try:
                from peft import PeftModel
            except ImportError as exc:
                raise RuntimeError("Loading --adapter requires peft. Install requirements-train.txt or omit --adapter.") from exc
            model = PeftModel.from_pretrained(model, adapter, local_files_only=local_only)
        model.eval()
        return torch, tokenizer, model
    except RuntimeError:
        raise
    except (OSError, ValueError, ImportError) as exc:
        policy = "Network downloads are disabled; use a local model or add --allow-download." if local_only else "Check the model identifier, dependencies, and available memory."
        raise RuntimeError(f"Could not load the model: {exc}. {policy}") from exc


def _generate_bundle(bundle: tuple[Any, Any, Any], messages: list[dict[str, str]], max_new_tokens: int) -> str:
    torch, tokenizer, model = bundle
    try:
        if getattr(tokenizer, "chat_template", None):
            prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
            prompt_text = "\n\n".join(f"{message['role'].upper()}:\n{message['content']}" for message in messages)
            prompt_text += "\n\nASSISTANT:\n"
        inputs = tokenizer(prompt_text, return_tensors="pt")
        inputs = {key: value.to(model.device) for key, value in inputs.items()}
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                                    pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id)
        return tokenizer.decode(output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    except RuntimeError:
        raise
    except (OSError, ValueError, ImportError) as exc:
        raise RuntimeError(f"Could not run the model: {exc}") from exc


class ModelRunner:
    """Load one frozen model once and reuse it for a local evaluation run."""
    def __init__(self, *, max_new_tokens: int = 512, **options: Any) -> None:
        self._bundle = _load_bundle(**options)
        self.max_new_tokens = max_new_tokens

    def generate(self, messages: list[dict[str, str]]) -> str:
        return _generate_bundle(self._bundle, messages, self.max_new_tokens)


def generate(messages: list[dict[str, str]], **options: Any) -> str:
    return ModelRunner(**options).generate(messages)


def main(argv: list[str] | None = None) -> int:
    # Windows may otherwise use cp949, which cannot print all Japanese/Chinese
    # source spellings included in the provenance-preserving JSON response.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Retrieve fiXmArge evidence; dry run is the default and never loads a model.")
    parser.add_argument("--text", required=True, help="Text to look up")
    parser.add_argument("--direction", choices=DIRECTIONS, default="fix-to-ko")
    parser.add_argument("--data-dir", help="Directory containing lexicon.jsonl and rules.jsonl")
    parser.add_argument("--external-dir", help="Directory containing the prepared English/Japanese lexicons.sqlite3 index")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Return lookup evidence and prompt only (default)")
    mode.add_argument("--generate", action="store_true", help="Explicitly load a model and generate a tentative answer")
    parser.add_argument("--model", help="Hugging Face causal model path or identifier; used only with --generate")
    parser.add_argument("--adapter", help="Optional PEFT adapter path or identifier")
    parser.add_argument("--revision", help="Base model revision; reviewed Qwen models default to the SHA pinned in configs")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto", help="Generation device (auto chooses CUDA when available)")
    parser.add_argument("--load-in-4bit", action="store_true", help="Explicitly load the base model in CUDA NF4, including when using an adapter")
    parser.add_argument("--allow-download", action="store_true", help="Allow model/adapter downloads during --generate")
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--strict-case", action="store_true", help="Disable case-insensitive fallback")
    parser.add_argument("--strict-punctuation", action="store_true", help="Disable middle-dot and apostrophe equivalence")
    args = parser.parse_args(argv)
    if args.generate and not args.model:
        parser.error("--generate requires --model")
    if args.max_new_tokens < 1:
        parser.error("--max-new-tokens must be positive")
    if args.load_in_4bit and args.device == "cpu":
        parser.error("--load-in-4bit cannot be combined with --device cpu")
    try:
        rag = LexiconRAG(args.data_dir, case_fallback=not args.strict_case,
                         punctuation_aliases={} if args.strict_punctuation else None,
                         external_dir=args.external_dir)
        result: dict[str, Any] = rag.lookup(args.text, args.direction)
        messages = build_prompt(result)
        result.update({"mode": "generate" if args.generate else "dry-run", "prompt": messages})
        if args.generate:
            raw = generate(messages, model_name=args.model, adapter=args.adapter,
                           allow_download=args.allow_download, max_new_tokens=args.max_new_tokens,
                           device=args.device, load_in_4bit=args.load_in_4bit, revision=args.revision)
            result["generation_raw"] = raw
            result["generation"] = json.dumps(ground_generation(result, raw), ensure_ascii=False)
            result["generation_config"] = {"model": args.model, "revision": resolve_revision(args.model, args.revision),
                                           "device": args.device, "load_in_4bit": args.load_in_4bit}
            result["messages"].append("generation contains dictionary-grounded lexical output; generation_raw preserves the unverified model response.")
        else:
            result["messages"].append("No model was loaded and no translation was generated.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc), "mode": "generate" if args.generate else "dry-run"}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
