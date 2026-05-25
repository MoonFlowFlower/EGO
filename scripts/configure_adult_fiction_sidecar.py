#!/usr/bin/env python3
"""Configure EgoOperator's local adult-fiction creative sidecar.

This helper does not download models or mutate EgoOperator runtime state. It
detects a local OpenAI-compatible server, chooses the best already-loaded model
for #80 smoke testing, and prints environment variables for the caller to use.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://localhost:1234/v1"
DEFAULT_API_KEY = "lm-studio"


def normalize_base_url(raw: str) -> str:
    base = (raw or DEFAULT_BASE_URL).strip().rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


def models_url(base_url: str) -> str:
    return f"{normalize_base_url(base_url)}/models"


def fetch_model_ids(base_url: str, timeout_seconds: float) -> list[str]:
    req = urllib.request.Request(models_url(base_url), headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    data = payload.get("data", [])
    ids: list[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                ids.append(item["id"])
    return ids


def model_score(model_id: str) -> tuple[int, int]:
    """Prefer Cydonia IQ4_XS, then nearby practical Cydonia/Skyfall quants."""

    value = model_id.lower()
    score = 0
    if "cydonia" in value:
        score += 1000
    elif "skyfall" in value:
        score += 600
    elif "thedrummer" in value:
        score += 250

    if "24b" in value:
        score += 100
    if "36b" in value:
        score += 40

    quant_preferences = [
        ("iq4_xs", 300),
        ("q4_k_m", 260),
        ("q4_k_s", 230),
        ("iq3_m", 210),
        ("iq3_xs", 190),
        ("q3_k_m", 160),
        ("q3_k_s", 120),
        ("q2_k", 70),
    ]
    for token, bonus in quant_preferences:
        if token in value:
            score += bonus
            break

    # Avoid accidentally choosing huge full-precision files when a quant is loaded.
    if "bf16" in value or "q8_0" in value:
        score -= 250
    return score, -len(model_id)


def choose_model(model_ids: list[str], explicit_model: str = "") -> str | None:
    if explicit_model:
        return explicit_model
    if not model_ids:
        return None
    return max(model_ids, key=model_score)


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def powershell_lines(base_url: str, api_key: str, model: str) -> list[str]:
    return [
        "$env:ADULT_FICTION_PROVIDER='openai_compatible'",
        f"$env:ADULT_FICTION_BASE_URL={ps_quote(normalize_base_url(base_url))}",
        f"$env:ADULT_FICTION_API_KEY={ps_quote(api_key)}",
        f"$env:ADULT_FICTION_MODEL={ps_quote(model)}",
    ]


def benchmark_command(model: str, base_url: str, api_key: str) -> str:
    return (
        "python .\\scripts\\benchmark_adult_fiction_provider.py `\n"
        "  --provider openai_compatible `\n"
        f"  --base-url {json.dumps(normalize_base_url(base_url))} `\n"
        f"  --api-key {json.dumps(api_key)} `\n"
        f"  --models {json.dumps(model)} `\n"
        "  --runtime-compatible `\n"
        '  --out "$env:TEMP\\ego_adult_local_benchmark.json"'
    )


def build_ok_result(args: argparse.Namespace, models: list[str], selected_model: str) -> dict[str, Any]:
    lines = powershell_lines(args.base_url, args.api_key, selected_model)
    return {
        "status": "ok",
        "provider": "openai_compatible",
        "base_url": normalize_base_url(args.base_url),
        "models_url": models_url(args.base_url),
        "model_count": len(models),
        "models": models,
        "selected_model": selected_model,
        "powershell_env": lines,
        "benchmark_command": benchmark_command(selected_model, args.base_url, args.api_key),
        "egooperator_command": "python .\\EgoOperator\\agent_base.py",
    }


def print_text_result(result: dict[str, Any]) -> None:
    if result["status"] != "ok":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("Selected local adult-fiction sidecar model:")
    print(f"  {result['selected_model']}")
    print("")
    print("PowerShell session env:")
    for line in result["powershell_env"]:
        print(line)
    print("")
    print("Benchmark:")
    print(result["benchmark_command"])
    print("")
    print("EgoOperator smoke:")
    print(result["egooperator_command"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect and configure a local OpenAI-compatible adult-fiction sidecar model.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--model", default="", help="Explicit loaded model id. If omitted, choose the best loaded Cydonia/Skyfall candidate.")
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--write-powershell", default="", help="Write a dot-sourceable PowerShell env file.")
    args = parser.parse_args()

    try:
        models = fetch_model_ids(args.base_url, args.timeout_seconds)
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        result = {
            "status": "server_unavailable",
            "provider": "openai_compatible",
            "base_url": normalize_base_url(args.base_url),
            "models_url": models_url(args.base_url),
            "error": str(exc),
            "next_action": "Start LM Studio server, load Cydonia IQ4_XS, then rerun this script.",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    selected = choose_model(models, args.model)
    if not selected:
        result = {
            "status": "no_loaded_models",
            "provider": "openai_compatible",
            "base_url": normalize_base_url(args.base_url),
            "models_url": models_url(args.base_url),
            "next_action": "Load bartowski/TheDrummer_Cydonia-24B-v4.1-GGUF IQ4_XS in LM Studio, then rerun this script.",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 3

    result = build_ok_result(args, models, selected)
    if args.write_powershell:
        path = Path(args.write_powershell)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(result["powershell_env"]) + "\n", encoding="utf-8")
        result["wrote_powershell"] = str(path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
