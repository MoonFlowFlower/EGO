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
INVALID_TEXT_MODEL_TOKENS = (
    "embedding",
    "embed-text",
    "text-embedding",
    "nomic-embed",
)

RECOMMENDED_NEXT_MODELS: list[dict[str, Any]] = [
    {
        "rank": 1,
        "candidate": "snowpiercer-15b-q4_k_m",
        "repo": "TheDrummer/Snowpiercer-15B-v4-GGUF",
        "lm_studio_search": "TheDrummer/Snowpiercer-15B-v4-GGUF",
        "quant": "Q4_K_M",
        "approx_size_gb": 9.11,
        "reason": "15B creative-writing model, smaller and likely faster than the current 24B Cydonia route while still above 12B class.",
        "source": "https://huggingface.co/TheDrummer/Snowpiercer-15B-v4-GGUF",
    },
    {
        "rank": 2,
        "candidate": "rocinante-xl-16b-q4_k_s",
        "repo": "bartowski/TheDrummer_Rocinante-XL-16B-v1-GGUF",
        "lm_studio_search": "bartowski/TheDrummer_Rocinante-XL-16B-v1-GGUF",
        "quant": "Q4_K_S",
        "approx_size_gb": 9.43,
        "reason": "16B roleplay/creative route with a smaller Q4_K_S quant for 12GB VRAM experiments.",
        "source": "https://huggingface.co/bartowski/TheDrummer_Rocinante-XL-16B-v1-GGUF",
    },
    {
        "rank": 3,
        "candidate": "anubis-mini-8b-q5_k_m",
        "repo": "TheDrummer/Anubis-Mini-8B-v1-GGUF",
        "lm_studio_search": "TheDrummer/Anubis-Mini-8B-v1-GGUF",
        "quant": "Q5_K_M",
        "approx_size_gb": 5.73,
        "reason": "Fast 8B fallback candidate for isolating whether Cydonia failures are speed/capacity related.",
        "source": "https://huggingface.co/TheDrummer/Anubis-Mini-8B-v1-GGUF",
    },
    {
        "rank": 4,
        "candidate": "unslopnemo-12b-q4_k_m",
        "repo": "TheDrummer/UnslopNemo-12B-v4.1-GGUF",
        "lm_studio_search": "TheDrummer/UnslopNemo-12B-v4.1-GGUF",
        "quant": "Q4_K_M",
        "approx_size_gb": 7.48,
        "reason": "Light 12B creative/roleplay comparison route; useful if 15B/16B still strains the machine.",
        "source": "https://huggingface.co/TheDrummer/UnslopNemo-12B-v4.1-GGUF/tree/main",
    },
]


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


def is_text_generation_model_id(model_id: str) -> bool:
    value = (model_id or "").lower()
    return bool(value.strip()) and not any(token in value for token in INVALID_TEXT_MODEL_TOKENS)


def text_generation_model_ids(model_ids: list[str]) -> list[str]:
    return [model_id for model_id in model_ids if is_text_generation_model_id(model_id)]


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


def model_matches_exclusion(model_id: str, exclusions: tuple[str, ...] = ()) -> bool:
    value = (model_id or "").lower()
    return any(item and item.lower() in value for item in exclusions)


def recommended_model_matches_exclusion(item: dict[str, Any], exclusions: tuple[str, ...] = ()) -> bool:
    haystack = " ".join(
        str(item.get(key) or "")
        for key in ("candidate", "repo", "lm_studio_search", "source")
    ).lower()
    return any(exclusion and exclusion.lower() in haystack for exclusion in exclusions)


def recommended_next_models(exclusions: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    filtered = [
        item
        for item in RECOMMENDED_NEXT_MODELS
        if not recommended_model_matches_exclusion(item, exclusions)
    ]
    result: list[dict[str, Any]] = []
    for index, item in enumerate(filtered, start=1):
        updated = dict(item)
        updated["rank"] = index
        result.append(updated)
    return result


def candidate_text_generation_model_ids(model_ids: list[str], exclusions: tuple[str, ...] = ()) -> list[str]:
    return [model_id for model_id in text_generation_model_ids(model_ids) if not model_matches_exclusion(model_id, exclusions)]


def choose_model(model_ids: list[str], explicit_model: str = "", exclusions: tuple[str, ...] = ()) -> str | None:
    if explicit_model:
        return explicit_model
    text_models = candidate_text_generation_model_ids(model_ids, exclusions)
    if not text_models:
        return None
    return max(text_models, key=model_score)


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


def strict_suite_command(model: str, base_url: str, api_key: str) -> str:
    env_lines = powershell_lines(base_url, api_key, model)
    env_lines.extend([
        "$env:ADULT_FICTION_EXPRESSIVENESS='explicit'",
        "$env:ADULT_FICTION_PROMPT_PROFILE='immersive_roleplay'",
        "$env:ADULT_FICTION_TIMEOUT_SECONDS='180'",
        "$env:ADULT_FICTION_MAX_TOKENS='120'",
        "$env:ADULT_FICTION_CONTEXT_TURNS='3'",
        "$env:ADULT_FICTION_MESSAGE_CHAR_LIMIT='420'",
        "python .\\scripts\\run_ego_experience_trial.py `",
        "  --adult-fiction-acceptance-suite `",
        '  --scenario-file "$env:TEMP\\ego_adult_fiction_private_scenario.json" `',
        "  --repeat-runs 3 `",
        "  --suite-timeout-seconds 1800 `",
        '  --out "$env:TEMP\\ego_adult_fiction_acceptance_candidate"',
    ])
    return "\n".join(env_lines)


def build_ok_result(args: argparse.Namespace, models: list[str], selected_model: str) -> dict[str, Any]:
    lines = powershell_lines(args.base_url, args.api_key, selected_model)
    text_models = text_generation_model_ids(models)
    exclusions = tuple(args.exclude_model or ())
    candidate_models = candidate_text_generation_model_ids(models, exclusions)
    return {
        "status": "ok",
        "provider": "openai_compatible",
        "base_url": normalize_base_url(args.base_url),
        "models_url": models_url(args.base_url),
        "model_count": len(models),
        "models": models,
        "text_generation_model_count": len(text_models),
        "text_generation_models": text_models,
        "ignored_non_text_models": [model for model in models if model not in text_models],
        "excluded_text_generation_models": [model for model in text_models if model not in candidate_models],
        "candidate_text_generation_model_count": len(candidate_models),
        "candidate_text_generation_models": candidate_models,
        "selected_model": selected_model,
        "needs_second_text_generation_candidate": len(text_models) < 2,
        "recommended_next_models": recommended_next_models(exclusions) if len(text_models) < 2 else [],
        "powershell_env": lines,
        "benchmark_command": benchmark_command(selected_model, args.base_url, args.api_key),
        "strict_suite_command": strict_suite_command(selected_model, args.base_url, args.api_key),
        "egooperator_command": "python .\\EgoOperator\\agent_base.py",
    }


def print_text_result(result: dict[str, Any]) -> None:
    if result["status"] != "ok":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("Selected local adult-fiction sidecar model:")
    print(f"  {result['selected_model']}")
    if result.get("ignored_non_text_models"):
        print("")
        print("Ignored non-text-generation models:")
        for model in result["ignored_non_text_models"]:
            print(f"  {model}")
    if result.get("excluded_text_generation_models"):
        print("")
        print("Excluded baseline text-generation models:")
        for model in result["excluded_text_generation_models"]:
            print(f"  {model}")
    if result.get("needs_second_text_generation_candidate"):
        print("")
        print("Recommended next text-generation candidates to load for #80 strict comparison:")
        for item in result["recommended_next_models"]:
            print(f"  {item['rank']}. {item['repo']} {item['quant']} (~{item['approx_size_gb']} GB)")
    print("")
    print("PowerShell session env:")
    for line in result["powershell_env"]:
        print(line)
    print("")
    print("Benchmark:")
    print(result["benchmark_command"])
    print("")
    print("Strict #80 candidate suite:")
    print(result["strict_suite_command"])
    print("")
    print("EgoOperator smoke:")
    print(result["egooperator_command"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect and configure a local OpenAI-compatible adult-fiction sidecar model.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--model", default="", help="Explicit loaded model id. If omitted, choose the best loaded Cydonia/Skyfall candidate.")
    parser.add_argument(
        "--exclude-model",
        action="append",
        default=[],
        help="Case-insensitive substring to exclude from automatic model selection, e.g. --exclude-model cydonia when comparing a newly loaded model.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--write-powershell", default="", help="Write a dot-sourceable PowerShell env file.")
    args = parser.parse_args(argv)

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

    selected = choose_model(models, args.model, tuple(args.exclude_model or ()))
    if not selected:
        text_models = text_generation_model_ids(models)
        exclusions = tuple(args.exclude_model or ())
        status = "no_candidate_text_generation_models" if exclusions and text_models else "no_text_generation_models"
        next_action = (
            "Load a non-excluded text-generation GGUF model in LM Studio, then rerun this script with the same --exclude-model option."
            if exclusions and text_models
            else "Load a text-generation GGUF model in LM Studio, then rerun this script."
        )
        result = {
            "status": status,
            "provider": "openai_compatible",
            "base_url": normalize_base_url(args.base_url),
            "models_url": models_url(args.base_url),
            "model_count": len(models),
            "models": models,
            "text_generation_model_count": len(text_models),
            "text_generation_models": text_models,
            "ignored_non_text_models": [model for model in models if model not in text_models],
            "excluded_text_generation_models": [
                model for model in text_models if model_matches_exclusion(model, exclusions)
            ],
            "recommended_next_models": recommended_next_models(exclusions),
            "next_action": next_action,
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
