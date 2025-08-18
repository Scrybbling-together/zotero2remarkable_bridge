"""
Tree state implementation for testing
"""
from typing import List, Dict, Any, Optional

from src.filetreeAdapters.AbstractFiletree import AbstractFiletree, Collection, TreeNode, File


class MockTreeState(AbstractFiletree):
    """In-memory implementation of TreeState for testing"""
    
    def __init__(self):
        self.root = Collection()
    
    def _get_node(self, path: List[str]) -> Optional[TreeNode]:
        """Navigate to a node in the tree"""
        current = self.root
        
        for name in path:
            if not isinstance(current, Collection):
                return None
            if name not in current.children:
                return None
            current = current.children[name]
        
        return current
    
    def _get_parent_and_name(self, path: List[str]) -> tuple[Optional[Collection], str]:
        """Get parent collection and child name"""
        if not path:
            return None, ""
        
        parent_path = path[:-1]
        name = path[-1]
        parent = self._get_node(parent_path)

        if not isinstance(parent, Collection):
            return None, name
            
        return parent, name
    
    def create_collection(self, path: List[str]) -> bool:
        if not path:
            return False
            
        parent, name = self._get_parent_and_name(path)
        if parent is None:
            return False
        
        if name in parent.children:
            return False
        
        parent.children[name] = Collection()
        return True
    
    def create_file(self, path: List[str], content: bytes, content_type: str = "application/octet-stream") -> bool:
        if not path:
            print("path is none")
            return False
            
        parent, name = self._get_parent_and_name(path)
        if parent is None:
            print(f"parent is none {path}")
            return False

        parent.children[name] = File(content=content, content_type=content_type)
        return True
    
    def node_exists(self, path: List[str]) -> bool:
        return self._get_node(path) is not None
    
    def is_collection(self, path: List[str]) -> bool:
        node = self._get_node(path)
        return isinstance(node, Collection)
    
    def is_file(self, path: List[str]) -> bool:
        node = self._get_node(path)
        return isinstance(node, File)
    
    def get_file_content(self, path: List[str]) -> bytes:
        node = self._get_node(path)
        if not isinstance(node, File):
            raise ValueError(f"Node at {path} is not a file")
        return node.content
    
    def get_file_content_type(self, path: List[str]) -> str:
        node = self._get_node(path)
        if not isinstance(node, File):
            raise ValueError(f"Node at {path} is not a file")
        return node.content_type
    
    def update_file_content(self, path: List[str], content: bytes) -> bool:
        node = self._get_node(path)
        if not isinstance(node, File):
            return False
        node.content = content
        return True
    
    def list_children(self, path: List[str]) -> List[str]:
        node = self._get_node(path)
        if not isinstance(node, Collection):
            raise ValueError(f"Node at {path} is not a collection")
        return list(node.children.keys())
    
    def add_tags(self, path: List[str], tags: List[str]) -> bool:
        node = self._get_node(path)
        if node is None:
            print("Node", node, "is false")
            return False
        
        for tag in tags:
            if tag not in node.tags:
                node.tags.append(tag)
        return True
    
    def remove_tags(self, path: List[str], tags: List[str]) -> bool:
        node = self._get_node(path)
        if node is None:
            return False
        
        for tag in tags:
            if tag in node.tags:
                node.tags.remove(tag)
        return True
    
    def get_tags(self, path: List[str]) -> List[str]:
        node = self._get_node(path)
        if node is None:
            return []
        return node.tags.copy()
    
    def has_tags(self, path: List[str], tags: List[str]) -> bool:
        node = self._get_node(path)
        if node is None:
            return False
        return all(tag in node.tags for tag in tags)
    
    def find_nodes_with_tag(self, tag: str) -> List[List[str]]:
        collection = self._get_node([])
        if not isinstance(collection, Collection):
            print("not a collection")
            return []
        
        results = []
        
        def _search(current_path: List[str], current_node: TreeNode):
            if tag in current_node.tags:
                results.append(current_path)
            
            if isinstance(current_node, Collection):
                for child_name, child_node in current_node.children.items():
                    child_path = current_path + [child_name]
                    _search(child_path, child_node)
        
        _search([], collection)
        return results

    def set_metadata(self, path: List[str], key: str, value: Any) -> bool:
        node = self._get_node(path)
        if node is None:
            return False
        node.metadata[key] = value
        return True
    
    def get_metadata(self, path: List[str], key: str) -> Any:
        node = self._get_node(path)
        if node is None:
            return None
        return node.metadata.get(key)
    
    def get_all_metadata(self, path: List[str]) -> Dict[str, Any]:
        node = self._get_node(path)
        if node is None:
            return {}
        return node.metadata.copy()
    
    def delete_node(self, path: List[str]) -> bool:
        if not path:
            return False
            
        parent, name = self._get_parent_and_name(path)
        if parent is None or name not in parent.children:
            return False
        
        del parent.children[name]
        return True