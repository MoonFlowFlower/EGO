"""Parent-owned P7 session. stdout is a private pipe, never a terminal or log.

The desktop automation parent consumes the one-line local token in memory.
Only the already authorized existing P2 credential reader sees the cloud key.
No cloud completion occurs until a client explicitly sends one.
"""
from __future__ import annotations

import json
import sys

from growthlab.models import read_key
from p7.proxy import ProxyServer
from p7.routing import RoutedTransport


def main():
    if sys.stdout.isatty() or '--private-pipe' not in sys.argv:
        raise SystemExit('private_parent_pipe_required')
    transport = RoutedTransport(api_key=read_key())
    metadata = transport.preflight()
    # Electron file:// documents use the literal opaque Origin "null".
    # The unpredictable Bearer token is still required for every API call.
    with ProxyServer(transport, port=18787, allowed_origins={'null', 'app://localhost', 'http://localhost'}) as server:
        print(json.dumps({'base_url': server.base_url, 'session_token': server.token,
                          'route': metadata}), flush=True)
        for line in sys.stdin:
            if line.strip() == 'stop':
                break


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Exception strings and traceback context may contain credentials.
        print(json.dumps({'error_type': type(error).__name__}), flush=True)
        raise SystemExit(1) from None
