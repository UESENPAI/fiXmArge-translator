#!/usr/bin/env python3
"""Inspect local training readiness without installing or downloading anything."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys


def inspect(include_torch=True):
    result = {"python": platform.python_version(), "platform": platform.system(),
              "architecture": platform.machine(), "packages": {}, "gpu": [], "notes": []}
    for name in ("torch", "transformers", "peft", "accelerate", "bitsandbytes",
                 "safetensors", "huggingface-hub"):
        try:
            result["packages"][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result["packages"][name] = None
    command = shutil.which("nvidia-smi")
    if command:
        try:
            completed = subprocess.run([command, "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10,
                check=False, shell=False)
            if completed.returncode == 0:
                for line in completed.stdout.splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) == 3:
                        result["gpu"].append({"name": parts[0], "vram_mib": int(parts[1]),
                                              "driver": parts[2], "source": "nvidia-smi"})
            else:
                result["notes"].append("nvidia-smi could not query the GPU")
        except (OSError, ValueError, subprocess.TimeoutExpired):
            result["notes"].append("nvidia-smi unavailable or timed out")
    else:
        result["notes"].append("nvidia-smi is not on PATH")
    if include_torch and result["packages"]["torch"]:
        try:
            import torch
            result["torch_cuda"] = {"available": torch.cuda.is_available(),
                                    "compiled_cuda": torch.version.cuda}
            if torch.cuda.is_available():
                result["torch_cuda"]["devices"] = [
                    {"name": torch.cuda.get_device_name(i),
                     "vram_bytes": torch.cuda.get_device_properties(i).total_memory,
                     "compute_capability": list(torch.cuda.get_device_capability(i))}
                    for i in range(torch.cuda.device_count())]
                result["torch_cuda"]["bf16"] = torch.cuda.is_bf16_supported()
        except (ImportError, OSError, RuntimeError) as exc:
            result["notes"].append("Torch import/CUDA check failed: " + str(exc))
    result["readiness"] = "GPU training not smoke-tested; this report is environment inspection only."
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-torch", action="store_true", help="Read installed version only; skip importing torch")
    args = parser.parse_args(argv)
    result = inspect(not args.no_torch)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Python {result['python']} / {result['platform']} / {result['architecture']}")
        for package, version in result["packages"].items():
            print(f"{package}: {version or 'not installed'}")
        for gpu in result["gpu"]:
            print(f"GPU: {gpu['name']} / {gpu['vram_mib']} MiB / driver {gpu['driver']}")
        for note in result["notes"]:
            print("Note: " + note)
        print(result["readiness"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
