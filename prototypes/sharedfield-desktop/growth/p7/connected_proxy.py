"""Same frozen routing-v2, with the connected-round's predeclared budget cap."""
import json
from pathlib import Path
from .routing_v2 import RoutedTransportV2
from . import runtime_session


class ConnectedTransport(RoutedTransportV2):
    def __init__(self, **kwargs):
        record = json.loads((Path(__file__).parents[1] /
            'evidence/p7/MC_CONNECTED_FREEZE.json').read_text(encoding='utf-8-sig'))
        cap = record['budget_at_start_usd'] + record['additional_occupancy_limit_usd']
        super().__init__(limit=min(5, cap), **kwargs)


if __name__ == '__main__':
    runtime_session.RoutedTransport = ConnectedTransport
    try:
        runtime_session.main()
    except Exception as error:
        print(json.dumps({'error_type': type(error).__name__}), flush=True)
        raise SystemExit(1) from None
