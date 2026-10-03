"""Current application entry; the v1 entry files remain reproducible snapshots.

Use -m p7.active_proxy for the credential window, or --private-pipe for an
owner-authorized parent that consumes its local token without displaying it.
"""
import json
import sys

from .routing_v2 import RoutedTransportV2, configuration


def main():
    if "--private-pipe" in sys.argv:
        from . import runtime_session as entry
    else:
        from . import launch_proxy as entry
    # Process-local factory injection keeps both frozen v1 entry files intact.
    # Neither module starts on import, and only one entry is run in this process.
    entry.RoutedTransport = RoutedTransportV2
    entry.configuration = configuration
    entry.main()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"error_type": type(error).__name__}), flush=True)
        raise SystemExit(1) from None
