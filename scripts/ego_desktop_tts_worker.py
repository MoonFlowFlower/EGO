"""Persistent EgoDesktop TTS worker.

Reads JSON requests from stdin and writes one JSON result per line to stdout.
The real mode is text -> Edge TTS base audio -> RVC voice conversion. Fake mode
is used by repo tests and never touches model/runtime dependencies.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import wave


DEFAULT_RVC_ROOT = Path(r"D:\Project\AISinging\ruanjian666")
DEFAULT_MODEL_NAME = "Skadi_CN.pth"
DEFAULT_BASE_VOICE = "zh-CN-XiaoxiaoNeural"
DEFAULT_F0_METHOD = "rmvpe"


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def parse_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def safe_request_id(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return text[:80] or f"tts_{int(time.time() * 1000)}"


def wav_duration(path: Path) -> float:
    try:
        with wave.open(str(path), "rb") as handle:
            frames = handle.getnframes()
            rate = handle.getframerate() or 1
            return round(frames / float(rate), 3)
    except (wave.Error, OSError):
        return 0.0


def write_fake_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 16000
    frame_count = int(sample_rate * 0.12)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frame_count)


class DesktopTtsWorker:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.rvc_root = Path(args.rvc_root).resolve()
        self.model_name = str(args.model_name or DEFAULT_MODEL_NAME)
        self.base_voice = str(args.base_voice or DEFAULT_BASE_VOICE)
        self.f0method = str(args.f0method or DEFAULT_F0_METHOD)
        self.f0up_key = int(args.f0up_key)
        self.index_path = str(args.index_path or "")
        self.index_rate = float(args.index_rate)
        self.filter_radius = int(args.filter_radius)
        self.resample_sr = int(args.resample_sr)
        self.rms_mix_rate = float(args.rms_mix_rate)
        self.protect = float(args.protect)
        self.device = str(args.device or "cuda:0")
        self.is_half = parse_bool(args.is_half, True)
        self.fake = bool(args.fake)
        self.edge_tts = None
        self.wavfile = None
        self.vc = None
        self.base_tts_available = False
        self.base_tts_error = ""
        self.rvc_available = False
        self.rvc_error = ""
        self.edge_tts_version = ""

    def ready_payload(self) -> dict:
        return {
            "type": "ready",
            "status": "ok",
            "worker_mode": "fake" if self.fake else "edge_tts_rvc",
            "base_tts_available": self.base_tts_available,
            "base_tts_error": self.base_tts_error,
            "rvc_available": self.rvc_available,
            "rvc_error": self.rvc_error,
            "rvc_root": str(self.rvc_root),
            "rvc_model": self.model_name,
            "base_voice": self.base_voice,
            "f0method": self.f0method,
            "edge_tts_version": self.edge_tts_version,
        }

    def initialize(self) -> None:
        if self.fake:
            self.base_tts_available = True
            self.rvc_available = True
            return
        try:
            self._initialize_edge_tts()
        except Exception as exc:  # pragma: no cover - depends on local runtime.
            self.base_tts_available = False
            self.base_tts_error = f"{exc.__class__.__name__}: {exc}"
            return
        if not self.base_tts_available:
            return
        try:
            self._initialize_rvc()
        except Exception as exc:  # pragma: no cover - depends on local runtime.
            self.rvc_available = False
            self.rvc_error = f"{exc.__class__.__name__}: {exc}"

    def _initialize_edge_tts(self) -> None:
        import edge_tts  # type: ignore

        self.edge_tts = edge_tts
        self.edge_tts_version = str(getattr(edge_tts, "__version__", "unknown"))
        if self.args.skip_base_tts_self_check:
            self.base_tts_available = True
            return
        with tempfile.TemporaryDirectory(prefix="ego_edge_tts_check_") as temp_dir:
            out_path = Path(temp_dir) / "check.mp3"
            asyncio.run(self._edge_tts_to_file("嗯", out_path))
            self.base_tts_available = out_path.exists() and out_path.stat().st_size > 0
            if not self.base_tts_available:
                self.base_tts_error = "edge_tts_self_check_empty_output"

    def _initialize_rvc(self) -> None:
        if not self.rvc_root.exists():
            raise FileNotFoundError(f"RVC root does not exist: {self.rvc_root}")
        model_path = self.rvc_root / "assets" / "weights" / self.model_name
        if not model_path.exists():
            raise FileNotFoundError(f"RVC model does not exist: {model_path}")
        if self.device.startswith("cuda"):
            import torch  # type: ignore

            if not torch.cuda.is_available():
                raise RuntimeError("CUDA is unavailable for requested RVC device")
        old_cwd = Path.cwd()
        old_argv = list(sys.argv)
        try:
            os.chdir(self.rvc_root)
            if str(self.rvc_root) not in sys.path:
                sys.path.insert(0, str(self.rvc_root))
            sys.argv = [sys.argv[0]]
            from dotenv import load_dotenv  # type: ignore
            from scipy.io import wavfile  # type: ignore
            from configs.config import Config  # type: ignore
            from infer.modules.vc.modules import VC  # type: ignore

            load_dotenv(self.rvc_root / ".env")
            config = Config()
            config.device = self.device
            config.is_half = self.is_half
            self.vc = VC(config)
            self.vc.get_vc(self.model_name)
            self.wavfile = wavfile
            self.rvc_available = True
        finally:
            sys.argv = old_argv
            os.chdir(old_cwd)

    async def _edge_tts_to_file(self, text: str, out_path: Path) -> None:
        if self.edge_tts is None:
            raise RuntimeError("edge_tts module is unavailable")
        communicator = self.edge_tts.Communicate(text=text, voice=self.base_voice)
        await communicator.save(str(out_path))

    def synthesize(self, request: dict) -> dict:
        request_id = safe_request_id(request.get("request_id"))
        audio_root = Path(str(request.get("audio_root") or self.args.audio_root)).resolve()
        text = str(request.get("text") or "").strip()
        if not text:
            return self._result(request_id, "empty_text", reason="text is empty")
        if self.fake:
            return self._fake_result(request_id, audio_root)
        if not self.base_tts_available:
            return self._result(request_id, "base_tts_unavailable", reason=self.base_tts_error)
        if not self.rvc_available or self.vc is None or self.wavfile is None:
            return self._result(request_id, "rvc_unavailable", reason=self.rvc_error)
        audio_root.mkdir(parents=True, exist_ok=True)
        base_mp3 = audio_root / f"{request_id}.edge.mp3"
        base_wav = audio_root / f"{request_id}.base.wav"
        out_wav = audio_root / f"{request_id}.skadi.wav"
        try:
            asyncio.run(self._edge_tts_to_file(text, base_mp3))
            self._run_ffmpeg(base_mp3, base_wav)
            old_cwd = Path.cwd()
            try:
                os.chdir(self.rvc_root)
                _info, wav_opt = self.vc.vc_single(
                    0,
                    str(base_wav),
                    int(request.get("f0up_key", self.f0up_key)),
                    None,
                    str(request.get("f0method") or self.f0method),
                    self.index_path,
                    "",
                    self.index_rate,
                    self.filter_radius,
                    self.resample_sr,
                    self.rms_mix_rate,
                    self.protect,
                )
            finally:
                os.chdir(old_cwd)
            sample_rate, audio = wav_opt
            if sample_rate is None or audio is None:
                return self._result(request_id, "rvc_unavailable", reason="RVC returned empty audio")
            self.wavfile.write(str(out_wav), sample_rate, audio)
            return self._ok_result(request_id, out_wav)
        except Exception as exc:  # pragma: no cover - depends on local runtime/network.
            return self._result(request_id, "tts_synthesis_error", reason=f"{exc.__class__.__name__}: {exc}")

    def _run_ffmpeg(self, source: Path, target: Path) -> None:
        ffmpeg = Path(str(self.args.ffmpeg_path or self.rvc_root / "ffmpeg.exe"))
        command = [
            str(ffmpeg),
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(target),
        ]
        subprocess.run(command, cwd=self.rvc_root, check=True)

    def _fake_result(self, request_id: str, audio_root: Path) -> dict:
        out_wav = audio_root / f"{request_id}.skadi.wav"
        write_fake_wav(out_wav)
        return self._ok_result(request_id, out_wav)

    def _ok_result(self, request_id: str, audio_file: Path) -> dict:
        return {
            "type": "result",
            "status": "ok",
            "request_id": request_id,
            "audio_file": str(audio_file),
            "audio_duration_sec": wav_duration(audio_file),
            "voice_profile": "skadi_cn",
            "base_voice": self.base_voice,
            "rvc_model": self.model_name,
            "f0method": self.f0method,
            "side_effects_executed": False,
            "memory_write": False,
            "tool_use": False,
            "message_send": False,
            "file_write": False,
            "network_call": False,
            "base_tts_network_call": not self.fake,
            "tts_temp_audio_file_write": True,
            "ui_audio_delivery_executed": True,
        }

    def _result(self, request_id: str, status: str, reason: str = "") -> dict:
        return {
            "type": "result",
            "status": status,
            "request_id": request_id,
            "reason": reason,
            "voice_profile": "skadi_cn",
            "base_voice": self.base_voice,
            "rvc_model": self.model_name,
            "f0method": self.f0method,
            "side_effects_executed": False,
            "memory_write": False,
            "tool_use": False,
            "message_send": False,
            "file_write": False,
            "network_call": False,
            "base_tts_network_call": False,
            "tts_temp_audio_file_write": False,
            "ui_audio_delivery_executed": False,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rvc-root", default=str(DEFAULT_RVC_ROOT))
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--base-voice", default=DEFAULT_BASE_VOICE)
    parser.add_argument("--f0method", default=DEFAULT_F0_METHOD)
    parser.add_argument("--f0up-key", type=int, default=0)
    parser.add_argument("--index-path", default="")
    parser.add_argument("--index-rate", type=float, default=0.0)
    parser.add_argument("--filter-radius", type=int, default=3)
    parser.add_argument("--resample-sr", type=int, default=0)
    parser.add_argument("--rms-mix-rate", type=float, default=1.0)
    parser.add_argument("--protect", type=float, default=0.33)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--is-half", default="true")
    parser.add_argument("--ffmpeg-path", default="")
    parser.add_argument("--audio-root", default=str(Path(tempfile.gettempdir()) / "ego_desktop_tts_audio"))
    parser.add_argument("--fake", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--skip-base-tts-self-check", action="store_true")
    return parser


def self_test(worker: DesktopTtsWorker) -> int:
    request = {
        "request_id": "self_test",
        "text": "你好呀，我在这里。",
        "audio_root": worker.args.audio_root,
        "f0method": worker.f0method,
        "f0up_key": worker.f0up_key,
    }
    emit(worker.synthesize(request))
    return 0


def main() -> int:
    args = build_parser().parse_args()
    worker = DesktopTtsWorker(args)
    worker.initialize()
    if args.self_test:
        return self_test(worker)
    emit(worker.ready_payload())
    for line in sys.stdin:
        try:
            request = json.loads(line)
            emit(worker.synthesize(request))
        except Exception as exc:  # pragma: no cover - defensive worker loop.
            emit({
                "type": "result",
                "status": "tts_worker_error",
                "request_id": "",
                "reason": f"{exc.__class__.__name__}: {exc}",
                "side_effects_executed": False,
                "memory_write": False,
                "tool_use": False,
                "message_send": False,
                "ui_audio_delivery_executed": False,
            })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
