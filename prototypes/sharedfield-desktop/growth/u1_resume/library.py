"""Reusable quoted-convention library; original frozen implementation retained."""
from u1.conventions.core import ConventionLibrary as FrozenLibrary, normalize


class ConventionLibrary(FrozenLibrary):
    def propose(self, proposal, *, allowed_ids):
        if isinstance(proposal, dict) and isinstance(proposal.get('meaning'), str):
            if not normalize(proposal['meaning']):
                raise ValueError('empty_normalized_meaning')
        return super().propose(proposal, allowed_ids=allowed_ids)
