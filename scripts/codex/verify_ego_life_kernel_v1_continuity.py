"""Callable, fail-closed evidence producer for the local V1 continuity playground.

This verifier deliberately keeps product acceptance separate from mechanism
claims.  It drives the product path when Tk is available, independently
recomputes a cheap cue/clock shortcut baseline, reruns real interventions, and
uses disposable database copies for tamper controls.  A missing observable
effect is retained as a blocking negative result rather than patched into a
pass-shaped report.
"""

from __future__ import annotations

import ast
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import ctypes
from ctypes import wintypes
import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import sqlite3
import secrets
import struct
import sys
import tempfile
import time
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labs.ego_life_playground_v0 import engine
from labs.ego_life_playground_v0.app import PlaygroundController, PlaygroundWindow
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore


PRODUCT_PATHS = (
    "labs/ego_life_playground_v0/__init__.py",
    "labs/ego_life_playground_v0/engine.py",
    "labs/ego_life_playground_v0/store.py",
    "labs/ego_life_playground_v0/app.py",
    "scripts/run_ego_life_playground_v0.py",
    "tests/test_ego_life_playground_v0.py",
)
ARTIFACT_NAMES = (
    "continuity.sqlite3",
    "trace.jsonl",
    "product_trigger_receipt.json",
    "baseline_comparison.json",
    "ablation_report.json",
    "replay_report.json",
    "leakage_report.json",
    "failure_manifest.json",
    "claim_ceiling.txt",
    "result.json",
)
CLAIM_CEILING = (
    "Local V1 continuity-playground engineering, product-trigger, and trace/replay "
    "evidence only; shortcut-baseline plausibility remains. This does not prove "
    "learning, mechanism validity, agency, autonomy, subjectivity, consciousness, "
    "real emotion, or electronic life."
)

_PIPE_FRAME_LIMIT = 1024 * 1024
_PIPE_TIMEOUT_MS = 30000
_PROBE_EXIT_TIMEOUT_MS = 5000
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
_ERROR_PIPE_CONNECTED = 535
_ERROR_IO_PENDING = 997
_ERROR_OPERATION_ABORTED = 995
_ERROR_INSUFFICIENT_BUFFER = 122
_WAIT_OBJECT_0 = 0
_WAIT_TIMEOUT = 258
_STILL_ACTIVE = 259
_PIPE_ACCESS_DUPLEX = 0x00000003
_FILE_FLAG_FIRST_PIPE_INSTANCE = 0x00080000
_FILE_FLAG_OVERLAPPED = 0x40000000
_PIPE_REJECT_REMOTE_CLIENTS = 0x00000008
_TOKEN_QUERY = 0x0008
_TOKEN_USER_INFORMATION_CLASS = 1
_SDDL_REVISION_1 = 1
_PROCESS_QUERY_INFORMATION = 0x0400
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_PROCESS_SYNCHRONIZE = 0x00100000


class _Overlapped(ctypes.Structure):
    _fields_ = [
        ("Internal", ctypes.c_size_t),
        ("InternalHigh", ctypes.c_size_t),
        ("Offset", wintypes.DWORD),
        ("OffsetHigh", wintypes.DWORD),
        ("hEvent", wintypes.HANDLE),
    ]


class _SecurityAttributes(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", wintypes.LPVOID),
        ("bInheritHandle", wintypes.BOOL),
    ]


class _SidAndAttributes(ctypes.Structure):
    _fields_ = [
        ("Sid", wintypes.LPVOID),
        ("Attributes", wintypes.DWORD),
    ]


class _TokenUser(ctypes.Structure):
    _fields_ = [("User", _SidAndAttributes)]


def _kernel32() -> Any:
    library = ctypes.WinDLL("kernel32", use_last_error=True)
    library.CreateNamedPipeW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
    ]
    library.CreateNamedPipeW.restype = wintypes.HANDLE
    library.GetCurrentProcess.argtypes = []
    library.GetCurrentProcess.restype = wintypes.HANDLE
    library.ConnectNamedPipe.argtypes = [wintypes.HANDLE, wintypes.LPVOID]
    library.ConnectNamedPipe.restype = wintypes.BOOL
    library.CreateEventW.argtypes = [
        wintypes.LPVOID,
        wintypes.BOOL,
        wintypes.BOOL,
        wintypes.LPCWSTR,
    ]
    library.CreateEventW.restype = wintypes.HANDLE
    library.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    library.WaitForSingleObject.restype = wintypes.DWORD
    library.GetOverlappedResult.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_Overlapped),
        ctypes.POINTER(wintypes.DWORD),
        wintypes.BOOL,
    ]
    library.GetOverlappedResult.restype = wintypes.BOOL
    library.CancelIoEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Overlapped)]
    library.CancelIoEx.restype = wintypes.BOOL
    library.WaitNamedPipeW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
    library.WaitNamedPipeW.restype = wintypes.BOOL
    library.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    library.CreateFileW.restype = wintypes.HANDLE
    library.ReadFile.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    library.ReadFile.restype = wintypes.BOOL
    library.WriteFile.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    library.WriteFile.restype = wintypes.BOOL
    library.GetNamedPipeServerProcessId.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.ULONG),
    ]
    library.GetNamedPipeServerProcessId.restype = wintypes.BOOL
    library.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    library.OpenProcess.restype = wintypes.HANDLE
    library.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    library.QueryFullProcessImageNameW.restype = wintypes.BOOL
    library.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    library.GetExitCodeProcess.restype = wintypes.BOOL
    library.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    library.FlushFileBuffers.restype = wintypes.BOOL
    library.DisconnectNamedPipe.argtypes = [wintypes.HANDLE]
    library.DisconnectNamedPipe.restype = wintypes.BOOL
    library.CloseHandle.argtypes = [wintypes.HANDLE]
    library.CloseHandle.restype = wintypes.BOOL
    library.LocalFree.argtypes = [wintypes.HANDLE]
    library.LocalFree.restype = wintypes.HANDLE
    return library


def _advapi32() -> Any:
    library = ctypes.WinDLL("advapi32", use_last_error=True)
    library.OpenProcessToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    library.OpenProcessToken.restype = wintypes.BOOL
    library.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    library.GetTokenInformation.restype = wintypes.BOOL
    library.ConvertSidToStringSidW.argtypes = [
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.LPWSTR),
    ]
    library.ConvertSidToStringSidW.restype = wintypes.BOOL
    library.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.DWORD),
    ]
    library.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
    return library


def _raise_last_winerror(label: str) -> None:
    error = ctypes.get_last_error()
    raise OSError(error, f"{label}: {ctypes.FormatError(error)}")


@contextmanager
def _overlapped_operation() -> Iterable[_Overlapped]:
    library = _kernel32()
    event = library.CreateEventW(None, True, False, None)
    if not event:
        _raise_last_winerror("CreateEventW(named pipe)")
    operation = _Overlapped()
    operation.hEvent = event
    try:
        yield operation
    finally:
        library.CloseHandle(event)


def _remaining_timeout_ms(deadline: float) -> int:
    remaining = int((deadline - time.monotonic()) * 1000)
    if remaining <= 0:
        raise TimeoutError("named-pipe protocol deadline expired")
    return remaining


def _wait_overlapped(
    handle: Any,
    operation: _Overlapped,
    timeout_ms: int,
    label: str,
) -> int:
    library = _kernel32()
    wait_result = int(library.WaitForSingleObject(operation.hEvent, timeout_ms))
    if wait_result == _WAIT_TIMEOUT:
        library.CancelIoEx(handle, ctypes.byref(operation))
        # An OVERLAPPED and its buffer must remain alive until cancellation is
        # observed. GetOverlappedResult(TRUE) is the Windows completion barrier.
        transferred = wintypes.DWORD()
        library.GetOverlappedResult(
            handle, ctypes.byref(operation), ctypes.byref(transferred), True
        )
        raise TimeoutError(f"{label} exceeded {timeout_ms} ms protocol bound")
    if wait_result != _WAIT_OBJECT_0:
        _raise_last_winerror(f"WaitForSingleObject({label})")
    transferred = wintypes.DWORD()
    if not library.GetOverlappedResult(
        handle, ctypes.byref(operation), ctypes.byref(transferred), False
    ):
        error = ctypes.get_last_error()
        if error == _ERROR_OPERATION_ABORTED:
            raise TimeoutError(f"{label} was cancelled")
        raise OSError(error, f"GetOverlappedResult({label}): {ctypes.FormatError(error)}")
    return int(transferred.value)


def _overlapped_write(handle: Any, payload: bytes, timeout_ms: int) -> int:
    library = _kernel32()
    buffer = ctypes.create_string_buffer(payload)
    with _overlapped_operation() as operation:
        succeeded = library.WriteFile(
            handle, buffer, len(payload), None, ctypes.byref(operation)
        )
        if not succeeded:
            error = ctypes.get_last_error()
            if error != _ERROR_IO_PENDING:
                raise OSError(error, f"WriteFile(named pipe): {ctypes.FormatError(error)}")
        return _wait_overlapped(handle, operation, timeout_ms, "WriteFile(named pipe)")


def _overlapped_read(handle: Any, size: int, timeout_ms: int) -> bytes:
    library = _kernel32()
    buffer = ctypes.create_string_buffer(size)
    with _overlapped_operation() as operation:
        succeeded = library.ReadFile(
            handle, buffer, size, None, ctypes.byref(operation)
        )
        if not succeeded:
            error = ctypes.get_last_error()
            if error != _ERROR_IO_PENDING:
                raise OSError(error, f"ReadFile(named pipe): {ctypes.FormatError(error)}")
        transferred = _wait_overlapped(
            handle, operation, timeout_ms, "ReadFile(named pipe)"
        )
        return buffer.raw[:transferred]


def _pipe_write_frame(
    handle: Any,
    value: Mapping[str, Any],
    timeout_ms: int = _PIPE_TIMEOUT_MS,
) -> None:
    payload = _json(value).encode("utf-8")
    if len(payload) > _PIPE_FRAME_LIMIT:
        raise ValueError("named-pipe frame exceeds canonical JSON length limit")
    framed = struct.pack("<I", len(payload)) + payload
    deadline = time.monotonic() + (timeout_ms / 1000)
    offset = 0
    while offset < len(framed):
        chunk = framed[offset : offset + 65536]
        written = _overlapped_write(
            handle, chunk, _remaining_timeout_ms(deadline)
        )
        if written <= 0:
            raise OSError("WriteFile(named pipe) made no progress")
        offset += written


def _pipe_read_exact(handle: Any, count: int, deadline: float) -> bytes:
    chunks: list[bytes] = []
    remaining = count
    while remaining:
        size = min(remaining, 65536)
        chunk = _overlapped_read(handle, size, _remaining_timeout_ms(deadline))
        if not chunk:
            raise EOFError("named pipe closed before complete frame")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _pipe_read_frame(
    handle: Any,
    timeout_ms: int = _PIPE_TIMEOUT_MS,
) -> dict[str, Any]:
    deadline = time.monotonic() + (timeout_ms / 1000)
    (length,) = struct.unpack("<I", _pipe_read_exact(handle, 4, deadline))
    if length > _PIPE_FRAME_LIMIT:
        raise ValueError("named-pipe frame length exceeds limit")
    value = json.loads(_pipe_read_exact(handle, length, deadline).decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("named-pipe frame must be a JSON object")
    return value


def _current_process_user_sid() -> str:
    """Read the current operator SID from this process token or fail closed."""

    kernel = _kernel32()
    security = _advapi32()
    token = wintypes.HANDLE()
    sid_text = wintypes.LPWSTR()
    if not security.OpenProcessToken(
        kernel.GetCurrentProcess(), _TOKEN_QUERY, ctypes.byref(token)
    ):
        _raise_last_winerror("OpenProcessToken(current operator)")
    try:
        required = wintypes.DWORD()
        if security.GetTokenInformation(
            token,
            _TOKEN_USER_INFORMATION_CLASS,
            None,
            0,
            ctypes.byref(required),
        ):
            raise RuntimeError("GetTokenInformation unexpectedly accepted an empty buffer")
        error = ctypes.get_last_error()
        if error != _ERROR_INSUFFICIENT_BUFFER or required.value <= 0:
            raise OSError(
                error,
                "GetTokenInformation(TokenUser) size query failed: "
                + ctypes.FormatError(error),
            )
        buffer = ctypes.create_string_buffer(required.value)
        if not security.GetTokenInformation(
            token,
            _TOKEN_USER_INFORMATION_CLASS,
            buffer,
            required.value,
            ctypes.byref(required),
        ):
            _raise_last_winerror("GetTokenInformation(TokenUser)")
        token_user = _TokenUser.from_buffer(buffer)
        if not token_user.User.Sid:
            raise RuntimeError("TokenUser returned a null operator SID")
        if not security.ConvertSidToStringSidW(
            token_user.User.Sid, ctypes.byref(sid_text)
        ):
            _raise_last_winerror("ConvertSidToStringSidW(current operator)")
        value = sid_text.value
        if not value:
            raise RuntimeError("ConvertSidToStringSidW returned an empty SID")
        return value
    finally:
        if sid_text:
            kernel.LocalFree(sid_text)
        if token:
            kernel.CloseHandle(token)


def _operator_only_pipe_sddl(operator_sid: str) -> str:
    parts = operator_sid.split("-")
    if len(parts) < 3 or parts[0] != "S" or any(
        not part.isdecimal() for part in parts[1:]
    ):
        raise ValueError("operator SID is not a canonical SID string")
    # Protected DACL with exactly one allow ACE: current operator, generic-all.
    return f"D:P(A;;GA;;;{operator_sid})"


@contextmanager
def _operator_pipe_security_attributes(
    expected_operator_sid: str,
) -> Iterable[Any]:
    current_operator_sid = _current_process_user_sid()
    if expected_operator_sid != current_operator_sid:
        raise PermissionError(
            "named-pipe operator SID differs from the current process token"
        )
    sddl = _operator_only_pipe_sddl(current_operator_sid)
    descriptor = wintypes.LPVOID()
    descriptor_size = wintypes.DWORD()
    if not _advapi32().ConvertStringSecurityDescriptorToSecurityDescriptorW(
        sddl,
        _SDDL_REVISION_1,
        ctypes.byref(descriptor),
        ctypes.byref(descriptor_size),
    ):
        _raise_last_winerror(
            "ConvertStringSecurityDescriptorToSecurityDescriptorW(named pipe)"
        )
    if not descriptor or descriptor_size.value <= 0:
        if descriptor:
            _kernel32().LocalFree(descriptor)
        raise RuntimeError("named-pipe security descriptor was empty")
    security_attributes = _SecurityAttributes(
        nLength=ctypes.sizeof(_SecurityAttributes),
        lpSecurityDescriptor=descriptor,
        bInheritHandle=False,
    )
    try:
        yield ctypes.byref(security_attributes)
    finally:
        _kernel32().LocalFree(descriptor)


def _create_named_pipe_server(pipe_name: str, operator_sid: str) -> Any:
    library = _kernel32()
    with _operator_pipe_security_attributes(operator_sid) as security_attributes:
        handle = library.CreateNamedPipeW(
            pipe_name,
            # PIPE_ACCESS_DUPLEX | FILE_FLAG_FIRST_PIPE_INSTANCE | FILE_FLAG_OVERLAPPED
            _PIPE_ACCESS_DUPLEX
            | _FILE_FLAG_FIRST_PIPE_INSTANCE
            | _FILE_FLAG_OVERLAPPED,
            _PIPE_REJECT_REMOTE_CLIENTS,
            1,
            _PIPE_FRAME_LIMIT,
            _PIPE_FRAME_LIMIT,
            _PIPE_TIMEOUT_MS,
            security_attributes,
        )
    if handle == _INVALID_HANDLE_VALUE:
        _raise_last_winerror("CreateNamedPipeW")
    return handle


def _connect_named_pipe_server(
    handle: Any,
    timeout_ms: int = _PIPE_TIMEOUT_MS,
) -> None:
    library = _kernel32()
    with _overlapped_operation() as operation:
        if library.ConnectNamedPipe(handle, ctypes.byref(operation)):
            return
        error = ctypes.get_last_error()
        if error == _ERROR_PIPE_CONNECTED:
            return
        if error != _ERROR_IO_PENDING:
            raise OSError(error, f"ConnectNamedPipe: {ctypes.FormatError(error)}")
        _wait_overlapped(handle, operation, timeout_ms, "ConnectNamedPipe")


def _open_named_pipe_client(pipe_name: str) -> Any:
    library = _kernel32()
    if not library.WaitNamedPipeW(pipe_name, _PIPE_TIMEOUT_MS):
        _raise_last_winerror("WaitNamedPipeW")
    handle = library.CreateFileW(
        pipe_name,
        0x80000000 | 0x40000000,
        0,
        None,
        3,
        0x40000000,  # FILE_FLAG_OVERLAPPED
        None,
    )
    if handle == _INVALID_HANDLE_VALUE:
        _raise_last_winerror("CreateFileW(named pipe)")
    return handle


def _query_process_image(process_handle: Any) -> str:
    library = _kernel32()
    size = wintypes.DWORD(32768)
    buffer = ctypes.create_unicode_buffer(size.value)
    if not library.QueryFullProcessImageNameW(
        process_handle, 0, buffer, ctypes.byref(size)
    ):
        _raise_last_winerror("QueryFullProcessImageNameW")
    value = buffer.value[: size.value]
    if not value or not Path(value).is_absolute():
        raise RuntimeError("process image path is not a complete absolute path")
    return str(Path(value).resolve())


def _query_process_commandline(process_handle: Any) -> str:
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    ntdll.NtQueryInformationProcess.argtypes = [
        wintypes.HANDLE,
        wintypes.ULONG,
        wintypes.LPVOID,
        wintypes.ULONG,
        ctypes.POINTER(wintypes.ULONG),
    ]
    ntdll.NtQueryInformationProcess.restype = ctypes.c_long
    needed = wintypes.ULONG()
    ntdll.NtQueryInformationProcess(
        process_handle, 60, None, 0, ctypes.byref(needed)
    )
    if needed.value < ctypes.sizeof(ctypes.c_void_p) + 4 or needed.value > _PIPE_FRAME_LIMIT:
        raise RuntimeError("NtQueryInformationProcess returned invalid command-line length")
    buffer = ctypes.create_string_buffer(needed.value)
    status = ntdll.NtQueryInformationProcess(
        process_handle, 60, buffer, needed.value, ctypes.byref(needed)
    )
    if status != 0:
        raise OSError(f"NtQueryInformationProcess(ProcessCommandLineInformation) status={status:#x}")

    class UnicodeString(ctypes.Structure):
        _fields_ = [
            ("Length", ctypes.c_ushort),
            ("MaximumLength", ctypes.c_ushort),
            ("Buffer", ctypes.c_void_p),
        ]

    value = UnicodeString.from_buffer(buffer)
    if not value.Buffer or value.Length <= 0 or value.Length > value.MaximumLength:
        raise RuntimeError("native process command line returned invalid UNICODE_STRING")
    return ctypes.wstring_at(value.Buffer, value.Length // ctypes.sizeof(ctypes.c_wchar))


def _split_windows_commandline(commandline: str) -> list[str]:
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    shell32.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    argc = ctypes.c_int()
    argv = shell32.CommandLineToArgvW(commandline, ctypes.byref(argc))
    if not argv:
        _raise_last_winerror("CommandLineToArgvW")
    try:
        return [argv[index] for index in range(argc.value)]
    finally:
        _kernel32().LocalFree(argv)


def _process_is_active(process_handle: Any) -> bool:
    code = wintypes.DWORD()
    if not _kernel32().GetExitCodeProcess(process_handle, ctypes.byref(code)):
        _raise_last_winerror("GetExitCodeProcess")
    return int(code.value) == _STILL_ACTIVE


def _wait_for_process_exit(
    process_handle: Any,
    timeout_ms: int = _PROBE_EXIT_TIMEOUT_MS,
) -> dict[str, Any]:
    """Observe termination and its exit code using the already-attested handle."""

    library = _kernel32()
    wait_result = int(library.WaitForSingleObject(process_handle, timeout_ms))
    if wait_result not in {_WAIT_OBJECT_0, _WAIT_TIMEOUT}:
        _raise_last_winerror("WaitForSingleObject(probe after ACK)")
    exit_code = wintypes.DWORD()
    if not library.GetExitCodeProcess(process_handle, ctypes.byref(exit_code)):
        _raise_last_winerror("GetExitCodeProcess(probe after ACK)")
    observed = wait_result == _WAIT_OBJECT_0 and int(exit_code.value) != _STILL_ACTIVE
    return {
        "probe_exit_observed": observed,
        "probe_exit_code": int(exit_code.value),
        "no_orphan": observed,
        "wait_result": wait_result,
        "timeout_ms": timeout_ms,
    }


def _json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _hash(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_ref(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "json_pointer": None,
        "content_mode": "raw_file",
        "sha256": _sha256_path(path),
        "byte_count": path.stat().st_size,
    }


class _EvidenceInputScope:
    def __init__(self, artifact_path: str | Path) -> None:
        self.artifact_path = Path(artifact_path).resolve()
        self.evidence_inputs: dict[str, Any] = {}

    def add(self, label: str, value: Any) -> dict[str, Any]:
        payload_hash = _hash(value)
        normalized = "".join(
            character if character.isalnum() else "_" for character in label
        ).strip("_") or "input"
        identifier = f"{normalized}_{payload_hash[:16]}"
        existing = self.evidence_inputs.get(identifier)
        if existing is not None and _json(existing) != _json(value):
            raise RuntimeError(f"evidence input identifier collision: {identifier}")
        self.evidence_inputs[identifier] = deepcopy(value)
        payload = _json(value).encode("utf-8")
        escaped = identifier.replace("~", "~0").replace("/", "~1")
        return {
            "path": str(self.artifact_path),
            "json_pointer": f"/evidence_inputs/{escaped}",
            "content_mode": "canonical_json_pointer",
            "input_id": identifier,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "byte_count": len(payload),
        }


_ACTIVE_EVIDENCE_SCOPE: ContextVar[_EvidenceInputScope | None] = ContextVar(
    "ego_v1_evidence_input_scope", default=None
)


@contextmanager
def evidence_input_scope(artifact_path: str | Path):
    scope = _EvidenceInputScope(artifact_path)
    token = _ACTIVE_EVIDENCE_SCOPE.set(scope)
    try:
        yield scope
    finally:
        _ACTIVE_EVIDENCE_SCOPE.reset(token)


def _semantic_ref(path: str, value: Any) -> dict[str, Any]:
    scope = _ACTIVE_EVIDENCE_SCOPE.get()
    if scope is None:
        raise RuntimeError("evidence-bearing report built outside evidence_input_scope")
    return scope.add(path, value)


def _attach_scope_inputs(report: dict[str, Any], scope: _EvidenceInputScope) -> dict[str, Any]:
    report["evidence_inputs"] = deepcopy(scope.evidence_inputs)
    return report


def _producer_name(function: Any) -> str:
    return f"{function.__module__}.{function.__name__}"


def _producer_hash(function: Any) -> str:
    return hashlib.sha256(inspect.getsource(function).encode("utf-8")).hexdigest()


def _current_manifest_hash() -> str:
    return build_product_code_manifest(ROOT)["manifest_hash"]


def _evidence_provenance(
    function: Any,
    *,
    input_artifacts: Sequence[Mapping[str, Any]],
    run_id: str | None,
    seed: int | None,
    episode_ids: Iterable[str] = (),
    context_ids: Iterable[str] = (),
    checkpoint_ids: Iterable[str] = (),
    aggregation_rule: str,
    manifest_hash: str | None = None,
) -> dict[str, Any]:
    """One complete provenance envelope shared by every evidence report."""

    return {
        "producer_function": _producer_name(function),
        "input_artifacts": [dict(item) for item in input_artifacts],
        "run_id": run_id,
        "seed": seed,
        "episode_ids": sorted({str(item) for item in episode_ids}),
        "context_ids": sorted({str(item) for item in context_ids}),
        "checkpoint_ids": sorted({str(item) for item in checkpoint_ids}),
        "aggregation_rule": aggregation_rule,
        "code_path_hash": _producer_hash(function),
        "product_code_manifest_hash": manifest_hash or _current_manifest_hash(),
    }


def _checkpoint_id(state: Mapping[str, Any]) -> str:
    return _hash(
        {
            "kind": "ego.life_playground.intervention_checkpoint.v1",
            "serialized_state": state,
        }
    )


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def build_product_code_manifest(repo_root: str | Path = ROOT) -> dict[str, Any]:
    """Hash exactly the six frozen live product files, in frozen order."""

    root = Path(repo_root).resolve()
    files: list[dict[str, Any]] = []
    for relative in PRODUCT_PATHS:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"missing frozen product path: {relative}")
        files.append(
            {
                "path": relative,
                "sha256": _sha256_path(path),
                "byte_count": path.stat().st_size,
            }
        )
    payload = {
        "schema_version": "ego.life_playground.product_code_manifest.v1",
        "files": files,
    }
    manifest_hash = _hash(payload)
    return {
        **payload,
        "manifest_hash": manifest_hash,
        "producer_function": _producer_name(build_product_code_manifest),
        "input_artifacts": [
            _artifact_ref(root / relative) for relative in PRODUCT_PATHS
        ],
        "run_id": None,
        "seed": None,
        "episode_ids": [],
        "context_ids": [],
        "checkpoint_ids": [],
        "aggregation_rule": "sha256_each_exact_ordered_six_file_payload_then_canonical_manifest",
        "code_path_hash": _producer_hash(build_product_code_manifest),
        "product_code_manifest_hash": manifest_hash,
    }


def run_cue_clock_fsm_baseline(
    state: Mapping[str, Any],
    command: Mapping[str, Any],
    run_meta: Mapping[str, Any],
) -> dict[str, Any]:
    """Independent cheap shortcut using only pre-decision public inputs.

    This function intentionally reimplements priors, deficit arithmetic,
    memory lookup, and tie-breaking.  It neither invokes the live reducer nor
    consumes stored traces, selected actions, outcomes, or post-action state.
    """

    before = deepcopy(dict(state))
    cue = str(command["cue"])
    sequence = int(command["sequence"])
    seed = int(run_meta["seed"])
    goal = deepcopy(before["current_goal"])
    goal_key = goal["state_variable"] or "homeostasis"
    context_key = f"{cue}|{goal_key}"
    interventions = dict(command["interventions"])
    memory = before["memory"] if interventions["memory_mode"] == "canonical" else {
        "episodic": [],
        "consolidated": [],
    }

    def total_deficit(organism: Mapping[str, float]) -> float:
        return sum(
            max(0.0, engine.TARGET_LEVEL - float(organism[key]))
            for key in engine.STATE_KEYS
        )

    def apply_delta(delta: Mapping[str, float]) -> dict[str, float]:
        return {
            key: _round(_clamp(float(before["organism"][key]) + float(delta[key])))
            for key in engine.STATE_KEYS
        }

    candidates: list[dict[str, Any]] = []
    for action in engine.ACTIONS:
        model_entry = before["model"].get(context_key, {}).get(action)
        if model_entry is not None and int(model_entry["count"]) > 0:
            predicted = {
                key: float(model_entry["ema_delta"][key]) for key in engine.STATE_KEYS
            }
            model_ref = {
                "source": "tabular_ema",
                "context_key": context_key,
                "action": action,
                "count": int(model_entry["count"]),
            }
        else:
            predicted = dict(engine.ACTION_PRIORS[action])
            for key, bonus in engine.CUE_BONUSES.get(cue, {}).get(action, {}).items():
                predicted[key] += 0.5 * float(bonus)
            predicted = {key: _round(predicted[key]) for key in engine.STATE_KEYS}
            model_ref = {
                "source": "hardcoded_prior",
                "context_key": context_key,
                "action": action,
                "count": 0,
            }

        predicted_after = apply_delta(predicted)
        if goal["status"] == "homeostasis":
            goal_reduction = 0.0
        else:
            key = str(goal["state_variable"])
            goal_reduction = _round(
                max(0.0, engine.TARGET_LEVEL - float(before["organism"][key]))
                - max(0.0, engine.TARGET_LEVEL - float(predicted_after[key]))
            )
        total_reduction = _round(total_deficit(before["organism"]) - total_deficit(predicted_after))

        memory_bias = 0.0
        memory_refs: list[str] = []
        for entry in memory.get("episodic", []):
            if (
                entry["cue"] == cue
                and entry["current_goal"] == goal_key
                and entry["action"] == action
            ):
                memory_bias += 0.20 * float(entry["utility"])
                memory_refs.append(str(entry["source_command_hash"]))
        for entry in memory.get("consolidated", []):
            if (
                entry["cue"] == cue
                and entry["current_goal"] == goal_key
                and entry["action"] == action
            ):
                memory_bias += 0.65 * float(entry["strength"])
                memory_refs.extend(str(item) for item in entry["source_command_hashes"])
        memory_bias = max(-0.5, min(0.5, memory_bias))

        digest = hashlib.sha256(
            f"{seed}|{sequence}|{context_key}|{action}".encode("utf-8")
        ).digest()
        tie = _round(
            (int.from_bytes(digest[:8], "big") / float(2**64 - 1)) * 1e-6,
            12,
        )
        untried = 0.025 if model_ref["count"] == 0 else 0.0
        score = _round(
            goal_reduction
            + total_reduction
            + memory_bias
            + untried
            - float(engine.ACTION_COSTS[action])
            + tie,
            9,
        )
        candidates.append(
            {
                "action": action,
                "predicted_delta": {key: _round(predicted[key]) for key in engine.STATE_KEYS},
                "current_goal_deficit_reduction": goal_reduction,
                "total_deficit_reduction": total_reduction,
                "memory_bias": _round(memory_bias),
                "untried_bonus": untried,
                "action_cost": engine.ACTION_COSTS[action],
                "deterministic_tie": tie,
                "total_score": score,
                "model_ref": model_ref,
                "memory_refs": sorted(set(memory_refs)),
            }
        )

    candidates.sort(key=lambda item: item["action"])
    selected = max(candidates, key=lambda item: (item["total_score"], item["deterministic_tie"]))
    selected_action = str(selected["action"])
    actual = dict(engine.ACTION_PRIORS[selected_action])
    for key, bonus in engine.CUE_BONUSES.get(cue, {}).get(selected_action, {}).items():
        actual[key] += float(bonus)
    actual = {key: _round(actual[key]) for key in engine.STATE_KEYS}
    context_id = _hash({"cue": cue, "goal": goal_key, "sequence": sequence})
    return {
        "schema_version": "ego.life_playground.shortcut_baseline.v1",
        "role": "baseline",
        **_evidence_provenance(
            run_cue_clock_fsm_baseline,
            input_artifacts=[
                _semantic_ref("serialized_predecision_state", before),
                _semantic_ref("typed_observation_command", command),
            ],
            run_id=str(run_meta["run_id"]),
            seed=seed,
            episode_ids=[str(before["clock"]["episode_id"])],
            context_ids=[context_id],
            aggregation_rule="independent_public_prior_model_memory_deficit_argmax",
        ),
        "episode_id": before["clock"]["episode_id"],
        "context_id": context_id,
        "selected_action": selected_action,
        "candidates": candidates,
        "actual_delta_from_public_table": actual,
        "next_organism_from_public_table": apply_delta(actual),
        "postdecision_inputs_read": False,
    }


def run_stored_trace_echo_control(traces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Demonstrate the appearance-only power of copying stored visible rows."""

    expected = [
        {
            "sequence": int(trace["sequence"]),
            "global_tick": int(trace["global_tick"]),
            "episode_index": int(trace["episode_index"]),
            "episode_tick": int(trace["episode_tick"]),
            "cue": str(trace["cue"]),
            "selected_action": str(trace["selected_action"]),
        }
        for trace in traces
    ]
    echoed = deepcopy(expected)
    matches = sum(left == right for left, right in zip(expected, echoed))
    run_id = None if not traces else str(traces[0].get("run_id"))
    seed = None if not traces else int(traces[0].get("seed"))
    return {
        "schema_version": "ego.life_playground.trace_echo_control.v1",
        "role": "post_hoc_appearance_control",
        **_evidence_provenance(
            run_stored_trace_echo_control,
            input_artifacts=[_semantic_ref("stored_posthoc_traces", list(traces))],
            run_id=run_id,
            seed=seed,
            episode_ids=[str(trace["episode_id"]) for trace in traces],
            context_ids=[str(trace["command_hash"]) for trace in traces],
            aggregation_rule="exact_visible_row_equality_over_stored_posthoc_rows",
        ),
        "visible_row_count": len(expected),
        "visible_row_match_count": matches,
        "visible_row_match_rate": 0.0 if not expected else matches / len(expected),
        "included_in_candidate_baseline_score": False,
        "causal_recomputation": False,
    }


def scan_for_leakage(
    payload: Mapping[str, Any], *, inject_positive_control: bool = False
) -> dict[str, Any]:
    """Context-aware scan for forbidden post-decision fields on causal inputs."""

    candidate = deepcopy(dict(payload))
    if inject_positive_control:
        command = candidate.setdefault("command", {})
        if isinstance(command, dict):
            command["selected_action"] = "__injected_positive_control__"
        else:
            candidate["selected_action"] = "__injected_positive_control__"

    always_forbidden = {
        "expected_action",
        "expected_selected_action",
        "expected_verdict",
        "hidden_label",
        "future_state",
        "state_after",
    }
    command_forbidden = always_forbidden | {
        "selected_action",
        "actual_delta",
        "prediction",
        "prediction_error",
        "candidates",
    }
    state_forbidden = always_forbidden | {
        "selected_action",
        "prediction",
        "prediction_error",
    }
    findings: list[dict[str, Any]] = []

    def walk(value: Any, path: str, context: str) -> None:
        if isinstance(value, Mapping):
            for raw_key, item in value.items():
                key = str(raw_key)
                child_path = f"{path}.{key}"
                forbidden = always_forbidden
                if context == "command":
                    forbidden = command_forbidden
                elif context == "state":
                    forbidden = state_forbidden
                if key in forbidden:
                    findings.append(
                        {
                            "path": child_path,
                            "field": key,
                            "reason": f"postdecision_or_hidden_field_on_{context}_surface",
                        }
                    )
                child_context = context
                if path == "$" and key in {"command", "state", "trace"}:
                    child_context = key
                walk(item, child_path, child_context)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]", context)

    walk(candidate, "$", "root")
    fired = inject_positive_control and any(
        finding["field"] == "selected_action" for finding in findings
    )
    state_value = candidate.get("state")
    command_value = candidate.get("command")
    episode_ids = []
    if isinstance(state_value, Mapping) and isinstance(state_value.get("clock"), Mapping):
        episode_ids = [str(state_value["clock"].get("episode_id"))]
    context_ids = []
    if isinstance(command_value, Mapping):
        context_ids = [str(command_value.get("command_hash") or _hash(command_value))]
    return {
        "schema_version": "ego.life_playground.leakage_scan.v1",
        **_evidence_provenance(
            scan_for_leakage,
            input_artifacts=[_semantic_ref("scanner_payload", candidate)],
            run_id=None,
            seed=None,
            episode_ids=episode_ids,
            context_ids=context_ids,
            aggregation_rule="recursive_contextual_forbidden_field_scan",
        ),
        "positive_control_injected": inject_positive_control,
        "positive_control_fired": fired,
        "findings": findings,
    }


def select_intervention_checkpoint(
    frames: Sequence[Any], *, minimum_global_tick: int = 16
) -> dict[str, Any]:
    """Select the frozen first recomputed frame at/after the requested tick."""

    eligible = [
        frame
        for frame in frames
        if int(frame.state["clock"]["global_tick"]) >= int(minimum_global_tick)
    ]
    if not eligible:
        raise ValueError(f"no checkpoint at or after global_tick {minimum_global_tick}")
    frame = min(eligible, key=lambda item: int(item.state["clock"]["global_tick"]))
    state = deepcopy(frame.state)
    return {
        "schema_version": "ego.life_playground.intervention_checkpoint.v1",
        **_evidence_provenance(
            select_intervention_checkpoint,
            input_artifacts=[_semantic_ref("recomputed_checkpoint_state", state)],
            run_id=None,
            seed=None,
            episode_ids=[str(state["clock"]["episode_id"])],
            checkpoint_ids=[_checkpoint_id(state)],
            aggregation_rule="minimum_global_tick_then_first_ordered_recomputed_frame",
        ),
        "checkpoint_id": _checkpoint_id(state),
        "sequence": int(frame.sequence),
        "global_tick": int(state["clock"]["global_tick"]),
        "episode_id": state["clock"]["episode_id"],
        "state": state,
    }


def run_paired_interventions(
    checkpoint_state: Mapping[str, Any],
    run_meta: Mapping[str, Any],
    *,
    cue: str,
) -> dict[str, Any]:
    """Rerun the sole reducer four ways from one serialized checkpoint."""

    state = deepcopy(dict(checkpoint_state))
    checkpoint_id = _checkpoint_id(state)
    sequence = int(state["clock"]["global_tick"]) + 1
    observation = {
        "cue": cue,
        "sequence": sequence,
        "trigger_source": "paired_intervention",
    }
    observation_id = _hash(observation)
    definitions = {
        "canonical": dict(engine.DEFAULT_INTERVENTIONS),
        "memory_off": {
            "memory_mode": "off",
            "update_mode": "enabled",
            "provenance_mode": "canonical",
        },
        "freeze_updates": {
            "memory_mode": "canonical",
            "update_mode": "frozen",
            "provenance_mode": "canonical",
        },
        "shuffle_provenance": {
            "memory_mode": "canonical",
            "update_mode": "enabled",
            "provenance_mode": "shuffle_projection",
        },
    }
    before_model = _json(state["model"])
    before_memory = _json(state["memory"])
    cases: dict[str, dict[str, Any]] = {}
    for name, interventions in definitions.items():
        command = engine.make_command(
            sequence=sequence,
            cue=cue,
            trigger_source="paired_intervention",
            interventions=interventions,
            prev_command_hash=state.get("last_command_hash"),
        )
        computed = engine.compute_step(deepcopy(state), command, run_meta)
        trace = computed.trace
        refs = sorted(
            {
                str(ref)
                for candidate in trace["candidates"]
                for ref in candidate["memory_refs"]
            }
        )
        cases[name] = {
            **_evidence_provenance(
                run_paired_interventions,
                input_artifacts=[
                    _semantic_ref("paired_checkpoint_state", state),
                    _semantic_ref(f"paired_command/{name}", command),
                ],
                run_id=str(run_meta["run_id"]),
                seed=int(run_meta["seed"]),
                episode_ids=[str(state["clock"]["episode_id"])],
                context_ids=[observation_id, str(command["command_hash"])],
                checkpoint_ids=[checkpoint_id],
                aggregation_rule=f"one_real_canonical_reducer_rerun:{name}",
            ),
            "checkpoint_id": checkpoint_id,
            "observation_id": observation_id,
            "command": command,
            "command_hash": command["command_hash"],
            "selected_action": trace["selected_action"],
            "candidates": trace["candidates"],
            "memory_read_refs": refs,
            "memory_read_count": len(refs),
            "model_update": trace["model_update"],
            "memory_update": trace["memory_update"],
            "provenance_projection": trace["provenance_projection"],
            "model_bytes_unchanged": before_model == _json(computed.next_state["model"]),
            "memory_bytes_unchanged": before_memory == _json(computed.next_state["memory"]),
            "state_after_hash": engine.state_hash(computed.next_state),
            "trace_hash": trace["trace_hash"],
            "engine_code_path_hash": trace["code_path_hash"],
        }

    canonical_scores = {
        item["action"]: float(item["total_score"])
        for item in cases["canonical"]["candidates"]
    }
    off_scores = {
        item["action"]: float(item["total_score"])
        for item in cases["memory_off"]["candidates"]
    }
    score_delta = {
        action: _round(canonical_scores[action] - off_scores[action], 9)
        for action in sorted(canonical_scores)
    }
    canonical_biases = [
        float(item["memory_bias"]) for item in cases["canonical"]["candidates"]
    ]
    blockers: list[str] = []
    if cases["canonical"]["memory_read_count"] == 0:
        blockers.append("natural_checkpoint_memory_read_set_empty")
    if not any(abs(value) > 0.0 for value in canonical_biases) or not any(
        abs(value) > 0.0 for value in score_delta.values()
    ):
        blockers.append("natural_checkpoint_memory_bias_zero")
    memory_off = cases["memory_off"]
    if memory_off["memory_read_count"] != 0 or any(
        float(item["memory_bias"]) != 0.0 for item in memory_off["candidates"]
    ):
        blockers.append("memory_off_read_or_score_effect_remained")
    if not memory_off["memory_bytes_unchanged"] or memory_off["memory_update"]["applied"]:
        blockers.append("memory_off_wrote_memory")
    frozen = cases["freeze_updates"]
    if not frozen["model_bytes_unchanged"] or not frozen["memory_bytes_unchanged"]:
        blockers.append("freeze_updates_changed_adaptive_bytes")
    if frozen["model_update"]["applied"] or frozen["memory_update"]["applied"]:
        blockers.append("freeze_updates_reported_applied_update")
    projection = cases["shuffle_provenance"]["provenance_projection"]
    marginals = projection["marginal_preservation"]
    if (
        projection["status"] != "applied"
        or int(projection["eligibility_count"]) < 2
        or int(projection["cross_slot_moves"]) < 1
        or not marginals["slot_counts_preserved"]
        or not marginals["bundle_multiset_preserved"]
    ):
        blockers.append(
            "shuffle_provenance_not_applied_or_insufficient_records:"
            + str(projection["status"])
        )

    def strip_memory_ids(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                key: strip_memory_ids(item)
                for key, item in value.items()
                if key != "memory_id"
            }
        if isinstance(value, list):
            return [strip_memory_ids(item) for item in value]
        return value

    renamed_state = deepcopy(state)
    renamed_count = 0
    for collection in ("episodic", "consolidated"):
        for index, record in enumerate(renamed_state["memory"][collection]):
            if "memory_id" in record:
                record["memory_id"] = f"opaque-renamed-{collection}-{index:06d}"
                renamed_count += 1
    canonical_behavior = {
        "selected_action": cases["canonical"]["selected_action"],
        "candidates": cases["canonical"]["candidates"],
    }
    renamed_computed = engine.compute_step(
        renamed_state, cases["canonical"]["command"], run_meta
    )
    renamed_behavior = {
        "selected_action": renamed_computed.trace["selected_action"],
        "candidates": renamed_computed.trace["candidates"],
    }
    source_semantic_hash = _hash(strip_memory_ids(state["memory"]))
    renamed_semantic_hash = _hash(strip_memory_ids(renamed_state["memory"]))
    memory_id_control = {
        **_evidence_provenance(
            run_paired_interventions,
            input_artifacts=[
                _semantic_ref("opaque_id_control/source_checkpoint", state),
                _semantic_ref("opaque_id_control/renamed_checkpoint", renamed_state),
                _semantic_ref("opaque_id_control/command", cases["canonical"]["command"]),
            ],
            run_id=str(run_meta["run_id"]),
            seed=int(run_meta["seed"]),
            episode_ids=[str(state["clock"]["episode_id"])],
            context_ids=[observation_id],
            checkpoint_ids=[checkpoint_id],
            aggregation_rule="rename_only_opaque_memory_ids_then_compare_candidate_behavior_canonical_json",
        ),
        "renamed_record_count": renamed_count,
        "source_semantic_memory_hash": source_semantic_hash,
        "renamed_semantic_memory_hash": renamed_semantic_hash,
        "semantic_memory_hash_unchanged": source_semantic_hash == renamed_semantic_hash,
        "source_candidate_behavior_hash": _hash(canonical_behavior),
        "renamed_candidate_behavior_hash": _hash(renamed_behavior),
        "candidate_behavior_bit_identical": _json(canonical_behavior) == _json(renamed_behavior),
        "selected_action_bit_identical": (
            canonical_behavior["selected_action"] == renamed_behavior["selected_action"]
        ),
    }
    if renamed_count == 0:
        blockers.append("opaque_memory_id_positive_control_no_records")
    if not memory_id_control["semantic_memory_hash_unchanged"]:
        blockers.append("opaque_memory_id_rename_changed_semantic_memory")
    if not memory_id_control["candidate_behavior_bit_identical"]:
        blockers.append("opaque_memory_id_leaked_into_candidate_behavior")

    return {
        "schema_version": "ego.life_playground.paired_interventions.v1",
        **_evidence_provenance(
            run_paired_interventions,
            input_artifacts=[
                _semantic_ref("serialized_checkpoint", state),
                _semantic_ref("typed_observation", observation),
            ],
            run_id=str(run_meta["run_id"]),
            seed=int(run_meta["seed"]),
            episode_ids=[str(state["clock"]["episode_id"])],
            context_ids=[observation_id],
            checkpoint_ids=[checkpoint_id],
            aggregation_rule="four_real_reducer_reruns_from_identical_checkpoint_and_observation",
        ),
        "checkpoint_id": checkpoint_id,
        "observation_id": observation_id,
        "engine_code_path_hash": run_meta["code_path_hash"],
        "cases": cases,
        "opaque_memory_id_rename_positive_control": memory_id_control,
        "canonical_minus_memory_off_score_delta": score_delta,
        "selection_level_shaping_observed": (
            cases["canonical"]["selected_action"] != cases["memory_off"]["selected_action"]
        ),
        "blocking_failures": blockers,
    }


def _tamper_copy(
    database: Path,
    run_id: str,
    name: str,
    mutate: Any,
    expected_reason_substring: str,
) -> dict[str, Any]:
    """Apply one real mutation to a disposable DB and require recovery failure."""

    metadata_connection = sqlite3.connect(str(database))
    try:
        meta_row = metadata_connection.execute(
            "SELECT run_meta_json FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        run_meta = {} if meta_row is None else json.loads(meta_row[0])
        command_context_ids = [
            str(json.loads(row[0])["command_hash"])
            for row in metadata_connection.execute(
                "SELECT command_json FROM commands WHERE run_id = ? ORDER BY sequence",
                (run_id,),
            ).fetchall()
        ]
        episode_ids = [
            str(json.loads(row[0])["episode_id"])
            for row in metadata_connection.execute(
                "SELECT trace_json FROM traces WHERE run_id = ? ORDER BY sequence",
                (run_id,),
            ).fetchall()
        ]
    finally:
        metadata_connection.close()

    def provenance(mutation: Mapping[str, Any]) -> dict[str, Any]:
        return _evidence_provenance(
            _tamper_copy,
            input_artifacts=[
                _artifact_ref(database),
                _semantic_ref(f"replay_tamper/{name}", mutation),
            ],
            run_id=run_id,
            seed=None if "seed" not in run_meta else int(run_meta["seed"]),
            episode_ids=episode_ids,
            context_ids=command_context_ids,
            aggregation_rule=f"actual_disposable_database_tamper_must_raise_expected_recovery_error:{name}",
        )

    with tempfile.TemporaryDirectory(prefix=f"ego-v1-{name}-") as temporary:
        copied = Path(temporary) / "tampered.sqlite3"
        shutil.copy2(database, copied)
        connection = sqlite3.connect(str(copied))
        try:
            mutation = mutate(connection, run_id)
            connection.commit()
        finally:
            connection.close()

        store: SQLiteEventStore | None = None
        try:
            store = SQLiteEventStore(copied)
            store.recover_run(run_id)
        except RecoveryError as exc:
            matched = expected_reason_substring in str(exc)
            return {
                **provenance(mutation),
                "mutation": mutation,
                "failed_closed": matched,
                "expected_failure_class": "RecoveryError",
                "expected_reason_substring": expected_reason_substring,
                "observed_failure_class": type(exc).__name__,
                "observed_failure_message": str(exc),
                "expected_reason_matched": matched,
                "tampered_database_sha256": _sha256_path(copied),
            }
        except Exception as exc:
            return {
                **provenance(mutation),
                "mutation": mutation,
                "failed_closed": False,
                "expected_failure_class": "RecoveryError",
                "expected_reason_substring": expected_reason_substring,
                "observed_failure_class": type(exc).__name__,
                "observed_failure_message": str(exc),
                "expected_reason_matched": False,
                "tampered_database_sha256": _sha256_path(copied),
            }
        finally:
            if store is not None:
                store.close()
        return {
            **provenance(mutation),
            "mutation": mutation,
            "failed_closed": False,
            "expected_failure_class": "RecoveryError",
            "expected_reason_substring": expected_reason_substring,
            "observed_failure_class": None,
            "observed_failure_message": None,
            "expected_reason_matched": False,
            "tampered_database_sha256": _sha256_path(copied),
        }


def _tamper_stored_action(connection: sqlite3.Connection, run_id: str) -> dict[str, Any]:
    row = connection.execute(
        "SELECT sequence, trace_json FROM traces WHERE run_id = ? ORDER BY sequence LIMIT 1",
        (run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("no stored trace available for action tamper")
    trace = json.loads(row[1])
    original = str(trace["selected_action"])
    replacement = next(action for action in engine.ACTIONS if action != original)
    trace["selected_action"] = replacement
    trace["trace_hash"] = _hash(
        {key: value for key, value in trace.items() if key != "trace_hash"}
    )
    connection.execute(
        "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = ?",
        (_json(trace), trace["trace_hash"], run_id, int(row[0])),
    )
    return {
        "kind": "stored_selected_action_and_hash_rewritten",
        "sequence": int(row[0]),
        "original": original,
        "replacement": replacement,
        "attacker_rehashed_payload_and_column": True,
    }


def _tamper_command_payload(connection: sqlite3.Connection, run_id: str) -> dict[str, Any]:
    row = connection.execute(
        "SELECT sequence, command_json FROM commands WHERE run_id = ? ORDER BY sequence LIMIT 1",
        (run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("no command available for payload tamper")
    command = json.loads(row[1])
    original = str(command["cue"])
    replacement = next(cue for cue in engine.CUES if cue != original)
    command["cue"] = replacement
    command["command_hash"] = _hash(
        {key: value for key, value in command.items() if key != "command_hash"}
    )
    connection.execute(
        "UPDATE commands SET command_json = ?, command_hash = ? WHERE run_id = ? AND sequence = ?",
        (_json(command), command["command_hash"], run_id, int(row[0])),
    )
    return {
        "kind": "typed_command_payload_and_hash_rewritten",
        "sequence": int(row[0]),
        "original_cue": original,
        "replacement_cue": replacement,
        "attacker_rehashed_payload_and_column": True,
    }


def _tamper_initial_state(connection: sqlite3.Connection, run_id: str) -> dict[str, Any]:
    row = connection.execute(
        "SELECT initial_state_json FROM runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    if row is None:
        raise RuntimeError("no initial state available for tamper")
    state = json.loads(row[0])
    original = float(state["organism"]["energy"])
    replacement = _round(min(0.99, original + 0.031))
    state["organism"]["energy"] = replacement
    state_hash = _hash(state)
    connection.execute(
        "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
        (_json(state), state_hash, run_id),
    )
    return {
        "kind": "initial_state_payload_and_hash_rewritten",
        "original_energy": original,
        "replacement_energy": replacement,
        "attacker_rehashed_payload_and_column": True,
    }


def _tamper_code_path_hash(connection: sqlite3.Connection, run_id: str) -> dict[str, Any]:
    replacement = "0" * 64
    connection.execute(
        "UPDATE runs SET code_path_hash = ? WHERE run_id = ?", (replacement, run_id)
    )
    return {
        "kind": "persisted_code_path_hash_rewritten",
        "replacement": replacement,
    }


def _recovery_hash_payload(recovered: Any) -> dict[str, Any]:
    return {
        "recovered": bool(recovered.recovered),
        "command_count": int(recovered.command_count),
        "final_state_hash": engine.state_hash(recovered.state),
        "final_model_hash": _hash(recovered.state["model"]),
        "final_memory_hash": _hash(recovered.state["memory"]),
        "current_goal_hash": _hash(recovered.state["current_goal"]),
        "clock_hash": _hash(recovered.state["clock"]),
        "trace_chain_tip": recovered.state["last_trace_hash"],
        "run_id": recovered.run_id,
        "seed": recovered.run_meta["seed"],
        "episode_ids": sorted(
            {str(trace["episode_id"]) for trace in recovered.traces}
        ),
        "engine_code_path_hash": recovered.run_meta["code_path_hash"],
    }


def _probe_recovery(database: str | Path, run_id: str) -> dict[str, Any]:
    """Open and recover one DB in the current externally orchestrated process."""

    store = SQLiteEventStore(Path(database).resolve())
    try:
        recovered = store.recover_run(run_id)
    finally:
        store.close()
    return {
        "schema_version": "ego.life_playground.fresh_process_recovery_probe.v1",
        "probe_pid": os.getpid(),
        **_recovery_hash_payload(recovered),
    }


def _prepare_fresh_process_probe_request(
    database: Path, recovered: Any
) -> dict[str, Any]:
    expected = _recovery_hash_payload(recovered)
    hash_fields = (
        "final_state_hash",
        "final_model_hash",
        "final_memory_hash",
        "current_goal_hash",
        "clock_hash",
        "trace_chain_tip",
    )
    challenge = secrets.token_hex(32)
    pipe_name = rf"\\.\pipe\EgoV1Continuity-{challenge}"
    operator_sid = _current_process_user_sid()
    pipe_sddl = _operator_only_pipe_sddl(operator_sid)
    return {
        "schema_version": "ego.life_playground.fresh_process_probe_request.v1",
        **_evidence_provenance(
            _prepare_fresh_process_probe_request,
            input_artifacts=[_artifact_ref(database)],
            run_id=recovered.run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=[str(trace["episode_id"]) for trace in recovered.traces],
            context_ids=[str(trace["command_hash"]) for trace in recovered.traces],
            aggregation_rule="freeze_database_challenge_prepare_pid_and_expected_recovery_hashes",
        ),
        "challenge": challenge,
        "pipe_name": pipe_name,
        "pipe_security": {
            "operator_sid": operator_sid,
            "sddl": pipe_sddl,
            "sddl_sha256": hashlib.sha256(pipe_sddl.encode("utf-8")).hexdigest(),
            "first_pipe_instance": True,
            "remote_clients_rejected": True,
        },
        "prepare_pid": os.getpid(),
        "database_path": str(database.resolve()),
        "database_sha256": _sha256_path(database),
        "run_id": recovered.run_id,
        "expected_command_count": int(recovered.command_count),
        "expected_hashes": {key: expected[key] for key in hash_fields},
        "hash_fields": list(hash_fields),
        "engine_code_path_hash": recovered.run_meta["code_path_hash"],
        "product_code_manifest_hash": _current_manifest_hash(),
    }


def _handshake_binding(
    request: Mapping[str, Any], receipt: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": "ego.life_playground.fresh_process_pipe_binding.v1",
        "challenge": request["challenge"],
        "pipe_name": request["pipe_name"],
        "pipe_security": request["pipe_security"],
        "prepare_pid": request["prepare_pid"],
        "probe_pid_claimed": receipt["probe_pid_claimed"],
        "database_path": request["database_path"],
        "database_sha256": request["database_sha256"],
        "run_id": request["run_id"],
        "engine_code_path_hash": request["engine_code_path_hash"],
        "product_code_manifest_hash": request["product_code_manifest_hash"],
        "expected_command_count": request["expected_command_count"],
        "expected_hashes": request["expected_hashes"],
        "output_path": receipt["output_path"],
        "receipt_path": receipt["receipt_path"],
    }


def build_fresh_process_probe_receipt(
    output_dir: str | Path, receipt_path: str | Path | None = None
) -> dict[str, Any]:
    output = Path(output_dir).resolve()
    receipt_file = Path(receipt_path or (output / "unit-probe-receipt.json")).resolve()
    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    request = replay["fresh_process_protocol"]["request"]
    database = Path(request["database_path"]).resolve()
    if _sha256_path(database) != request["database_sha256"]:
        raise RuntimeError("probe DB SHA differs from prepared request")
    recovered = _probe_recovery(database, str(request["run_id"]))
    receipt = {
        "schema_version": "ego.life_playground.fresh_process_probe_receipt.v1",
        "challenge": request["challenge"],
        "prepare_pid": request["prepare_pid"],
        "probe_pid": recovered["probe_pid"],
        "probe_pid_claimed": recovered["probe_pid"],
        "pipe_name": request["pipe_name"],
        "pipe_security": request["pipe_security"],
        "output_path": str(output),
        "receipt_path": str(receipt_file),
        "database_path": str(database),
        "database_sha256": _sha256_path(database),
        "run_id": recovered["run_id"],
        "command_count": recovered["command_count"],
        "recovered": recovered["recovered"],
        "hashes": {
            key: recovered[key] for key in request["hash_fields"]
        },
        "engine_code_path_hash": recovered["engine_code_path_hash"],
        "product_code_manifest_hash": request["product_code_manifest_hash"],
    }
    receipt["binding_hash"] = _hash(_handshake_binding(request, receipt))
    return receipt


def validate_fresh_process_probe_receipt(
    request: Mapping[str, Any],
    receipt: Mapping[str, Any],
    attestation: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if receipt.get("schema_version") != "ego.life_playground.fresh_process_probe_receipt.v1":
        blockers.append("receipt_schema_mismatch")
    if receipt.get("challenge") != request.get("challenge"):
        blockers.append("challenge_mismatch")
    if receipt.get("prepare_pid") != request.get("prepare_pid"):
        blockers.append("prepare_pid_mismatch")
    if receipt.get("probe_pid") == request.get("prepare_pid"):
        blockers.append("probe_pid_equals_prepare_pid")
    if receipt.get("probe_pid_claimed") != receipt.get("probe_pid"):
        blockers.append("claimed_probe_pid_fields_disagree")
    if receipt.get("pipe_name") != request.get("pipe_name"):
        blockers.append("pipe_name_mismatch")
    if receipt.get("pipe_security") != request.get("pipe_security"):
        blockers.append("pipe_security_mismatch")
    try:
        current_operator_sid = _current_process_user_sid()
    except Exception:
        current_operator_sid = None
    pipe_security = request.get("pipe_security")
    if not isinstance(pipe_security, Mapping):
        blockers.append("pipe_security_missing")
    elif pipe_security.get("operator_sid") != current_operator_sid:
        blockers.append("pipe_operator_sid_mismatch")
    elif current_operator_sid is not None:
        expected_sddl = _operator_only_pipe_sddl(current_operator_sid)
        if pipe_security != {
            "operator_sid": current_operator_sid,
            "sddl": expected_sddl,
            "sddl_sha256": hashlib.sha256(expected_sddl.encode("utf-8")).hexdigest(),
            "first_pipe_instance": True,
            "remote_clients_rejected": True,
        }:
            blockers.append("pipe_security_contract_mismatch")
    if receipt.get("database_path") != request.get("database_path"):
        blockers.append("database_path_mismatch")
    if receipt.get("database_sha256") != request.get("database_sha256"):
        blockers.append("database_sha256_mismatch")
    try:
        current_database_sha = _sha256_path(Path(str(request.get("database_path"))).resolve())
    except Exception:
        current_database_sha = None
    if current_database_sha != request.get("database_sha256"):
        blockers.append("current_database_sha256_mismatch")
    if receipt.get("run_id") != request.get("run_id"):
        blockers.append("run_id_mismatch")
    if receipt.get("command_count") != request.get("expected_command_count"):
        blockers.append("command_count_mismatch")
    if receipt.get("recovered") is not True:
        blockers.append("probe_did_not_recover")
    if receipt.get("hashes") != request.get("expected_hashes"):
        blockers.append("recovery_hash_mismatch")
    if receipt.get("engine_code_path_hash") != request.get("engine_code_path_hash"):
        blockers.append("engine_code_path_hash_mismatch")
    if receipt.get("product_code_manifest_hash") != request.get("product_code_manifest_hash"):
        blockers.append("product_code_manifest_hash_mismatch")
    try:
        expected_binding_hash = _hash(_handshake_binding(request, receipt))
    except Exception:
        expected_binding_hash = None
    if receipt.get("binding_hash") != expected_binding_hash:
        blockers.append("binding_hash_mismatch")
    attestation_blockers = list(attestation.get("blocking_failures", []))
    if attestation.get("valid") is not True:
        blockers.append("live_pipe_attestation_failed")
    if attestation.get("probe_exit_observed") is not True:
        blockers.append("probe_exit_not_observed_after_ack")
    if attestation.get("probe_exit_code") != 0:
        blockers.append("probe_exit_code_not_zero")
    if attestation.get("no_orphan") is not True:
        blockers.append("probe_orphan_not_ruled_out")
    observed_pid = attestation.get("server_pid")
    if observed_pid != receipt.get("probe_pid_claimed"):
        blockers.append("attested_server_pid_mismatch")
    if observed_pid == request.get("prepare_pid"):
        blockers.append("attested_server_pid_equals_prepare_pid")
    if observed_pid == attestation.get("finalizer_pid"):
        blockers.append("attested_server_pid_equals_finalizer_pid")
    return {
        "valid": blockers == [],
        "blocking_failures": blockers,
        "attestation_blocking_failures": attestation_blockers,
        "prepare_pid": request.get("prepare_pid"),
        "probe_pid_claimed": receipt.get("probe_pid_claimed"),
        "probe_pid_observed": observed_pid,
        "finalizer_pid": attestation.get("finalizer_pid"),
        "process_boundary": bool(
            attestation.get("valid")
            and attestation.get("probe_exit_observed") is True
            and attestation.get("probe_exit_code") == 0
            and attestation.get("no_orphan") is True
            and len(
                {
                    request.get("prepare_pid"),
                    observed_pid,
                    attestation.get("finalizer_pid"),
                }
            )
            == 3
        ),
    }


def _probe_snapshot(database: Path, run_id: str, hash_fields: Sequence[str]) -> dict[str, Any]:
    recovered = _probe_recovery(database, run_id)
    return {
        "database_sha256": _sha256_path(database),
        "command_count": recovered["command_count"],
        "hashes": {key: recovered[key] for key in hash_fields},
        "engine_code_path_hash": recovered["engine_code_path_hash"],
    }


def _snapshot_matches_request(
    snapshot: Mapping[str, Any], request: Mapping[str, Any]
) -> bool:
    return bool(
        snapshot.get("database_sha256") == request.get("database_sha256")
        and snapshot.get("command_count") == request.get("expected_command_count")
        and snapshot.get("hashes") == request.get("expected_hashes")
        and snapshot.get("engine_code_path_hash") == request.get("engine_code_path_hash")
    )


def _response_hash(
    binding: Mapping[str, Any], nonce: str, probe_pid: int, snapshot: Mapping[str, Any]
) -> str:
    return _hash(
        {
            "kind": "ego.life_playground.named_pipe_challenge_response.v1",
            "binding": binding,
            "nonce": nonce,
            "probe_pid": probe_pid,
            "snapshot": snapshot,
        }
    )


def _ack_hash(challenge: str, nonce: str, server_pid: int, finalizer_pid: int) -> str:
    return _hash(
        {
            "kind": "ego.life_playground.named_pipe_finalize_ack.v1",
            "challenge": challenge,
            "nonce": nonce,
            "server_pid": server_pid,
            "finalizer_pid": finalizer_pid,
        }
    )


def serve_fresh_process_probe(
    output_dir: str | Path, receipt_path: str | Path
) -> None:
    """Serve one live challenge and exit only after a valid finalizer ACK."""

    output = Path(output_dir).resolve()
    receipt_file = Path(receipt_path).resolve()
    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    request = replay["fresh_process_protocol"]["request"]
    if len(str(request["challenge"])) != 64:
        raise RuntimeError("probe challenge is not 256 bits")
    pipe_security = request.get("pipe_security")
    if not isinstance(pipe_security, Mapping):
        raise RuntimeError("prepared request has no named-pipe security contract")
    operator_sid = str(pipe_security.get("operator_sid", ""))
    expected_sddl = _operator_only_pipe_sddl(operator_sid)
    if pipe_security != {
        "operator_sid": operator_sid,
        "sddl": expected_sddl,
        "sddl_sha256": hashlib.sha256(expected_sddl.encode("utf-8")).hexdigest(),
        "first_pipe_instance": True,
        "remote_clients_rejected": True,
    }:
        raise RuntimeError("prepared named-pipe security contract is not exact")
    pipe_handle = _create_named_pipe_server(
        str(request["pipe_name"]), operator_sid
    )
    library = _kernel32()
    connected = False
    try:
        receipt = build_fresh_process_probe_receipt(output, receipt_file)
        receipt_file.parent.mkdir(parents=True, exist_ok=True)
        _write_json(receipt_file, receipt)
        _connect_named_pipe_server(pipe_handle)
        connected = True
        challenge_message = _pipe_read_frame(pipe_handle)
        binding = _handshake_binding(request, receipt)
        finalizer_pid = challenge_message.get("finalizer_pid")
        nonce = challenge_message.get("nonce")
        if challenge_message.get("kind") != "ego.life_playground.named_pipe_challenge.v1":
            raise RuntimeError("unexpected named-pipe challenge kind")
        if challenge_message.get("challenge") != request["challenge"]:
            raise RuntimeError("named-pipe challenge mismatch")
        if challenge_message.get("binding") != binding:
            raise RuntimeError("named-pipe binding mismatch")
        if challenge_message.get("binding_hash") != _hash(binding):
            raise RuntimeError("named-pipe binding hash mismatch")
        if not isinstance(nonce, str) or len(nonce) != 64:
            raise RuntimeError("finalizer nonce is not 256 bits")
        if not isinstance(finalizer_pid, int) or finalizer_pid in {
            int(request["prepare_pid"]),
            os.getpid(),
        }:
            raise RuntimeError("prepare/probe/finalizer PIDs are not distinct")
        database = Path(request["database_path"]).resolve()
        after_challenge = _probe_snapshot(
            database, str(request["run_id"]), request["hash_fields"]
        )
        if not _snapshot_matches_request(after_challenge, request):
            raise RuntimeError("database or recovery hashes drifted before probe response")
        response = {
            "kind": "ego.life_playground.named_pipe_challenge_response.v1",
            "challenge": request["challenge"],
            "binding_hash": _hash(binding),
            "nonce": nonce,
            "probe_pid_claimed": os.getpid(),
            "snapshot_after_challenge": after_challenge,
            "response_hash": _response_hash(
                binding, nonce, os.getpid(), after_challenge
            ),
        }
        _pipe_write_frame(pipe_handle, response)
        acknowledgement = _pipe_read_frame(pipe_handle)
        expected_ack = _ack_hash(
            str(request["challenge"]), nonce, os.getpid(), int(finalizer_pid)
        )
        if acknowledgement != {
            "kind": "ego.life_playground.named_pipe_finalize_ack.v1",
            "ack_hash": expected_ack,
        }:
            raise RuntimeError("finalizer acknowledgement mismatch")
    finally:
        if connected:
            library.DisconnectNamedPipe(pipe_handle)
        library.CloseHandle(pipe_handle)


def _normalize_windows_path(value: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(value)))


def _expected_probe_argv(receipt: Mapping[str, Any]) -> list[str]:
    return [
        _normalize_windows_path(sys.executable),
        _normalize_windows_path(Path(__file__).resolve()),
        "--probe",
        "--output",
        _normalize_windows_path(str(receipt["output_path"])),
        "--probe-receipt",
        _normalize_windows_path(str(receipt["receipt_path"])),
    ]


def _normalized_observed_argv(argv: Sequence[str]) -> list[str]:
    if len(argv) != 7:
        return list(argv)
    return [
        _normalize_windows_path(argv[0]),
        _normalize_windows_path(argv[1]),
        argv[2],
        argv[3],
        _normalize_windows_path(argv[4]),
        argv[5],
        _normalize_windows_path(argv[6]),
    ]


def _perform_named_pipe_attestation(
    request: Mapping[str, Any],
    receipt: Mapping[str, Any],
    receipt_path: str | Path,
) -> dict[str, Any]:
    """Attest one live server using the same connected pipe/process handles."""

    blockers: list[str] = []
    pipe_handle: Any = None
    process_handle: Any = None
    observed_pid: int | None = None
    server_image: str | None = None
    server_commandline: str | None = None
    observed_argv: list[str] = []
    response: dict[str, Any] | None = None
    ack_sent = False
    probe_exit_observed = False
    probe_exit_code: int | None = None
    no_orphan = False
    exit_wait_result: int | None = None
    finalizer_pid = os.getpid()
    pre_snapshot: dict[str, Any] | None = None
    post_snapshot: dict[str, Any] | None = None
    try:
        if _normalize_windows_path(receipt_path) != _normalize_windows_path(
            str(receipt.get("receipt_path", ""))
        ):
            blockers.append("receipt_path_argument_mismatch")
        database = Path(str(request["database_path"])).resolve()
        pre_snapshot = _probe_snapshot(
            database, str(request["run_id"]), request["hash_fields"]
        )
        if not _snapshot_matches_request(pre_snapshot, request):
            blockers.append("database_or_hash_drift_before_handshake")
        current_operator_sid = _current_process_user_sid()
        pipe_security = request.get("pipe_security")
        expected_sddl = _operator_only_pipe_sddl(current_operator_sid)
        expected_pipe_security = {
            "operator_sid": current_operator_sid,
            "sddl": expected_sddl,
            "sddl_sha256": hashlib.sha256(expected_sddl.encode("utf-8")).hexdigest(),
            "first_pipe_instance": True,
            "remote_clients_rejected": True,
        }
        if pipe_security != expected_pipe_security:
            blockers.append("pipe_security_contract_mismatch")
        pipe_handle = _open_named_pipe_client(str(request["pipe_name"]))
        pid_value = wintypes.ULONG()
        if not _kernel32().GetNamedPipeServerProcessId(
            pipe_handle, ctypes.byref(pid_value)
        ):
            _raise_last_winerror("GetNamedPipeServerProcessId")
        observed_pid = int(pid_value.value)
        if observed_pid in {int(request["prepare_pid"]), finalizer_pid}:
            blockers.append("prepare_probe_finalizer_pids_not_distinct")
        process_handle = _kernel32().OpenProcess(
            _PROCESS_QUERY_LIMITED_INFORMATION
            | _PROCESS_QUERY_INFORMATION
            | _PROCESS_SYNCHRONIZE,
            False,
            observed_pid,
        )
        if not process_handle:
            _raise_last_winerror("OpenProcess(named-pipe server)")
        if not _process_is_active(process_handle):
            blockers.append("named_pipe_server_exited_before_challenge")
        server_image = _query_process_image(process_handle)
        if _normalize_windows_path(server_image) != _normalize_windows_path(sys.executable):
            blockers.append("probe_executable_mismatch")
        server_commandline = _query_process_commandline(process_handle)
        observed_argv = _normalized_observed_argv(
            _split_windows_commandline(server_commandline)
        )
        if observed_argv != _expected_probe_argv(receipt):
            blockers.append("probe_commandline_mismatch")
        if observed_pid != receipt.get("probe_pid_claimed"):
            blockers.append("observed_server_pid_differs_from_claimed_probe_pid")
        binding = _handshake_binding(request, receipt)
        if receipt.get("binding_hash") != _hash(binding):
            blockers.append("receipt_binding_hash_mismatch")
        if blockers:
            raise RuntimeError("pre-challenge attestation failed")
        nonce = secrets.token_hex(32)
        challenge_message = {
            "kind": "ego.life_playground.named_pipe_challenge.v1",
            "challenge": request["challenge"],
            "binding": binding,
            "binding_hash": _hash(binding),
            "nonce": nonce,
            "finalizer_pid": finalizer_pid,
        }
        _pipe_write_frame(pipe_handle, challenge_message)
        response = _pipe_read_frame(pipe_handle)
        if response.get("kind") != "ego.life_playground.named_pipe_challenge_response.v1":
            blockers.append("challenge_response_kind_mismatch")
        if response.get("challenge") != request["challenge"]:
            blockers.append("challenge_response_challenge_mismatch")
        if response.get("binding_hash") != _hash(binding):
            blockers.append("challenge_response_binding_mismatch")
        if response.get("nonce") != nonce:
            blockers.append("challenge_response_nonce_mismatch")
        if response.get("probe_pid_claimed") != observed_pid:
            blockers.append("challenge_response_pid_mismatch")
        response_snapshot = response.get("snapshot_after_challenge")
        if not isinstance(response_snapshot, Mapping) or not _snapshot_matches_request(
            response_snapshot, request
        ):
            blockers.append("probe_snapshot_after_challenge_mismatch")
        expected_response_hash = _response_hash(
            binding,
            nonce,
            observed_pid,
            response_snapshot if isinstance(response_snapshot, Mapping) else {},
        )
        if response.get("response_hash") != expected_response_hash:
            blockers.append("challenge_response_hash_mismatch")
        post_snapshot = _probe_snapshot(
            database, str(request["run_id"]), request["hash_fields"]
        )
        if not _snapshot_matches_request(post_snapshot, request):
            blockers.append("database_or_hash_drift_after_handshake")
        if not _process_is_active(process_handle):
            blockers.append("named_pipe_server_exited_before_ack")
        if blockers:
            raise RuntimeError("challenge-response attestation failed")
        acknowledgement = {
            "kind": "ego.life_playground.named_pipe_finalize_ack.v1",
            "ack_hash": _ack_hash(
                str(request["challenge"]), nonce, observed_pid, finalizer_pid
            ),
        }
        _pipe_write_frame(pipe_handle, acknowledgement)
        ack_sent = True
        exit_observation = _wait_for_process_exit(process_handle)
        probe_exit_observed = bool(exit_observation["probe_exit_observed"])
        probe_exit_code = int(exit_observation["probe_exit_code"])
        no_orphan = bool(exit_observation["no_orphan"])
        exit_wait_result = int(exit_observation["wait_result"])
        if not probe_exit_observed:
            blockers.append("probe_exit_not_observed_after_ack")
        if probe_exit_code != 0:
            blockers.append("probe_exit_code_not_zero")
        if not no_orphan:
            blockers.append("probe_orphan_not_ruled_out")
    except Exception as exc:
        if not blockers:
            blockers.append(
                f"named_pipe_attestation_error:{type(exc).__name__}:{exc}"
            )
    finally:
        if process_handle:
            _kernel32().CloseHandle(process_handle)
        if pipe_handle and pipe_handle != _INVALID_HANDLE_VALUE:
            _kernel32().CloseHandle(pipe_handle)
    return {
        "valid": bool(
            blockers == []
            and ack_sent
            and probe_exit_observed
            and probe_exit_code == 0
            and no_orphan
        ),
        "blocking_failures": blockers,
        "prepare_pid": request.get("prepare_pid"),
        "probe_pid_claimed": receipt.get("probe_pid_claimed"),
        "server_pid": observed_pid,
        "finalizer_pid": finalizer_pid,
        "server_executable": server_image,
        "server_commandline": server_commandline,
        "server_argv": observed_argv,
        "expected_argv": _expected_probe_argv(receipt),
        "challenge_response_valid": response is not None and blockers == [],
        "ack_sent": ack_sent,
        "probe_exit_observed": probe_exit_observed,
        "probe_exit_code": probe_exit_code,
        "no_orphan": no_orphan,
        "probe_exit_wait_result": exit_wait_result,
        "probe_exit_timeout_ms": _PROBE_EXIT_TIMEOUT_MS,
        "pre_handshake_snapshot": pre_snapshot,
        "post_handshake_snapshot": post_snapshot,
    }


def run_replay_checks(database: str | Path, run_id: str) -> dict[str, Any]:
    """Freshly recompute the run and exercise four actual tamper controls."""

    path = Path(database).resolve()
    store = SQLiteEventStore(path)
    try:
        recovered = store.recover_run(run_id)
    finally:
        store.close()
    request = _prepare_fresh_process_probe_request(path, recovered)
    fresh = {
        "status": "external_probe_required",
        "recovered": False,
        "process_boundary": False,
        "final_hashes_match_parent": False,
        **_evidence_provenance(
            run_replay_checks,
            input_artifacts=[
                _artifact_ref(path),
                _semantic_ref("fresh_process_probe_request", request),
            ],
            run_id=run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=[str(trace["episode_id"]) for trace in recovered.traces],
            context_ids=[request["challenge"]],
            aggregation_rule="block_until_external_probe_receipt_validates",
        ),
    }
    controls = {
        "stored_action_rehashed": _tamper_copy(
            path,
            run_id,
            "stored-action",
            _tamper_stored_action,
            "stored trace differs from independent recomputation",
        ),
        "command_payload": _tamper_copy(
            path,
            run_id,
            "command-payload",
            _tamper_command_payload,
            "stored trace differs from independent recomputation",
        ),
        "initial_state": _tamper_copy(
            path,
            run_id,
            "initial-state",
            _tamper_initial_state,
            "stored trace differs from independent recomputation",
        ),
        "code_path_hash": _tamper_copy(
            path,
            run_id,
            "code-path",
            _tamper_code_path_hash,
            "engine code-path drift detected",
        ),
    }
    blockers = [
        f"tamper_control_did_not_fail_closed:{name}"
        for name, report in controls.items()
        if not report["failed_closed"]
    ]
    blockers.append("fresh_process_probe_receipt_absent")
    return {
        "schema_version": "ego.life_playground.replay_report.v1",
        **_evidence_provenance(
            run_replay_checks,
            input_artifacts=[_artifact_ref(path)],
            run_id=run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=[str(trace["episode_id"]) for trace in recovered.traces],
            context_ids=[str(trace["command_hash"]) for trace in recovered.traces],
            aggregation_rule="prepare_external_fresh_process_probe_and_run_disposable_tamper_controls",
        ),
        "engine_code_path_hash": recovered.run_meta["code_path_hash"],
        "fresh_recovery": fresh,
        "fresh_process_protocol": {"request": request, "receipt": None, "validation": None},
        "tamper_controls": controls,
        "blocking_failures": blockers,
    }


def _run_atomicity_control(
    database: Path, run_id: str, manifest_hash: str | None = None
) -> dict[str, Any]:
    """Inject a real second-write failure and observe transaction/UI truth."""

    with tempfile.TemporaryDirectory(prefix="ego-v1-atomicity-") as temporary:
        copied = Path(temporary) / "atomicity.sqlite3"
        shutil.copy2(database, copied)
        store = SQLiteEventStore(copied)
        callbacks: list[dict[str, Any]] = []
        controller = PlaygroundController(
            store,
            run_id=run_id,
            on_committed=lambda state, trace: callbacks.append(
                {"state": engine.state_hash(state), "trace": trace["trace_hash"]}
            ),
        )
        counts_before = store.row_counts(run_id)
        state_before = engine.state_hash(controller.state)
        frame_count_before = len(controller.recovery.frames)
        store.connection.executescript(
            """
            CREATE TRIGGER injected_second_write_failure
            BEFORE INSERT ON traces
            BEGIN
              SELECT RAISE(ABORT, 'injected trace insert failure');
            END;
            """
        )
        dispatched = controller.dispatch(
            "novelty",
            engine.DEFAULT_INTERVENTIONS,
            trigger_source="headless_acceptance",
        )
        counts_after = store.row_counts(run_id)
        state_after = engine.state_hash(controller.state)
        frame_count_after = len(controller.recovery.frames)
        store.close()
    checks = {
        "receipt_rejected": not dispatched.receipt.committed,
        "command_trace_parity_preserved": counts_after[0] == counts_after[1],
        "row_counts_unchanged": counts_before == counts_after,
        "controller_state_unchanged": state_before == state_after,
        "timeline_frames_unchanged": frame_count_before == frame_count_after,
        "committed_callback_not_called": callbacks == [],
    }
    return {
        **_evidence_provenance(
            _run_atomicity_control,
            input_artifacts=[
                _artifact_ref(database),
                _semantic_ref("atomicity/injected_trace_insert_abort", {"trigger": "injected_second_write_failure"}),
            ],
            run_id=run_id,
            seed=int(controller.run_meta["seed"]),
            episode_ids=[str(trace["episode_id"]) for trace in controller.recovery.traces],
            context_ids=[str(controller.state.get("last_command_hash"))],
            aggregation_rule="all_real_second_insert_abort_atomicity_checks_true",
            manifest_hash=manifest_hash,
        ),
        "injection": "SQLite BEFORE INSERT ON traces RAISE(ABORT)",
        "receipt": {
            "committed": dispatched.receipt.committed,
            "error": dispatched.receipt.error,
        },
        "row_counts_before": {"commands": counts_before[0], "traces": counts_before[1]},
        "row_counts_after": {"commands": counts_after[0], "traces": counts_after[1]},
        "checks": checks,
        "passed": all(checks.values()),
    }


def _headless_diagnostic_run(database: Path, run_id: str) -> dict[str, Any]:
    if database.exists():
        database.unlink()
    store = SQLiteEventStore(database)
    controller = PlaygroundController(store, run_id=run_id, seed=17)
    receipts: list[dict[str, Any]] = []
    for _ in range(24):
        dispatched = controller.dispatch(
            "novelty",
            engine.DEFAULT_INTERVENTIONS,
            trigger_source="headless_acceptance",
        )
        receipts.append(
            {
                "sequence": dispatched.receipt.sequence,
                "committed": dispatched.receipt.committed,
                "error": dispatched.receipt.error,
            }
        )
        if not dispatched.receipt.committed:
            break
    recovered = controller.recover()
    store.close()
    return {
        "mode": "headless_diagnostic_only",
        "receipts": receipts,
        "command_count": recovered.command_count,
        "all_committed": all(item["committed"] for item in receipts) and len(receipts) == 24,
    }


def _drive_real_tk_run(database: Path, run_id: str) -> tuple[dict[str, Any], list[str]]:
    """Invoke the actual ttk Run/Pause widgets and drain Tk's scheduler."""

    blockers: list[str] = []
    if database.exists():
        database.unlink()
    store = SQLiteEventStore(database)
    controller = PlaygroundController(store, run_id=run_id, seed=17)
    root: Any = None
    window: Any = None
    try:
        import tkinter as tk

        root = tk.Tk()
        window = PlaygroundWindow(root, controller, display_interval_ms=50)
        root.update_idletasks()
        initial_paused = not window.running and controller.recovery.command_count == 0
        window.cue_var.set("novelty")

        committed_callbacks: list[dict[str, Any]] = []
        redraw = window._on_committed
        pause_invoke_result: Any = None
        pause_invoked_from_commit_callback = False
        pause_invoked_at_count: int | None = None

        def tracked_redraw(state: dict[str, Any], trace: dict[str, Any]) -> None:
            nonlocal pause_invoke_result
            nonlocal pause_invoked_at_count
            nonlocal pause_invoked_from_commit_callback
            committed_callbacks.append(
                {
                    "sequence": int(trace["sequence"]),
                    "state_hash": engine.state_hash(state),
                    "trace_hash": trace["trace_hash"],
                }
            )
            if len(committed_callbacks) == 24:
                # Stop inside the 24th real commit callback.  This prevents one
                # root.update() call from draining a newly-due recurring timer
                # and overshooting the frozen product-clock target.
                pause_invoked_at_count = controller.recovery.command_count
                pause_invoke_result = window.pause_button.invoke()
                pause_invoked_from_commit_callback = True
            redraw(state, trace)

        controller.on_committed = tracked_redraw
        run_invoke_result = window.run_button.invoke()
        deadline = time.monotonic() + 15.0
        while controller.recovery.command_count < 24 and time.monotonic() < deadline:
            root.update()
            time.sleep(0.006)
        if pause_invoked_at_count is None:
            pause_invoked_at_count = controller.recovery.command_count
            pause_invoke_result = window.pause_button.invoke()
        count_at_pause_request = pause_invoked_at_count
        root.update()
        count_after_pause = controller.recovery.command_count
        state_after_pause = engine.state_hash(controller.state)
        for _ in range(2):
            time.sleep(0.065)
            root.update()
        pause_stable = (
            controller.recovery.command_count == count_after_pause
            and engine.state_hash(controller.state) == state_after_pause
        )

        children = list(window.timeline_tree.get_children())
        historical_observed = False
        latest_restored = False
        if len(children) >= 2:
            historical = next(
                (
                    item
                    for item in children
                    if int(window.timeline_tree.item(item, "values")[0]) == 8
                ),
                children[0],
            )
            window.timeline_tree.selection_set(historical)
            window.timeline_tree.event_generate("<<TreeviewSelect>>")
            root.update()
            historical_observed = bool(
                window._is_historical()
                and window.run_button.instate(["disabled"])
                and window.step_button.instate(["disabled"])
            )
            latest = children[-1]
            window.timeline_tree.selection_set(latest)
            window.timeline_tree.event_generate("<<TreeviewSelect>>")
            root.update()
            latest_restored = not window._is_historical()

        latest_trace = controller.last_trace or {}
        visible_text = window.trace_text.get("1.0", "end-1c")
        goals_text = window.goals_text.get("1.0", "end-1c")
        memory_text = window.memory_text.get("1.0", "end-1c")
        visible_surface_checks = {
            "clock_status_visible": "global_tick=" in window.status_var.get()
            and "episode=" in window.status_var.get(),
            "goal_visible": "current_goal=" in goals_text,
            "organism_visible": len(window.state_widgets) == len(engine.STATE_KEYS),
            "all_candidates_visible": len(window.candidate_tree.get_children())
            == len(engine.ACTIONS),
            "prediction_visible": '"prediction"' in visible_text,
            "error_visible": '"prediction_error"' in visible_text,
            "model_update_visible": '"model_update"' in visible_text,
            "memory_update_visible": '"memory_update"' in visible_text,
            "provenance_visible": '"memory_refs"' in visible_text
            and '"provenance_projection"' in visible_text,
            "memory_surface_visible": "episodic" in memory_text
            and "consolidated" in memory_text,
        }
        preclose = {
            "command_count": controller.recovery.command_count,
            "state_hash": engine.state_hash(controller.state),
            "model_hash": _hash(controller.state["model"]),
            "memory_hash": _hash(controller.state["memory"]),
            "goal_hash": _hash(controller.state["current_goal"]),
            "clock_hash": _hash(controller.state["clock"]),
        }
        timeline_rows = len(children)
        window.close()
        window = None
        root = None
        store.close()

        close_command_count = int(preclose["command_count"])
        fresh_hashes: dict[str, Any] = {}
        recovery_hash_match = False
        report = {
            "mode": "real_tk_widget_path",
            "tk_available": True,
            "initial_paused": initial_paused,
            "run_button_invoked": run_invoke_result is not None,
            "run_button_invoke_return": str(run_invoke_result),
            "pause_button_invoked": pause_invoke_result is not None,
            "pause_button_invoke_return": str(pause_invoke_result),
            "pause_invoked_from_commit_callback": pause_invoked_from_commit_callback,
            "scheduler_driven": True,
            "command_count_at_pause_request": count_at_pause_request,
            "command_count": close_command_count,
            "pause_stable_across_two_display_intervals": pause_stable,
            "closed_without_additional_command": close_command_count == count_after_pause,
            "committed_callback_count": len(committed_callbacks),
            "committed_callback_sequences": [item["sequence"] for item in committed_callbacks],
            "visible_redraw_reached_latest": (
                bool(committed_callbacks)
                and committed_callbacks[-1]["sequence"] == count_after_pause
            ),
            "latest_trigger_source": latest_trace.get("trigger_source"),
            "timeline_row_count": timeline_rows,
            "historical_frame_read_only_observed": historical_observed,
            "latest_frame_restored": latest_restored,
            "visible_surface_checks": visible_surface_checks,
            "preclose_hashes": preclose,
            "fresh_recovery_hashes": fresh_hashes,
            "fresh_recovery_hash_match": recovery_hash_match,
            "fresh_recovery_process_boundary": False,
            "fresh_recovery_prepare_pid": os.getpid(),
            "fresh_recovery_probe_pid": None,
            "fresh_recovery_status": "external_probe_required",
        }
        if close_command_count != 24:
            blockers.append(f"real_tk_run_command_count_not_24:{close_command_count}")
        if not pause_invoked_from_commit_callback or count_at_pause_request != 24:
            blockers.append("real_tk_pause_not_invoked_from_24th_commit_callback")
        if latest_trace.get("trigger_source") != "ui_run_button":
            blockers.append("real_tk_run_trigger_source_not_observed")
        if not pause_stable:
            blockers.append("pause_did_not_hold_across_two_display_intervals")
        if not report["closed_without_additional_command"]:
            blockers.append("command_observed_after_window_close")
        blockers.append("fresh_process_probe_receipt_absent")
        if not all(visible_surface_checks.values()):
            blockers.append("required_visible_surface_missing")
        if not historical_observed or not latest_restored:
            blockers.append("historical_timeline_read_only_control_not_observed")
        return report, blockers
    except Exception as exc:
        blockers.append(f"real_tk_widget_path_unavailable_or_failed:{type(exc).__name__}:{exc}")
        try:
            if window is not None:
                window.close()
        except Exception:
            pass
        try:
            if root is not None:
                root.destroy()
        except Exception:
            pass
        store.close()
        diagnostic = _headless_diagnostic_run(database, run_id)
        return {
            "mode": "headless_diagnostic_after_tk_failure",
            "tk_available": False,
            "tk_failure": f"{type(exc).__name__}: {exc}",
            "diagnostic": diagnostic,
        }, blockers


def _baseline_actions_from_initial_state_and_commands(
    database: Path, run_id: str
) -> dict[str, Any]:
    """Recompute shortcut outputs without selecting from the traces table."""

    connection = sqlite3.connect(str(database))
    try:
        row = connection.execute(
            "SELECT run_meta_json, initial_state_json FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"missing run for baseline recomputation: {run_id}")
        run_meta = json.loads(row[0])
        state = json.loads(row[1])
        command_rows = connection.execute(
            "SELECT command_json FROM commands WHERE run_id = ? ORDER BY sequence",
            (run_id,),
        ).fetchall()
    finally:
        connection.close()
    actions: list[str] = []
    candidate_hashes: list[str] = []
    for command_row in command_rows:
        command = json.loads(command_row[0])
        baseline = run_cue_clock_fsm_baseline(state, command, run_meta)
        actions.append(str(baseline["selected_action"]))
        candidate_hashes.append(_hash(baseline["candidates"]))
        # State advancement uses the sole canonical reducer but the shortcut
        # action calculation above remains independent and trace-free.
        state = engine.compute_step(state, command, run_meta).next_state
    return {
        "actions": actions,
        "candidate_hashes": candidate_hashes,
        "command_count": len(command_rows),
        "trace_rows_read": 0,
    }


def _load_trace_payloads(database: Path, run_id: str) -> list[dict[str, Any]]:
    connection = sqlite3.connect(str(database))
    try:
        rows = connection.execute(
            "SELECT trace_json FROM traces WHERE run_id = ? ORDER BY sequence",
            (run_id,),
        ).fetchall()
    finally:
        connection.close()
    return [json.loads(row[0]) for row in rows]


def _build_baseline_report(
    recovered: Any, manifest_hash: str, database: str | Path
) -> dict[str, Any]:
    baseline_rows: list[dict[str, Any]] = []
    action_matches = 0
    organism_matches = 0
    for index, trace in enumerate(recovered.traces):
        predecision = recovered.frames[index].state
        candidate = run_cue_clock_fsm_baseline(
            predecision, trace["command"], recovered.run_meta
        )
        next_state = recovered.frames[index + 1].state
        action_match = candidate["selected_action"] == trace["selected_action"]
        organism_match = (
            _json(candidate["next_organism_from_public_table"])
            == _json(next_state["organism"])
        )
        action_matches += int(action_match)
        organism_matches += int(organism_match)
        baseline_rows.append(
            {
                "sequence": trace["sequence"],
                "input_state_hash": _hash(predecision),
                "command_hash": trace["command_hash"],
                "baseline_selected_action": candidate["selected_action"],
                "candidate_selected_action": trace["selected_action"],
                "selected_action_match": action_match,
                "organism_transition_match": organism_match,
                "baseline_context_id": candidate["context_id"],
            }
        )
    count = len(baseline_rows)
    echo = run_stored_trace_echo_control(recovered.traces)
    tree = ast.parse(inspect.getsource(run_cue_clock_fsm_baseline))
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } | {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    prohibited = sorted(
        {"compute_step", "_score_candidate", "compute_trace_hash"} & called_names
    )
    source_database = Path(database).resolve()
    original_actions = [row["baseline_selected_action"] for row in baseline_rows]
    original_trace_hash = _hash(recovered.traces)
    with tempfile.TemporaryDirectory(prefix="ego-v1-baseline-controls-") as temporary:
        deleted_copy = Path(temporary) / "trace-deleted.sqlite3"
        shutil.copy2(source_database, deleted_copy)
        connection = sqlite3.connect(str(deleted_copy))
        try:
            deleted_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM traces WHERE run_id = ?", (recovered.run_id,)
                ).fetchone()[0]
            )
            connection.execute("DELETE FROM traces WHERE run_id = ?", (recovered.run_id,))
            connection.commit()
        finally:
            connection.close()
        deleted_baseline = _baseline_actions_from_initial_state_and_commands(
            deleted_copy, recovered.run_id
        )
        deleted_traces = _load_trace_payloads(deleted_copy, recovered.run_id)
        deleted_echo = run_stored_trace_echo_control(deleted_traces)

        tampered_copy = Path(temporary) / "stored-action-tampered.sqlite3"
        shutil.copy2(source_database, tampered_copy)
        connection = sqlite3.connect(str(tampered_copy))
        try:
            tamper_mutation = _tamper_stored_action(connection, recovered.run_id)
            connection.commit()
        finally:
            connection.close()
        tampered_baseline = _baseline_actions_from_initial_state_and_commands(
            tampered_copy, recovered.run_id
        )
        tampered_traces = _load_trace_payloads(tampered_copy, recovered.run_id)
        tampered_echo = run_stored_trace_echo_control(tampered_traces)

    shared_control_inputs = [
        _artifact_ref(source_database),
        _semantic_ref("baseline_control/original_actions", original_actions),
    ]
    deletion_control = {
        **_evidence_provenance(
            _build_baseline_report,
            input_artifacts=shared_control_inputs
            + [_semantic_ref("baseline_control/delete_all_stored_traces", {"deleted": deleted_count})],
            run_id=recovered.run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=[str(trace["episode_id"]) for trace in recovered.traces],
            context_ids=[str(trace["command_hash"]) for trace in recovered.traces],
            aggregation_rule="delete_all_stored_traces_then_recompute_baseline_from_initial_state_and_commands",
            manifest_hash=manifest_hash,
        ),
        "mutation": {"deleted_trace_rows": deleted_count},
        "independent_baseline": {
            "recomputable": deleted_baseline["command_count"] == count,
            "bit_identical": deleted_baseline["actions"] == original_actions,
            "trace_rows_read": deleted_baseline["trace_rows_read"],
            "selected_actions_hash": _hash(deleted_baseline["actions"]),
        },
        "echo_control": {
            "recomputable": len(deleted_traces) == count and count > 0,
            "bit_identical": _hash(deleted_traces) == original_trace_hash,
            "visible_row_count": deleted_echo["visible_row_count"],
            "dependency": "stored_trace_rows_required",
        },
    }
    tamper_control = {
        **_evidence_provenance(
            _build_baseline_report,
            input_artifacts=shared_control_inputs
            + [_semantic_ref("baseline_control/stored_action_rehashed_mutation", tamper_mutation)],
            run_id=recovered.run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=[str(trace["episode_id"]) for trace in recovered.traces],
            context_ids=[str(trace["command_hash"]) for trace in recovered.traces],
            aggregation_rule="rehash_tampered_stored_action_then_compare_independent_baseline_and_echo",
            manifest_hash=manifest_hash,
        ),
        "mutation": tamper_mutation,
        "independent_baseline": {
            "recomputable": tampered_baseline["command_count"] == count,
            "bit_identical": tampered_baseline["actions"] == original_actions,
            "trace_rows_read": tampered_baseline["trace_rows_read"],
            "selected_actions_hash": _hash(tampered_baseline["actions"]),
        },
        "echo_control": {
            "recomputable": tampered_echo["visible_row_count"] == count,
            "bit_identical": _hash(tampered_traces) == original_trace_hash,
            "visible_row_count": tampered_echo["visible_row_count"],
            "tampered_action_visible": _hash(tampered_traces) != original_trace_hash,
        },
    }
    return {
        "schema_version": "ego.life_playground.baseline_comparison.v1",
        **_evidence_provenance(
            _build_baseline_report,
            input_artifacts=[
                _artifact_ref(source_database),
                _semantic_ref("recomputed_run_traces", recovered.traces),
            ],
            run_id=recovered.run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=[str(item["episode_id"]) for item in recovered.traces],
            context_ids=[str(item["command_hash"]) for item in recovered.traces],
            aggregation_rule="exact_match_rate_and_actual_deletion_tamper_controls",
            manifest_hash=manifest_hash,
        ),
        "baseline": {
            "role": "baseline",
            **_evidence_provenance(
                run_cue_clock_fsm_baseline,
                input_artifacts=[
                    _artifact_ref(source_database),
                    _semantic_ref("ordered_predecision_baseline_rows", baseline_rows),
                ],
                run_id=recovered.run_id,
                seed=int(recovered.run_meta["seed"]),
                episode_ids=[str(item["episode_id"]) for item in recovered.traces],
                context_ids=[str(item["command_hash"]) for item in recovered.traces],
                aggregation_rule="independent_baseline_over_each_ordered_predecision_state_and_command",
                manifest_hash=manifest_hash,
            ),
            "call_count": count,
            "prohibited_live_reducer_calls": prohibited,
            "selected_action_match_count": action_matches,
            "selected_action_match_rate": 0.0 if not count else action_matches / count,
            "organism_transition_match_count": organism_matches,
            "organism_transition_match_rate": 0.0 if not count else organism_matches / count,
            "rows": baseline_rows,
        },
        "post_hoc_appearance_control": echo,
        "stored_trace_deletion_control": deletion_control,
        "stored_selected_action_tamper_control": tamper_control,
        "included_post_hoc_control_in_candidate_baseline_score": False,
        "verdict_ceiling": "SHORTCUT_BASELINE_REMAINS_PLAUSIBLE_OR_STRONGER_CEILING",
    }


def _build_leakage_report(recovered: Any, manifest_hash: str) -> dict[str, Any]:
    input_scans: list[dict[str, Any]] = []
    trace_scans: list[dict[str, Any]] = []
    for index, trace in enumerate(recovered.traces):
        input_scans.append(
            {
                "sequence": trace["sequence"],
                "scan": scan_for_leakage(
                    {
                        "state": recovered.frames[index].state,
                        "command": trace["command"],
                    },
                    inject_positive_control=False,
                ),
            }
        )
        trace_scans.append(
            {
                "sequence": trace["sequence"],
                "scan": scan_for_leakage(
                    {"trace": trace}, inject_positive_control=False
                ),
            }
        )
    positive = scan_for_leakage(
        {
            "state": recovered.frames[0].state,
            "command": recovered.traces[0]["command"],
        },
        inject_positive_control=True,
    )
    run_episode_ids = [str(item["episode_id"]) for item in recovered.traces]
    run_context_ids = [str(item["command_hash"]) for item in recovered.traces]
    positive.update(
        _evidence_provenance(
            scan_for_leakage,
            input_artifacts=positive["input_artifacts"],
            run_id=recovered.run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=run_episode_ids,
            context_ids=run_context_ids,
            aggregation_rule="injected_known_selected_action_positive_control_must_fire",
            manifest_hash=manifest_hash,
        )
    )
    for record in input_scans + trace_scans:
        record["scan"].update(
            _evidence_provenance(
                scan_for_leakage,
                input_artifacts=record["scan"]["input_artifacts"],
                run_id=recovered.run_id,
                seed=int(recovered.run_meta["seed"]),
                episode_ids=run_episode_ids,
                context_ids=[str(record["sequence"])],
                aggregation_rule="one_contextual_leakage_schema_scan",
                manifest_hash=manifest_hash,
            )
        )
    clean_findings = [
        finding
        for record in input_scans + trace_scans
        for finding in record["scan"]["findings"]
    ]
    blockers: list[str] = []
    if clean_findings:
        blockers.append("leakage_scanner_clean_run_findings_nonempty")
    if not positive["positive_control_fired"]:
        blockers.append("leakage_positive_control_did_not_fire")
    return {
        "schema_version": "ego.life_playground.leakage_report.v1",
        **_evidence_provenance(
            _build_leakage_report,
            input_artifacts=[
                _semantic_ref(
                    "predecision_states_commands_and_postdecision_traces",
                    recovered.traces,
                )
            ],
            run_id=recovered.run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=run_episode_ids,
            context_ids=run_context_ids,
            aggregation_rule="all_contextual_clean_scans_empty_and_injected_control_fires",
            manifest_hash=manifest_hash,
        ),
        "input_scans": input_scans,
        "postdecision_trace_schema_scans": trace_scans,
        "positive_control": positive,
        "clean_finding_count": len(clean_findings),
        "blocking_failures": blockers,
    }


def _route_firewall_report(
    repo_root: Path,
    *,
    run_id: str | None = None,
    seed: int | None = None,
    episode_ids: Iterable[str] = (),
    context_ids: Iterable[str] = (),
    manifest_hash: str | None = None,
) -> dict[str, Any]:
    path = repo_root / "docs" / "PROGRAM_STATE_UNIFIED.yaml"
    checks: dict[str, bool] = {}
    error: str | None = None
    authority: dict[str, Any] = {}
    try:
        import yaml

        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        authority = dict(document["route_guard"]["v1_ready_authority"])
        checks = {
            "enabled_false": authority.get("enabled") is False,
            "default_enabled_false": authority.get("default_enabled") is False,
            "mainline_connected_false": authority.get("mainline_connected") is False,
            "runtime_authority_none": authority.get("runtime_authority") == "none",
            "science_weight_zero": authority.get("science_weight") == 0,
            "remote_anchor_false": authority.get("remote_anchor") is False,
        }
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    return {
        **_evidence_provenance(
            _route_firewall_report,
            input_artifacts=[_artifact_ref(path)] if path.is_file() else [
                _semantic_ref("missing_program_state_path", str(path))
            ],
            run_id=run_id,
            seed=seed,
            episode_ids=episode_ids,
            context_ids=context_ids,
            aggregation_rule="all_v1_ready_machine_authority_firewall_fields_exact",
            manifest_hash=manifest_hash,
        ),
        "authority_subset": {
            key: authority.get(key)
            for key in (
                "enabled",
                "default_enabled",
                "mainline_connected",
                "runtime_authority",
                "science_weight",
                "remote_anchor",
            )
        },
        "checks": checks,
        "error": error,
        "passed": error is None and bool(checks) and all(checks.values()),
    }


def _code_surface_report(
    repo_root: Path,
    database: Path,
    *,
    run_id: str | None = None,
    seed: int | None = None,
    episode_ids: Iterable[str] = (),
    context_ids: Iterable[str] = (),
    manifest_hash: str | None = None,
) -> dict[str, Any]:
    forbidden_roots = {
        "anthropic",
        "httpx",
        "openai",
        "requests",
        "socket",
        "urllib3",
        "websockets",
    }
    imported: list[dict[str, str]] = []
    reducer_definitions: list[str] = []
    parse_errors: list[str] = []
    for relative in PRODUCT_PATHS[:-1]:
        path = repo_root / relative
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except Exception as exc:
            parse_errors.append(f"{relative}:{type(exc).__name__}:{exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "compute_step":
                reducer_definitions.append(f"{relative}:{node.lineno}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.append({"path": relative, "module": alias.name})
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append({"path": relative, "module": node.module})
    forbidden = [
        item
        for item in imported
        if item["module"].split(".", 1)[0] in forbidden_roots
    ]
    connection = sqlite3.connect(str(database))
    try:
        tables = sorted(
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            ).fetchall()
        )
    finally:
        connection.close()
    expected_tables = ["commands", "runs", "traces"]
    checks = {
        "one_canonical_reducer_definition": len(reducer_definitions) == 1,
        "no_forbidden_network_or_llm_import": forbidden == [],
        "all_product_python_parses": parse_errors == [],
        "only_canonical_durable_tables": tables == expected_tables,
    }
    return {
        **_evidence_provenance(
            _code_surface_report,
            input_artifacts=[
                _semantic_ref(
                    "exact_six_file_product_manifest",
                    build_product_code_manifest(repo_root),
                ),
                _artifact_ref(database),
            ],
            run_id=run_id,
            seed=seed,
            episode_ids=episode_ids,
            context_ids=context_ids,
            aggregation_rule="bounded_ast_and_sqlite_surface_checks_all_true",
            manifest_hash=manifest_hash,
        ),
        "reducer_definitions": reducer_definitions,
        "forbidden_imports": forbidden,
        "parse_errors": parse_errors,
        "sqlite_tables": tables,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _continuity_report(
    recovered: Any, manifest_hash: str | None = None
) -> dict[str, Any]:
    traces = list(recovered.traces)
    episode_indices = sorted({int(trace["episode_index"]) for trace in traces})
    boundaries: list[dict[str, Any]] = []
    carried_unfinished = False
    for trace in traces:
        if trace["episode_transition"]["applied"]:
            previous = recovered.frames[int(trace["sequence"]) - 1].state
            unfinished = previous["current_goal"]["status"] == "active"
            goal_carried = _json(previous["current_goal"]) == _json(trace["goal_before"])
            carried_unfinished = carried_unfinished or (unfinished and goal_carried)
            boundaries.append(
                {
                    "sequence": trace["sequence"],
                    "from_episode_index": trace["episode_transition"]["from_episode_index"],
                    "to_episode_index": trace["episode_transition"]["to_episode_index"],
                    "rollover_before_action": trace["action_episode"]["episode_index"]
                    == trace["episode_transition"]["to_episode_index"],
                    "carry_checks": trace["episode_transition"]["carry_checks"],
                    "unfinished_goal_before_boundary": unfinished,
                    "goal_carried_into_decision": goal_carried,
                }
            )
    goal_context_checks = [
        trace["context_key"]
        == f"{trace['cue']}|{trace['goal_before']['state_variable'] or 'homeostasis'}"
        and all("current_goal_deficit_reduction" in item for item in trace["candidates"])
        for trace in traces
    ]
    checks = {
        "exact_24_ticks": recovered.command_count == 24,
        "episode_indices_0_1_2": episode_indices == [0, 1, 2],
        "two_rollovers": len(boundaries) == 2,
        "rollover_before_action": all(item["rollover_before_action"] for item in boundaries),
        "all_causal_carry_checks": all(
            all(item["carry_checks"].values()) for item in boundaries
        ),
        "unfinished_goal_carried_across_boundary": carried_unfinished,
        "goal_enters_context_and_score": bool(goal_context_checks)
        and all(goal_context_checks),
    }
    return {
        **_evidence_provenance(
            _continuity_report,
            input_artifacts=[_semantic_ref("recomputed_continuity_frames", traces)],
            run_id=recovered.run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=[str(trace["episode_id"]) for trace in traces],
            context_ids=[str(trace["command_hash"]) for trace in traces],
            aggregation_rule="all_frozen_clock_goal_and_boundary_checks_true",
            manifest_hash=manifest_hash,
        ),
        "episode_indices": episode_indices,
        "boundaries": boundaries,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    payload = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    temporary.write_bytes(payload)
    temporary.replace(path)


_FRESH_RECEIPT_ABSENT = "fresh_process_probe_receipt_absent"
_FRESH_RECOVERY_HARD_FAILURE = (
    "hard_requirement_failed:fresh_recovery_all_causal_hashes_match"
)
_FRESH_REPLAY_HARD_FAILURE = (
    "hard_requirement_failed:fresh_replay_and_all_tamper_controls_fail_closed"
)
_NATURAL_MEMORY_BLOCKERS = [
    "hard_requirement_failed:paired_interventions_computed_without_blocker",
    "natural_checkpoint_memory_bias_zero",
]
_REQUIRED_TAMPER_CONTROLS = (
    "stored_action_rehashed",
    "command_payload",
    "initial_state",
    "code_path_hash",
)


def _verdict_from_computed_blockers(blockers: Sequence[str]) -> str:
    ordered = list(blockers)
    if not ordered:
        return "local_v1_continuity_product_acceptance"
    if ordered == _NATURAL_MEMORY_BLOCKERS:
        return "continuity_only__memory_conditioning_not_observed"
    return "v1_continuity_product_acceptance_blocked"


def _aggregate_finalized_replay_state(
    prepared_blockers: Sequence[str],
    replay_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Remove only the external-receipt blocker; preserve computed tamper failures."""

    replay_blockers = replay_report.get("blocking_failures", [])
    if not isinstance(replay_blockers, list) or not all(
        isinstance(item, str) for item in replay_blockers
    ):
        replay_blockers = ["replay_blocking_failures_schema_invalid"]
    remaining_replay = list(
        dict.fromkeys(
            item for item in replay_blockers if item != _FRESH_RECEIPT_ABSENT
        )
    )
    controls = replay_report.get("tamper_controls")
    if not isinstance(controls, Mapping):
        remaining_replay.append("tamper_controls_missing")
    else:
        for control_name in _REQUIRED_TAMPER_CONTROLS:
            control = controls.get(control_name)
            if not isinstance(control, Mapping) or control.get("failed_closed") is not True:
                failure = f"tamper_control_did_not_fail_closed:{control_name}"
                if failure not in remaining_replay:
                    remaining_replay.append(failure)
    replay_controls_passed = remaining_replay == []
    removable = {_FRESH_RECEIPT_ABSENT, _FRESH_RECOVERY_HARD_FAILURE}
    if replay_controls_passed:
        removable.add(_FRESH_REPLAY_HARD_FAILURE)
    blockers = list(
        dict.fromkeys(item for item in prepared_blockers if item not in removable)
    )
    if not replay_controls_passed and _FRESH_REPLAY_HARD_FAILURE not in blockers:
        blockers.append(_FRESH_REPLAY_HARD_FAILURE)
    for replay_blocker in remaining_replay:
        if replay_blocker not in blockers:
            blockers.append(replay_blocker)
    return {
        "replay_blocking_failures": remaining_replay,
        "fresh_replay_and_all_tamper_controls_fail_closed": replay_controls_passed,
        "blocking_failures": blockers,
        "verdict": _verdict_from_computed_blockers(blockers),
    }


def _embed_report_input(
    report: dict[str, Any], artifact_path: Path, label: str, value: Any
) -> dict[str, Any]:
    scope = _EvidenceInputScope(artifact_path)
    scope.evidence_inputs.update(deepcopy(report.get("evidence_inputs", {})))
    ref = scope.add(label, value)
    report["evidence_inputs"] = scope.evidence_inputs
    return ref


def _resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError("JSON pointer must be empty or start with /")
    value = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def audit_generated_artifact_inputs(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir).resolve()
    report_names = (
        "result.json",
        "failure_manifest.json",
        "product_trigger_receipt.json",
        "baseline_comparison.json",
        "ablation_report.json",
        "replay_report.json",
        "leakage_report.json",
    )
    failures: list[str] = []
    checked = 0
    for report_name in report_names:
        report_path = output / report_name
        document = json.loads(report_path.read_text(encoding="utf-8"))

        def walk(value: Any, location: str) -> None:
            nonlocal checked
            if isinstance(value, Mapping):
                refs = value.get("input_artifacts", [])
                if isinstance(refs, list) and refs and all(
                    isinstance(item, Mapping) for item in refs
                ):
                    for index, ref in enumerate(refs):
                        checked += 1
                        ref_location = f"{location}/input_artifacts/{index}"
                        raw_path = str(ref.get("path", ""))
                        if raw_path.startswith(("semantic://", "inline://")):
                            failures.append(f"pseudo_path:{ref_location}:{raw_path}")
                            continue
                        path = Path(raw_path)
                        if not path.is_absolute() or not path.is_file():
                            failures.append(f"unresolvable_path:{ref_location}:{raw_path}")
                            continue
                        try:
                            mode = ref.get("content_mode")
                            if mode == "raw_file":
                                if ref.get("json_pointer") is not None:
                                    raise ValueError("raw_file ref has non-null JSON pointer")
                                payload = path.read_bytes()
                            elif mode == "canonical_json_pointer":
                                target = json.loads(path.read_text(encoding="utf-8"))
                                pointed = _resolve_json_pointer(
                                    target, str(ref.get("json_pointer", ""))
                                )
                                payload = _json(pointed).encode("utf-8")
                            else:
                                raise ValueError(f"unknown content_mode: {mode}")
                            if hashlib.sha256(payload).hexdigest() != ref.get("sha256"):
                                raise ValueError("sha256 mismatch")
                            if len(payload) != ref.get("byte_count"):
                                raise ValueError("byte_count mismatch")
                        except Exception as exc:
                            failures.append(
                                f"ref_validation_failed:{ref_location}:{type(exc).__name__}:{exc}"
                            )
                for key, item in value.items():
                    walk(item, f"{location}/{key}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, f"{location}/{index}")

        walk(document, report_name)
    manifest_hash = build_product_code_manifest(ROOT)["manifest_hash"]
    return {
        "schema_version": "ego.life_playground.evidence_input_audit.v1",
        **_evidence_provenance(
            audit_generated_artifact_inputs,
            input_artifacts=[
                _artifact_ref(output / name)
                for name in report_names
                if name != "result.json"
            ],
            run_id=None,
            seed=None,
            context_ids=[str(output)],
            aggregation_rule="open_every_report_resolve_every_verifier_ref_and_recompute_hash_and_bytes",
            manifest_hash=manifest_hash,
        ),
        "checked_ref_count": checked,
        "blocking_failures": failures,
        "zero_pseudo_or_unverifiable_refs": failures == [],
    }


def _run_verification_in(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACT_NAMES:
        path = output / name
        if path.exists():
            path.unlink()

    manifest = build_product_code_manifest(ROOT)
    database = output / "continuity.sqlite3"
    trace_path = output / "trace.jsonl"
    run_id = "ego-v1-continuity-frozen-seed17"
    trigger_report, ui_blockers = _drive_real_tk_run(database, run_id)

    store = SQLiteEventStore(database)
    try:
        recovered = store.recover_run(run_id)
        store.export_run(run_id, trace_path)
    finally:
        store.close()

    episode_ids = [str(trace["episode_id"]) for trace in recovered.traces]
    command_context_ids = [str(trace["command_hash"]) for trace in recovered.traces]
    with evidence_input_scope(output / "ablation_report.json") as ablation_scope:
        checkpoint = select_intervention_checkpoint(
            list(recovered.frames), minimum_global_tick=16
        )
        ablation = run_paired_interventions(
            checkpoint["state"], recovered.run_meta, cue="novelty"
        )
        ablation["product_code_manifest_hash"] = manifest["manifest_hash"]
        _attach_scope_inputs(ablation, ablation_scope)
    with evidence_input_scope(output / "replay_report.json") as replay_scope:
        replay = run_replay_checks(database, run_id)
        replay["product_code_manifest_hash"] = manifest["manifest_hash"]
        _attach_scope_inputs(replay, replay_scope)
    with evidence_input_scope(output / "baseline_comparison.json") as baseline_scope:
        baseline = _build_baseline_report(
            recovered, manifest["manifest_hash"], database
        )
        _attach_scope_inputs(baseline, baseline_scope)
    with evidence_input_scope(output / "leakage_report.json") as leakage_scope:
        leakage = _build_leakage_report(recovered, manifest["manifest_hash"])
        _attach_scope_inputs(leakage, leakage_scope)
    with evidence_input_scope(output / "product_trigger_receipt.json") as trigger_scope:
        continuity = _continuity_report(recovered, manifest["manifest_hash"])
        atomicity = _run_atomicity_control(database, run_id, manifest["manifest_hash"])
        route_firewall = _route_firewall_report(
            ROOT,
            run_id=run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=episode_ids,
            context_ids=command_context_ids,
            manifest_hash=manifest["manifest_hash"],
        )
        code_surface = _code_surface_report(
            ROOT,
            database,
            run_id=run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=episode_ids,
            context_ids=command_context_ids,
            manifest_hash=manifest["manifest_hash"],
        )
        trigger_report.update({
            "schema_version": "ego.life_playground.product_trigger_receipt.v1",
            **_evidence_provenance(
                _drive_real_tk_run,
                input_artifacts=[_artifact_ref(database), _artifact_ref(trace_path)],
                run_id=run_id,
                seed=int(recovered.run_meta["seed"]),
                episode_ids=episode_ids,
                context_ids=command_context_ids,
                checkpoint_ids=[checkpoint["checkpoint_id"]],
                aggregation_rule="actual_widget_scheduler_commit_callback_redraw_pause_close_fresh_process_recovery",
                manifest_hash=manifest["manifest_hash"],
            ),
            "engine_code_path_hash": recovered.run_meta["code_path_hash"],
            "continuity_report": continuity,
            "route_firewall": route_firewall,
            "code_surface_report": code_surface,
            "atomic_second_write_control": atomicity,
            "fresh_process_probe_challenge": replay["fresh_process_protocol"]["request"]["challenge"],
        })
        _attach_scope_inputs(trigger_report, trigger_scope)

    ui_mode = trigger_report.get("mode") == "real_tk_widget_path"
    visible_checks = trigger_report.get("visible_surface_checks", {})
    hard_requirements = {
        "paused_default_and_route_firewall_closed": bool(
            ui_mode
            and trigger_report.get("initial_paused")
            and route_firewall["passed"]
        ),
        "real_run_widget_to_ui_run_button_commit_and_redraw": bool(
            ui_mode
            and trigger_report.get("run_button_invoked")
            and trigger_report.get("pause_button_invoked")
            and trigger_report.get("pause_invoked_from_commit_callback")
            and trigger_report.get("command_count_at_pause_request") == 24
            and trigger_report.get("latest_trigger_source") == "ui_run_button"
            and trigger_report.get("committed_callback_count") == 24
            and trigger_report.get("visible_redraw_reached_latest")
        ),
        "twenty_four_ticks_three_episodes_two_rollovers": continuity["passed"],
        "required_state_goal_candidate_update_provenance_surfaces_visible": bool(
            visible_checks and all(visible_checks.values())
        ),
        "unfinished_goal_carry_and_scoring_observed": bool(
            continuity["checks"]["unfinished_goal_carried_across_boundary"]
            and continuity["checks"]["goal_enters_context_and_score"]
        ),
        "pause_and_close_stop_product_clock": bool(
            trigger_report.get("pause_stable_across_two_display_intervals")
            and trigger_report.get("closed_without_additional_command")
        ),
        "fresh_recovery_all_causal_hashes_match": bool(
            trigger_report.get("fresh_recovery_hash_match")
            and trigger_report.get("fresh_recovery_process_boundary")
            and replay["fresh_recovery"]["recovered"]
            and replay["fresh_recovery"]["process_boundary"]
            and replay["fresh_recovery"]["final_hashes_match_parent"]
        ),
        "historical_timeline_is_read_only_and_latest_restores": bool(
            trigger_report.get("historical_frame_read_only_observed")
            and trigger_report.get("latest_frame_restored")
        ),
        "paired_interventions_computed_without_blocker": ablation["blocking_failures"] == [],
        "second_sqlite_write_failure_is_atomic_and_no_redraw": atomicity["passed"],
        "fresh_replay_and_all_tamper_controls_fail_closed": replay["blocking_failures"] == [],
        "independent_baseline_and_positive_leakage_control_called": bool(
            baseline["baseline"]["call_count"] == 24
            and baseline["baseline"]["prohibited_live_reducer_calls"] == []
            and leakage["positive_control"]["positive_control_fired"]
            and leakage["blocking_failures"] == []
        ),
        "one_reducer_no_forbidden_import_or_second_durable_truth": code_surface["passed"],
    }

    blockers: list[str] = list(ui_blockers)
    blockers.extend(
        f"hard_requirement_failed:{name}"
        for name, passed in hard_requirements.items()
        if not passed
    )
    blockers.extend(ablation["blocking_failures"])
    blockers.extend(replay["blocking_failures"])
    blockers.extend(leakage["blocking_failures"])
    if not route_firewall["passed"]:
        blockers.append("v1_route_firewall_readback_failed")
    if not code_surface["passed"]:
        blockers.append("product_code_surface_check_failed")
    blockers = list(dict.fromkeys(blockers))

    verdict = _verdict_from_computed_blockers(blockers)

    _write_json(output / "product_trigger_receipt.json", trigger_report)
    _write_json(output / "baseline_comparison.json", baseline)
    _write_json(output / "ablation_report.json", ablation)
    _write_json(output / "replay_report.json", replay)
    _write_json(output / "leakage_report.json", leakage)
    (output / "claim_ceiling.txt").write_bytes(
        (CLAIM_CEILING + "\n").encode("utf-8")
    )

    failure_manifest = {
        "schema_version": "ego.life_playground.failure_manifest.v1",
        "evidence_inputs": {},
        **_evidence_provenance(
            _run_verification_in,
            input_artifacts=[_artifact_ref(database), _artifact_ref(trace_path)],
            run_id=run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=episode_ids,
            context_ids=command_context_ids + [ablation["observation_id"]],
            checkpoint_ids=[checkpoint["checkpoint_id"]],
            aggregation_rule="ordered_union_of_false_hard_requirements_and_computed_subreport_blockers",
            manifest_hash=manifest["manifest_hash"],
        ),
        "checkpoint_id": checkpoint["checkpoint_id"],
        "blocking_failures": blockers,
    }
    _write_json(output / "failure_manifest.json", failure_manifest)

    evidence_paths = [
        database,
        trace_path,
        output / "product_trigger_receipt.json",
        output / "baseline_comparison.json",
        output / "ablation_report.json",
        output / "replay_report.json",
        output / "leakage_report.json",
        output / "failure_manifest.json",
        output / "claim_ceiling.txt",
    ]
    result = {
        "schema_version": "ego.life_playground.v1_continuity_result.v1",
        "task_id": "EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A",
        "evidence_inputs": {},
        **_evidence_provenance(
            run_verification,
            input_artifacts=[_artifact_ref(path) for path in evidence_paths],
            run_id=run_id,
            seed=int(recovered.run_meta["seed"]),
            episode_ids=episode_ids,
            context_ids=command_context_ids + [ablation["observation_id"]],
            checkpoint_ids=[checkpoint["checkpoint_id"]],
            aggregation_rule="accept_only_if_every_computed_hard_requirement_true_and_blocking_failures_empty",
            manifest_hash=manifest["manifest_hash"],
        ),
        "context_summary": {
            "intervention_checkpoint_id": checkpoint["checkpoint_id"],
            "intervention_observation_id": ablation["observation_id"],
        },
        "engine_code_path_hash": recovered.run_meta["code_path_hash"],
        "product_code_manifest": manifest,
        "hard_requirements": hard_requirements,
        "blocking_failures": blockers,
        "verdict": verdict,
        "enabled": False,
        "default_enabled": False,
        "mainline_connected": False,
        "runtime_authority": "none",
        "science_weight": 0,
        "remote_anchor": False,
        "claim_ceiling": CLAIM_CEILING,
        "selection_level_shaping_observed": ablation["selection_level_shaping_observed"],
    }
    _write_json(output / "result.json", result)
    evidence_audit = audit_generated_artifact_inputs(output)
    if evidence_audit["blocking_failures"]:
        raise RuntimeError(
            "generated evidence input audit failed: "
            + "; ".join(evidence_audit["blocking_failures"])
        )
    result["evidence_input_audit"] = evidence_audit
    _write_json(output / "result.json", result)
    return result


def run_verification(
    output_dir: str | Path,
    *,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    """Execute the frozen product run and aggregate only callable checks."""

    if write_artifacts:
        return _run_verification_in(Path(output_dir).resolve())
    with tempfile.TemporaryDirectory(prefix="ego-v1-verification-") as temporary:
        return _run_verification_in(Path(temporary))


def finalize_verification(
    output_dir: str | Path, probe_receipt: str | Path | Mapping[str, Any]
) -> dict[str, Any]:
    """Bind an externally produced probe receipt into the prepared artifact set."""

    output = Path(output_dir).resolve()
    replay_path = output / "replay_report.json"
    trigger_path = output / "product_trigger_receipt.json"
    failure_path = output / "failure_manifest.json"
    result_path = output / "result.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    trigger = json.loads(trigger_path.read_text(encoding="utf-8"))
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if isinstance(probe_receipt, Mapping):
        raise TypeError("production finalization requires a persisted receipt path")
    receipt_path = Path(probe_receipt).resolve()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    request = replay["fresh_process_protocol"]["request"]
    attestation = _perform_named_pipe_attestation(request, receipt, receipt_path)
    validation = validate_fresh_process_probe_receipt(request, receipt, attestation)
    if not validation["valid"]:
        raise ValueError(
            "fresh-process probe receipt rejected: "
            + ",".join(validation["blocking_failures"])
        )

    request_ref = _embed_report_input(
        replay, replay_path, "finalize/fresh_process_probe_request", request
    )
    receipt_ref = _embed_report_input(
        replay, replay_path, "finalize/fresh_process_probe_receipt", receipt
    )
    attestation_ref = _embed_report_input(
        replay, replay_path, "finalize/live_named_pipe_os_attestation", attestation
    )
    validation_report = {
        "schema_version": "ego.life_playground.fresh_process_probe_validation.v1",
        **_evidence_provenance(
            finalize_verification,
            input_artifacts=[
                _artifact_ref(Path(request["database_path"])),
                request_ref,
                receipt_ref,
                attestation_ref,
            ],
            run_id=str(request["run_id"]),
            seed=int(replay["seed"]),
            episode_ids=replay["episode_ids"],
            context_ids=[str(request["challenge"])],
            aggregation_rule="challenge_db_run_pid_recovery_hashes_and_post_ack_exit_zero_must_match",
            manifest_hash=replay["product_code_manifest_hash"],
        ),
        "os_attestation": attestation,
        **validation,
    }
    replay["fresh_process_protocol"] = {
        "request": request,
        "receipt": receipt,
        "validation": validation_report,
    }
    replay["fresh_recovery"] = {
        "status": "external_probe_validated",
        **_evidence_provenance(
            finalize_verification,
            input_artifacts=[
                _artifact_ref(Path(request["database_path"])),
                request_ref,
                receipt_ref,
                attestation_ref,
            ],
            run_id=str(request["run_id"]),
            seed=int(replay["seed"]),
            episode_ids=replay["episode_ids"],
            context_ids=[str(request["challenge"])],
            aggregation_rule="external_probe_receipt_hashes_and_post_ack_exit_zero_validated",
            manifest_hash=replay["product_code_manifest_hash"],
        ),
        "recovered": True,
        "command_count": receipt["command_count"],
        "prepare_pid": request["prepare_pid"],
        "probe_pid_claimed": receipt["probe_pid_claimed"],
        "probe_pid_observed": attestation["server_pid"],
        "finalizer_pid": attestation["finalizer_pid"],
        "probe_exit_observed": attestation["probe_exit_observed"],
        "probe_exit_code": attestation["probe_exit_code"],
        "no_orphan": attestation["no_orphan"],
        "process_boundary": validation["process_boundary"],
        "final_hashes_match_parent": True,
        **receipt["hashes"],
    }
    finalized_replay_state = _aggregate_finalized_replay_state(
        result["blocking_failures"], replay
    )
    replay["blocking_failures"] = finalized_replay_state[
        "replay_blocking_failures"
    ]
    _write_json(replay_path, replay)

    trigger_request_ref = _embed_report_input(
        trigger, trigger_path, "finalize/fresh_process_probe_request", request
    )
    trigger_receipt_ref = _embed_report_input(
        trigger, trigger_path, "finalize/fresh_process_probe_receipt", receipt
    )
    trigger_attestation_ref = _embed_report_input(
        trigger, trigger_path, "finalize/live_named_pipe_os_attestation", attestation
    )
    trigger["fresh_process_recovery"] = {
        "schema_version": "ego.life_playground.trigger_fresh_process_recovery.v1",
        **_evidence_provenance(
            finalize_verification,
            input_artifacts=[
                _artifact_ref(Path(request["database_path"])),
                trigger_request_ref,
                trigger_receipt_ref,
                trigger_attestation_ref,
            ],
            run_id=str(request["run_id"]),
            seed=int(trigger["seed"]),
            episode_ids=trigger["episode_ids"],
            context_ids=[str(request["challenge"])],
            aggregation_rule="validated_external_probe_updates_trigger_recovery_only",
            manifest_hash=trigger["product_code_manifest_hash"],
        ),
        "os_attestation": attestation,
        "prepare_pid": request["prepare_pid"],
        "probe_pid_claimed": receipt["probe_pid_claimed"],
        "probe_pid_observed": attestation["server_pid"],
        "finalizer_pid": attestation["finalizer_pid"],
        "probe_exit_observed": attestation["probe_exit_observed"],
        "probe_exit_code": attestation["probe_exit_code"],
        "no_orphan": attestation["no_orphan"],
        "process_boundary": validation["process_boundary"],
        "hashes_match": True,
        "hashes": receipt["hashes"],
    }
    trigger["fresh_recovery_hashes"] = {
        "state_hash": receipt["hashes"]["final_state_hash"],
        "model_hash": receipt["hashes"]["final_model_hash"],
        "memory_hash": receipt["hashes"]["final_memory_hash"],
        "goal_hash": receipt["hashes"]["current_goal_hash"],
        "clock_hash": receipt["hashes"]["clock_hash"],
    }
    trigger["fresh_recovery_hash_match"] = True
    trigger["fresh_recovery_process_boundary"] = validation["process_boundary"]
    trigger["fresh_recovery_probe_pid_claimed"] = receipt["probe_pid_claimed"]
    trigger["fresh_recovery_probe_pid_observed"] = attestation["server_pid"]
    trigger["fresh_recovery_probe_exit_observed"] = attestation["probe_exit_observed"]
    trigger["fresh_recovery_probe_exit_code"] = attestation["probe_exit_code"]
    trigger["fresh_recovery_no_orphan"] = attestation["no_orphan"]
    trigger["fresh_recovery_status"] = "external_probe_validated"
    _write_json(trigger_path, trigger)

    result["hard_requirements"]["fresh_recovery_all_causal_hashes_match"] = True
    result["hard_requirements"][
        "fresh_replay_and_all_tamper_controls_fail_closed"
    ] = finalized_replay_state[
        "fresh_replay_and_all_tamper_controls_fail_closed"
    ]
    result["blocking_failures"] = finalized_replay_state["blocking_failures"]
    result["verdict"] = finalized_replay_state["verdict"]
    result["fresh_process_protocol"] = {
        "status": "external_probe_validated",
        "challenge": request["challenge"],
        "prepare_pid": request["prepare_pid"],
        "probe_pid_claimed": receipt["probe_pid_claimed"],
        "probe_pid_observed": attestation["server_pid"],
        "finalizer_pid": attestation["finalizer_pid"],
        "probe_exit_observed": attestation["probe_exit_observed"],
        "probe_exit_code": attestation["probe_exit_code"],
        "no_orphan": attestation["no_orphan"],
        "process_boundary": validation["process_boundary"],
    }
    failure["blocking_failures"] = finalized_replay_state["blocking_failures"]
    _write_json(failure_path, failure)

    evidence_paths = [
        output / "continuity.sqlite3",
        output / "trace.jsonl",
        trigger_path,
        output / "baseline_comparison.json",
        output / "ablation_report.json",
        replay_path,
        output / "leakage_report.json",
        failure_path,
        output / "claim_ceiling.txt",
    ]
    result["input_artifacts"] = [_artifact_ref(path) for path in evidence_paths]
    result.pop("evidence_input_audit", None)
    _write_json(result_path, result)
    evidence_audit = audit_generated_artifact_inputs(output)
    if evidence_audit["blocking_failures"]:
        raise RuntimeError(
            "finalized evidence input audit failed: "
            + "; ".join(evidence_audit["blocking_failures"])
        )
    result["evidence_input_audit"] = evidence_audit
    _write_json(result_path, result)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(
            ROOT / "artifacts" / "EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A"
        ),
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--probe", action="store_true")
    modes.add_argument("--finalize", action="store_true")
    parser.add_argument("--probe-receipt")
    args = parser.parse_args(argv)
    if args.probe:
        if not args.probe_receipt:
            parser.error("--probe-receipt is required with --probe")
        serve_fresh_process_probe(args.output, args.probe_receipt)
        return 0
    if args.finalize:
        if not args.probe_receipt:
            parser.error("--probe-receipt is required with --finalize")
        result = finalize_verification(args.output, args.probe_receipt)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    result = run_verification(args.output, write_artifacts=True)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
