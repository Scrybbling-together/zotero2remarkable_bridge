from dataclasses import dataclass, field
from typing import List, Any, Dict

@dataclass
class TreeNode:
    """Base class for all tree nodes"""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    handle: str = field(default_factory=str)
    type: str = field(default_factory=str)
    name: str = field(default_factory=str)
    path: str = field(default_factory=str)



