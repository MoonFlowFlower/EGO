import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ego_desktop_tts_worker_fake_self_test(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "ego_desktop_tts_worker.py"),
            "--fake",
            "--self-test",
            "--audio-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["status"] == "ok"
    assert payload["rvc_model"] == "Skadi_CN.pth"
    assert payload["f0method"] == "rmvpe"
    assert payload["ui_audio_delivery_executed"] is True
    assert payload["memory_write"] is False
    assert payload["tool_use"] is False
    assert payload["message_send"] is False
    assert payload["base_tts_network_call"] is False
    assert payload["tts_temp_audio_file_write"] is True
    assert Path(payload["audio_file"]).exists()
