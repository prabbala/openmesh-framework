"""LOB Hierarchy data models — LOBCategory and LOBNode.

Defines the two-tier LOB hierarchy: I_LOB (Infrastructure) and P_LOB (Product).
LOBs are organizational boundaries for scoping access and visibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LOBCategory(Enum):
    """LOB category types."""

    I_LOB = "infrastructure"  # Infrastructure LOB
    P_LOB = "product"  # Product LOB


@dataclass
class LOBNode:
    """A node in the LOB hierarchy.

    Fields:
        lob_id: Unique identifier.
        name: Human-readable name.
        category: I_LOB or P_LOB.
        parent_lob_id: Optional parent for nested LOBs.
        entity_id: Which Entity this LOB belongs to.
    """

    lob_id: str
    name: str
    category: LOBCategory
    parent_lob_id: Optional[str] = None
    entity_id: str = ""

    def __post_init__(self) -> None:
        if not self.lob_id or not self.lob_id.strip():
            raise ValueError("lob_id must be a non-empty string")
        if not self.name or not self.name.strip():
            raise ValueError("name must be a non-empty string")
