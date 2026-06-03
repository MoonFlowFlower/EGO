import json

import scripts.configure_adult_fiction_sidecar as sidecar


def test_choose_model_prefers_cydonia_iq4_xs():
    models = [
        "bartowski/TheDrummer_Skyfall-36B-v2-GGUF/TheDrummer_Skyfall-36B-v2-Q4_K_M.gguf",
        "bartowski/TheDrummer_Cydonia-24B-v4.1-GGUF/TheDrummer_Cydonia-24B-v4.1-Q4_K_M.gguf",
        "bartowski/TheDrummer_Cydonia-24B-v4.1-GGUF/TheDrummer_Cydonia-24B-v4.1-IQ4_XS.gguf",
    ]

    assert sidecar.choose_model(models) == models[2]


def test_choose_model_uses_explicit_model():
    assert sidecar.choose_model(["loaded-a"], "manual-model-id") == "manual-model-id"


def test_choose_model_ignores_embedding_models():
    models = [
        "text-embedding-nomic-embed-text-v1.5",
        "thedrummer_cydonia-24b-v4.1",
    ]

    assert sidecar.choose_model(models) == "thedrummer_cydonia-24b-v4.1"


def test_choose_model_returns_none_when_only_embedding_loaded():
    assert sidecar.choose_model(["text-embedding-nomic-embed-text-v1.5"]) is None


def test_choose_model_can_exclude_cydonia_for_second_candidate():
    models = [
        "thedrummer_cydonia-24b-v4.1",
        "TheDrummer/Snowpiercer-15B-v4-GGUF:Q4_K_M",
    ]

    assert sidecar.choose_model(models, exclusions=("cydonia",)) == models[1]


def test_choose_model_returns_none_when_all_text_models_excluded():
    assert sidecar.choose_model(["thedrummer_cydonia-24b-v4.1"], exclusions=("cydonia",)) is None


def test_recommended_next_models_filters_excluded_candidates():
    result = sidecar.recommended_next_models(("snowpiercer",))

    assert result[0]["candidate"] == "rocinante-xl-16b-q4_k_s"
    assert result[0]["rank"] == 1
    assert all("snowpiercer" not in item["candidate"] for item in result)


def test_normalize_base_url_accepts_chat_completions_url():
    assert (
        sidecar.normalize_base_url("http://localhost:1234/v1/chat/completions")
        == "http://localhost:1234/v1"
    )


def test_powershell_env_contains_openai_compatible_sidecar():
    lines = sidecar.powershell_lines("http://localhost:1234/v1", "lm-studio", "cydonia-iq4")
    text = "\n".join(lines)

    assert "ADULT_FICTION_PROVIDER='openai_compatible'" in text
    assert "ADULT_FICTION_BASE_URL='http://localhost:1234/v1'" in text
    assert "ADULT_FICTION_API_KEY='lm-studio'" in text
    assert "ADULT_FICTION_MODEL='cydonia-iq4'" in text


def test_build_ok_result_is_json_serializable():
    class Args:
        base_url = "http://localhost:1234/v1"
        api_key = "lm-studio"
        exclude_model = ["cydonia"]

    result = sidecar.build_ok_result(
        Args(),
        ["cydonia-iq4", "snowpiercer-q4", "text-embedding-nomic-embed-text-v1.5"],
        "snowpiercer-q4",
    )

    assert result["status"] == "ok"
    assert result["selected_model"] == "snowpiercer-q4"
    assert result["text_generation_model_count"] == 2
    assert result["candidate_text_generation_models"] == ["snowpiercer-q4"]
    assert result["excluded_text_generation_models"] == ["cydonia-iq4"]
    assert result["ignored_non_text_models"] == ["text-embedding-nomic-embed-text-v1.5"]
    assert result["needs_second_text_generation_candidate"] is False
    assert "--runtime-compatible" in result["benchmark_command"]
    assert "--adult-fiction-acceptance-suite" in result["strict_suite_command"]
    assert "ADULT_FICTION_MODEL='snowpiercer-q4'" in result["strict_suite_command"]
    json.dumps(result)


def test_build_ok_result_filters_recommendations_when_second_candidate_needed():
    class Args:
        base_url = "http://localhost:1234/v1"
        api_key = "lm-studio"
        exclude_model = ["cydonia", "snowpiercer"]

    result = sidecar.build_ok_result(
        Args(),
        ["cydonia-iq4"],
        "manual-model",
    )

    assert result["needs_second_text_generation_candidate"] is True
    assert result["recommended_next_models"][0]["candidate"] == "rocinante-xl-16b-q4_k_s"


def test_exclude_model_no_candidate_status_shape():
    models = ["thedrummer_cydonia-24b-v4.1", "text-embedding-nomic-embed-text-v1.5"]
    text_models = sidecar.text_generation_model_ids(models)
    exclusions = ("cydonia",)
    result = {
        "status": "no_candidate_text_generation_models" if exclusions and text_models else "no_text_generation_models",
        "excluded_text_generation_models": [
            model for model in text_models if sidecar.model_matches_exclusion(model, exclusions)
        ],
    }

    assert result["status"] == "no_candidate_text_generation_models"
    assert result["excluded_text_generation_models"] == ["thedrummer_cydonia-24b-v4.1"]


def test_no_candidate_next_action_mentions_non_excluded_model(monkeypatch, capsys):
    monkeypatch.setattr(
        sidecar,
        "fetch_model_ids",
        lambda base_url, timeout: ["cydonia-iq4", "snowpiercer-q4"],
    )

    exit_code = sidecar.main([
        "--exclude-model",
        "cydonia",
        "--exclude-model",
        "snowpiercer",
        "--json",
    ])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 3
    assert "non-excluded text-generation" in payload["next_action"]
    assert payload["recommended_next_models"][0]["candidate"] == "rocinante-xl-16b-q4_k_s"
