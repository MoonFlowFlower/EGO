"""Current-user Windows DPAPI storage for the loopback credential only."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import re
import secrets
import tempfile

from growthlab.records import ROOT

TOKEN_PATH = ROOT / 'runs/kernel_v1/local-token.dpapi'


class Blob(ctypes.Structure):
    _fields_ = [('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]


def crypt(data, *, decrypt=False):
    if os.name != 'nt':
        raise RuntimeError('windows_dpapi_required')
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    dll = ctypes.WinDLL('crypt32',use_last_error=True)
    function = dll.CryptUnprotectData if decrypt else dll.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    if not function(ctypes.byref(source),None,None,None,None,1,ctypes.byref(output)):
        raise RuntimeError('dpapi_unavailable')
    try:
        return ctypes.string_at(output.data,output.size)
    finally:
        free = ctypes.WinDLL('kernel32').LocalFree
        free.argtypes = [ctypes.c_void_p]
        free.restype = ctypes.c_void_p
        free(output.data)


def persistent_token(path=TOKEN_PATH, *, rotate=False, supplied=None):
    path = Path(path)
    if path.exists() and not rotate and supplied is None:
        token = crypt(path.read_bytes(),decrypt=True).decode('ascii')
    else:
        token = supplied or secrets.token_urlsafe(32)
        if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}',token):
            raise ValueError('invalid_local_token')
        path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as output:
            output.write(crypt(token.encode('ascii')))
            temporary = Path(output.name)
        os.replace(temporary,path)
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}',token):
        raise ValueError('invalid_local_token')
    return token
