import pytest
import pytest_asyncio
import os
import importlib
import tempfile
from httpx import AsyncClient, ASGITransport

from emotiond import core
from emotiond.drive_adapter import DriveStateAdapter, get_drive_adapter
from emotiond.drives import reset_drive_manager
from tools.verify_mvp14_mainline_wiring import inspect_wiring


class _EmotionSnapshot:
    energy = 0.2
    uncertainty = 0.6
    social_safety = 0.4


@pytest_asyncio.fixture(scope="function")
async def isolated_db():
    """Provide an isolated db for API mainline wiring verification."""
    from emotiond import config, db, core as core_module

    test_data_dir = tempfile.mkdtemp(prefix="emotiond_mvp14_wiring_")
    original_db_path = os.environ.get("EMOTIOND_DB_PATH")

    os.environ["EMOTIOND_DB_PATH"] = os.path.join(test_data_dir, "test_emotiond.db")

    importlib.reload(config)
    importlib.reload(db)
    importlib.reload(core_module)

    core_module.emotion_state.valence = 0.0
    core_module.emotion_state.arousal = 0.3
    core_module.emotion_state.subjective_time = 0
    core_module.emotion_state.prediction_error = 0.0
    core_module.emotion_state.anger = 0.0
    core_module.emotion_state.sadness = 0.0
    core_module.emotion_state.anxiety = 0.0
    core_module.emotion_state.joy = 0.0
    core_module.emotion_state.loneliness = 0.0
    core_module.emotion_state.regulation_budget = 1.0
    core_module.emotion_state.social_safety = 0.6
    core_module.emotion_state.energy = 0.7
    core_module.relationship_manager.relationships = {}
    core_module.relationship_manager.last_actions = {}

    await db.init_db()

    yield

    if original_db_path:
        os.environ["EMOTIOND_DB_PATH"] = original_db_path
    else:
        os.environ.pop("EMOTIOND_DB_PATH", None)


def test_core_build_drive_state_uses_adapter_to_sync_new_manager(monkeypatch):
    DriveStateAdapter.reset()
    reset_drive_manager()

    adapter = get_drive_adapter(enable_dual_run=True)
    monkeypatch.setattr(core, "_mvp14_adapter", adapter)
    monkeypatch.setattr(core, "ENABLE_MVP14_DUAL_RUN", True)

    drive_state = core.build_drive_state_from_emotion(_EmotionSnapshot())

    assert drive_state.get_component("energy").current == 0.2
    assert drive_state.get_component("uncertainty").current == 0.6
    assert drive_state.get_component("social").current == 0.4
    assert drive_state.get_component("safety").current == 0.4
    assert drive_state.get_component("fatigue").current == 0.8

    new_state = adapter.get_new_state()
    assert new_state is not None
    assert new_state.active_drives["stability"].intensity == pytest.approx(0.2)
    assert new_state.active_drives["coherence"].intensity == pytest.approx(0.6)
    assert new_state.active_drives["completion"].intensity == pytest.approx(0.4)
    assert new_state.active_drives["verification"].intensity == pytest.approx(0.4)
    assert new_state.active_drives["repair"].intensity == pytest.approx(0.8)


def test_mvp14_static_verifier_reports_core_converged_workspace_legacy():
    report = inspect_wiring()

    assert report["core"]["converged"] is True
    assert report["workspace"]["legacy_path_present"] is True
    assert report["status"] == "decision_mainline_converged_workspace_still_legacy"


@pytest.mark.asyncio
async def test_plan_api_mainline_consumes_drive_adapter(monkeypatch, isolated_db):
    from emotiond.api import app

    adapter = get_drive_adapter(enable_dual_run=True)
    call_counts = {
        "build_legacy_state": 0,
        "get_drive_modulation_params_for_components": 0,
    }

    original_build = adapter.build_legacy_state
    original_params = adapter.get_drive_modulation_params_for_components

    def traced_build(*args, **kwargs):
        call_counts["build_legacy_state"] += 1
        return original_build(*args, **kwargs)

    def traced_params(*args, **kwargs):
        call_counts["get_drive_modulation_params_for_components"] += 1
        return original_params(*args, **kwargs)

    monkeypatch.setattr(adapter, "build_legacy_state", traced_build)
    monkeypatch.setattr(adapter, "get_drive_modulation_params_for_components", traced_params)
    monkeypatch.setattr(core, "_mvp14_adapter", adapter)
    monkeypatch.setattr(core, "ENABLE_MVP14_DUAL_RUN", True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/plan",
            json={"user_id": "mvp14_wiring_user", "user_text": "please help me plan"},
        )

    assert response.status_code == 200
    assert call_counts["build_legacy_state"] >= 1
    assert call_counts["get_drive_modulation_params_for_components"] >= 1
