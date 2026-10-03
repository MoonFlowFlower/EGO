"""Change one candidate; retain the original frozen implementation and policy."""
import json
from pathlib import Path

from .routing import RoutedTransport


def configuration():
    return json.loads(Path(__file__).with_suffix(".json").read_bytes())


class RoutedTransportV2(RoutedTransport):
    def __init__(self, *, mode="product", route_index=0, **kwargs):
        super().__init__(mode=mode, route_index=route_index, **kwargs)
        replacement = configuration()
        if replacement["policy"] != self.policy or replacement["routes"][:2] != self.config["routes"][:2]:
            raise ValueError("v2_only_replaces_third_candidate")
        self.config = replacement
        self.routes = replacement["routes"] if mode == "product" else [replacement["routes"][route_index]]
        self.model = replacement["public_model"] if mode == "product" else self.routes[0]["model"]
        self.route = replacement["version"] if mode == "product" else self.routes[0]["route"]
