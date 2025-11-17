from dataclasses import dataclass, field
from typing import List, Any, Dict


@dataclass
class TreeNode:
    """Base class for all tree nodes"""
    tags: List[str]
    handle: str
    type: str
    name: str
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_zotero_item(cls, zot_item: Dict[str, Any]):
        data = zot_item.get("data", {})
        return TreeNode(
            handle=data['key'],
            name=data.get('filename', ""),
            type=data.get('itemType', ''),
            tags=data.get('tags', []),
            path=data.get('path', ''),
            metadata=data
        )
