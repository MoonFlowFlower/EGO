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

    result = sidecar.build_ok_result(Args(), ["cydonia-iq4"], "cydonia-iq4")

    assert result["status"] == "ok"
    assert result["selected_model"] == "cydonia-iq4"
    assert "--runtime-compatible" in result["benchmark_command"]
    json.dumps(result)
