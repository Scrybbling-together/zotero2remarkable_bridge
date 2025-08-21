from abc import ABC, abstractmethod
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


@dataclass
class Collection(TreeNode):
    """Collection node that can contain other nodes"""
    children: Dict[str, TreeNode] = field(default_factory=dict)


@dataclass
class File(TreeNode):
    """File node with content"""
    content: bytes = b""
    content_type: str = "application/octet-stream"


class AbstractFiletree(ABC):
    """Abstract interface for tree structures with collections and files"""

    # Node creation (explicit - no auto-creation)
    @abstractmethod
    def create_collection(self, path: List[str]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def create_file(self, path: List[str], content: bytes, content_type: str = "application/octet-stream") -> bool:
        raise NotImplementedError()

    # Node existence
    @abstractmethod
    def node_exists(self, handle: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def is_collection(self, path: List[str]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def is_file(self, path: List[str]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_file_content(self, handle: str) -> bytes:
        raise NotImplementedError()

    @abstractmethod
    def get_file_content_type(self, path: List[str]) -> str:
        raise NotImplementedError()

    @abstractmethod
    def update_file_content(self, path: List[str], content: bytes) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def list_children(self, handle: str) -> List[TreeNode]:
        raise NotImplementedError()

    @abstractmethod
    def add_tags(self, handle: str, tags: List[str]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def remove_tags(self, handle: str, tags: List[str]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_tags(self, path: List[str]) -> List[str]:
        raise NotImplementedError()

    @abstractmethod
    def has_tags(self, path: List[str], tags: List[str]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def find_nodes_with_tag(self, tag: str) -> List[TreeNode]:
        raise NotImplementedError()

    @abstractmethod
    def set_metadata(self, path: List[str], key: str, value: Any) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_metadata(self, path: List[str], key: str) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def get_all_metadata(self, path: List[str]) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def delete_node(self, path: List[str]) -> bool:
        raise NotImplementedError()



