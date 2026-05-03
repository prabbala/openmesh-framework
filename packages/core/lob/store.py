"""LOB Store — CRUD operations for LOB nodes.

Manages the LOB hierarchy with referential integrity checks.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from .models import LOBNode


class LOBNotFoundError(Exception):
    """Raised when a LOB is not found."""


class DuplicateLOBError(Exception):
    """Raised when a LOB ID already exists."""


class LOBReferentialIntegrityError(Exception):
    """Raised when LOB deletion would violate referential integrity."""

    def __init__(self, message: str, referencing_ids: List[str]) -> None:
        super().__init__(message)
        self.referencing_ids = referencing_ids


class LOBStore:
    """In-memory store for LOB nodes with CRUD operations."""

    def __init__(self) -> None:
        self._lobs: Dict[str, LOBNode] = {}
        # Track which domains reference each LOB
        self._domain_lob_refs: Dict[str, Set[str]] = {}  # lob_id -> {domain_ids}
        # Track which users are assigned to each LOB
        self._user_lob_refs: Dict[str, Set[str]] = {}  # lob_id -> {user_ids}

    def create_lob(self, lob: LOBNode) -> LOBNode:
        """Create a LOB node.

        Raises:
            DuplicateLOBError: If lob_id already exists.
        """
        if lob.lob_id in self._lobs:
            raise DuplicateLOBError(
                f"LOB with id '{lob.lob_id}' already exists"
            )
        self._lobs[lob.lob_id] = lob
        return lob

    def get_lob(self, lob_id: str) -> Optional[LOBNode]:
        """Return a LOB by ID, or None if not found."""
        return self._lobs.get(lob_id)

    def list_lobs(self, entity_id: Optional[str] = None) -> List[LOBNode]:
        """Return all LOBs, optionally filtered by entity_id."""
        if entity_id is not None:
            return [l for l in self._lobs.values() if l.entity_id == entity_id]
        return list(self._lobs.values())

    def get_all_lob_ids(self) -> Set[str]:
        """Return the set of all LOB IDs."""
        return set(self._lobs.keys())

    def delete_lob(self, lob_id: str) -> None:
        """Delete a LOB. Rejects if domains or users reference it.

        Raises:
            LOBNotFoundError: If lob_id does not exist.
            LOBReferentialIntegrityError: If domains or users reference this LOB.
        """
        if lob_id not in self._lobs:
            raise LOBNotFoundError(f"LOB '{lob_id}' not found")

        referencing: List[str] = []
        # Check domain references
        domain_refs = self._domain_lob_refs.get(lob_id, set())
        referencing.extend(sorted(domain_refs))
        # Check user references
        user_refs = self._user_lob_refs.get(lob_id, set())
        referencing.extend(sorted(user_refs))

        if referencing:
            raise LOBReferentialIntegrityError(
                f"Cannot delete LOB '{lob_id}': "
                f"{len(referencing)} entity(ies) reference it",
                referencing_ids=referencing,
            )

        del self._lobs[lob_id]
        self._domain_lob_refs.pop(lob_id, None)
        self._user_lob_refs.pop(lob_id, None)

    # ── Reference tracking ───────────────────────────────────────────

    def add_domain_ref(self, lob_id: str, domain_id: str) -> None:
        """Track that a domain references this LOB."""
        self._domain_lob_refs.setdefault(lob_id, set()).add(domain_id)

    def remove_domain_ref(self, lob_id: str, domain_id: str) -> None:
        """Remove a domain reference from this LOB."""
        refs = self._domain_lob_refs.get(lob_id)
        if refs:
            refs.discard(domain_id)

    def add_user_ref(self, lob_id: str, user_id: str) -> None:
        """Track that a user is assigned to this LOB."""
        self._user_lob_refs.setdefault(lob_id, set()).add(user_id)

    def remove_user_ref(self, lob_id: str, user_id: str) -> None:
        """Remove a user reference from this LOB."""
        refs = self._user_lob_refs.get(lob_id)
        if refs:
            refs.discard(user_id)
