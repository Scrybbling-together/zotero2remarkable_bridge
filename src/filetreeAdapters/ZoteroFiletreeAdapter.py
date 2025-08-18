import tempfile
from pathlib import Path
from typing import List, Any, Dict, Optional

from pyzotero.zotero import Zotero

from src.filetreeAdapters.AbstractFiletree import AbstractFiletree


class ZoteroFiletreeAdapter(AbstractFiletree):
    """
    Adapter that implements AbstractFiletree interface for Zotero API.
    
    Path convention:
    - Root: []
    - Library items: ["items"]
    - Specific item: ["items", item_key]
    - Item attachments: ["items", item_key, "attachments"]
    - Specific attachment: ["items", item_key, "attachments", attachment_key]
    - Collections: ["collections"]
    - Specific collection: ["collections", collection_key]
    """
    
    def __init__(self, zotero_client: Zotero):
        self.zot = zotero_client
        self._item_cache = {}
        self._collection_cache = {}
    
    def _get_item_by_key(self, key: str) -> Optional[Dict]:
        """Get item by key with caching."""
        if key not in self._item_cache:
            try:
                self._item_cache[key] = self.zot.item(key)
            except Exception:
                return None
        return self._item_cache[key]
    
    def _get_collection_by_key(self, key: str) -> Optional[Dict]:
        """Get collection by key with caching."""
        if key not in self._collection_cache:
            try:
                self._collection_cache[key] = self.zot.collection(key)
            except Exception:
                return None
        return self._collection_cache[key]
    
    def _invalidate_cache(self, item_key: str = None):
        """Invalidate cache for specific item or all items."""
        if item_key:
            self._item_cache.pop(item_key, None)
        else:
            self._item_cache.clear()
            self._collection_cache.clear()
    
    def create_collection(self, path: List[str]) -> bool:
        """Create a new collection in Zotero."""
        try:
            if len(path) == 2 and path[0] == "collections":
                collection_name = path[1]
                payload = [{"name": collection_name}]
                result = self.zot.create_collection(payload)
                self._invalidate_cache()
                return result.get("success", {}) != {}
            return False
        except Exception:
            return False
    
    def create_file(self, path: List[str], content: bytes, content_type: str = "application/octet-stream") -> bool:
        """Create a file attachment in Zotero."""
        try:
            if len(path) == 4 and path[0] == "items" and path[2] == "attachments":
                parent_key = path[1]
                filename = path[3]
                
                # Save content to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                
                try:
                    # Create attachment using Zotero API
                    result = self.zot.attachment_simple([temp_path], parent_key)
                    success = result.get("success", {}) != {}
                    if success:
                        self._invalidate_cache(parent_key)
                    return success
                finally:
                    # Clean up temporary file
                    Path(temp_path).unlink(missing_ok=True)
            
            elif len(path) == 2 and path[0] == "items":
                # Create standalone item
                item_template = self.zot.item_template("document")
                item_template["title"] = path[1]
                result = self.zot.create_items([item_template])
                self._invalidate_cache()
                return result.get("success", {}) != {}
            
            return False
        except Exception:
            return False
    
    def node_exists(self, path: List[str]) -> bool:
        """Check if a node exists at the given path."""
        try:
            if not path:
                return True  # Root always exists
            
            if path[0] == "items":
                if len(path) == 1:
                    return True  # Items container always exists
                elif len(path) == 2:
                    return self._get_item_by_key(path[1]) is not None
                elif len(path) == 3 and path[2] == "attachments":
                    item = self._get_item_by_key(path[1])
                    return item is not None
                elif len(path) == 4 and path[2] == "attachments":
                    parent_item = self._get_item_by_key(path[1])
                    if parent_item is None:
                        return False
                    attachments = self.zot.children(path[1])
                    return any(att["key"] == path[3] for att in attachments)
            
            elif path[0] == "collections":
                if len(path) == 1:
                    return True  # Collections container always exists
                elif len(path) == 2:
                    return self._get_collection_by_key(path[1]) is not None
            
            return False
        except Exception:
            return False
    
    def is_collection(self, path: List[str]) -> bool:
        """Check if the node is a collection (container)."""
        try:
            if not path:
                return True  # Root is a collection
            
            if path[0] == "items":
                if len(path) == 1:
                    return True  # Items container
                elif len(path) == 2:
                    item = self._get_item_by_key(path[1])
                    return item is not None and item.get("data", {}).get("itemType") != "attachment"
                elif len(path) == 3 and path[2] == "attachments":
                    return True  # Attachments container
                return False
            
            elif path[0] == "collections":
                if len(path) == 1:
                    return True  # Collections container
                elif len(path) == 2:
                    return self._get_collection_by_key(path[1]) is not None
            
            return False
        except Exception:
            return False
    
    def is_file(self, path: List[str]) -> bool:
        """Check if the node is a file."""
        try:
            if len(path) == 4 and path[0] == "items" and path[2] == "attachments":
                parent_item = self._get_item_by_key(path[1])
                if parent_item is None:
                    return False
                attachments = self.zot.children(path[1])
                attachment = next((att for att in attachments if att["key"] == path[3]), None)
                return attachment is not None and attachment.get("data", {}).get("itemType") == "attachment"
            return False
        except Exception:
            return False
    
    def get_file_content(self, path: List[str]) -> bytes:
        """Get the content of a file attachment."""
        try:
            if len(path) == 4 and path[0] == "items" and path[2] == "attachments":
                attachment_key = path[3]
                with tempfile.TemporaryDirectory() as temp_dir:
                    self.zot.dump(attachment_key, path=temp_dir)
                    # Find the downloaded file
                    temp_path = Path(temp_dir)
                    files = list(temp_path.glob("*"))
                    if files:
                        with open(files[0], "rb") as f:
                            return f.read()
            raise FileNotFoundError(f"File not found at path: {path}")
        except Exception as e:
            raise FileNotFoundError(f"Could not retrieve file content: {str(e)}")
    
    def get_file_content_type(self, path: List[str]) -> str:
        """Get the content type of a file attachment."""
        try:
            if len(path) == 4 and path[0] == "items" and path[2] == "attachments":
                parent_key = path[1]
                attachment_key = path[3]
                attachments = self.zot.children(parent_key)
                attachment = next((att for att in attachments if att["key"] == attachment_key), None)
                if attachment:
                    return attachment.get("data", {}).get("contentType", "application/octet-stream")
            return "application/octet-stream"
        except Exception:
            return "application/octet-stream"
    
    def update_file_content(self, path: List[str], content: bytes) -> bool:
        """Update the content of an existing file attachment."""
        try:
            if len(path) == 4 and path[0] == "items" and path[2] == "attachments":
                parent_key = path[1]
                attachment_key = path[3]
                
                # Get the original filename
                attachments = self.zot.children(parent_key)
                attachment = next((att for att in attachments if att["key"] == attachment_key), None)
                if not attachment:
                    return False
                
                filename = attachment.get("data", {}).get("filename", "updated_file")
                
                # Save new content to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                
                try:
                    # Delete old attachment and create new one
                    self.zot.delete_item(attachment)
                    result = self.zot.attachment_simple([temp_path], parent_key)
                    success = result.get("success", {}) != {}
                    if success:
                        self._invalidate_cache(parent_key)
                    return success
                finally:
                    Path(temp_path).unlink(missing_ok=True)
            
            return False
        except Exception:
            return False
    
    def list_children(self, path: List[str]) -> List[str]:
        """List the children of a collection node."""
        try:
            if not path:
                # Root level: return top-level containers
                return ["items", "collections"]
            
            if path[0] == "items":
                if len(path) == 1:
                    # List all items
                    items = self.zot.items()
                    return [item["key"] for item in items if item.get("data", {}).get("itemType") != "attachment"]
                elif len(path) == 2:
                    # This is an item, no children (items don't contain other items directly)
                    return []
                elif len(path) == 3 and path[2] == "attachments":
                    # List attachments for an item
                    item_key = path[1]
                    attachments = self.zot.children(item_key)
                    return [att["key"] for att in attachments if att.get("data", {}).get("itemType") == "attachment"]
            
            elif path[0] == "collections":
                if len(path) == 1:
                    # List all collections
                    collections = self.zot.collections()
                    return [coll["key"] for coll in collections]
                elif len(path) == 2:
                    # List items in a specific collection
                    collection_key = path[1]
                    items = self.zot.collection_items(collection_key)
                    return [item["key"] for item in items]
            
            return []
        except Exception:
            return []
    
    def add_tags(self, path: List[str], tags: List[str]) -> bool:
        """Add tags to an item."""
        try:
            if len(path) == 2 and path[0] == "items":
                item_key = path[1]
                item = self._get_item_by_key(item_key)
                if item:
                    self.zot.add_tags(item, *tags)
                    self._invalidate_cache(item_key)
                    return True
            return False
        except Exception:
            return False
    
    def remove_tags(self, path: List[str], tags: List[str]) -> bool:
        """Remove tags from an item."""
        try:
            if len(path) == 2 and path[0] == "items":
                item_key = path[1]
                item = self._get_item_by_key(item_key)
                if item:
                    current_tags = item.get("data", {}).get("tags", [])
                    new_tags = [tag for tag in current_tags if tag.get("tag") not in tags]
                    item["data"]["tags"] = new_tags
                    self.zot.update_item(item)
                    self._invalidate_cache(item_key)
                    return True
            return False
        except Exception:
            return False
    
    def get_tags(self, path: List[str]) -> List[str]:
        """Get all tags for an item."""
        try:
            if len(path) == 2 and path[0] == "items":
                item_key = path[1]
                item = self._get_item_by_key(item_key)
                if item:
                    tags = item.get("data", {}).get("tags", [])
                    return [tag.get("tag", "") for tag in tags if tag.get("tag")]
            return []
        except Exception:
            return []
    
    def has_tags(self, path: List[str], tags: List[str]) -> bool:
        """Check if an item has all specified tags."""
        try:
            current_tags = self.get_tags(path)
            return all(tag in current_tags for tag in tags)
        except Exception:
            return False
    
    def find_nodes_with_tag(self, tag: str) -> List[List[str]]:
        """Find all items with a specific tag."""
        try:
            items = self.zot.items(tag="items")
            return [["items", item["key"]] for item in items]
        except Exception:
            return []
    
    def set_metadata(self, path: List[str], key: str, value: Any) -> bool:
        """Set metadata for an item."""
        try:
            if len(path) == 2 and path[0] == "items":
                item_key = path[1]
                item = self._get_item_by_key(item_key)
                if item:
                    # Map common metadata keys to Zotero fields
                    if key in item.get("data", {}):
                        item["data"][key] = value
                        self.zot.update_item(item)
                        self._invalidate_cache(item_key)
                        return True
            return False
        except Exception:
            return False
    
    def get_metadata(self, path: List[str], key: str) -> Any:
        """Get metadata for an item."""
        try:
            if len(path) == 2 and path[0] == "items":
                item_key = path[1]
                item = self._get_item_by_key(item_key)
                if item:
                    return item.get("data", {}).get(key)
            elif len(path) == 4 and path[0] == "items" and path[2] == "attachments":
                # Get attachment metadata
                parent_key = path[1]
                attachment_key = path[3]
                attachments = self.zot.children(parent_key)
                attachment = next((att for att in attachments if att["key"] == attachment_key), None)
                if attachment:
                    return attachment.get("data", {}).get(key)
            return None
        except Exception:
            return None
    
    def get_all_metadata(self, path: List[str]) -> Dict[str, Any]:
        """Get all metadata for an item."""
        try:
            if len(path) == 2 and path[0] == "items":
                item_key = path[1]
                item = self._get_item_by_key(item_key)
                if item:
                    return item.get("data", {})
            elif len(path) == 4 and path[0] == "items" and path[2] == "attachments":
                # Get attachment metadata
                parent_key = path[1]
                attachment_key = path[3]
                attachments = self.zot.children(parent_key)
                attachment = next((att for att in attachments if att["key"] == attachment_key), None)
                if attachment:
                    return attachment.get("data", {})
            return {}
        except Exception:
            return {}
    
    def delete_node(self, path: List[str]) -> bool:
        """Delete a node (item, attachment, or collection)."""
        try:
            if len(path) == 2 and path[0] == "items":
                # Delete an item
                item_key = path[1]
                item = self._get_item_by_key(item_key)
                if item:
                    self.zot.delete_item(item)
                    self._invalidate_cache(item_key)
                    return True
            
            elif len(path) == 4 and path[0] == "items" and path[2] == "attachments":
                # Delete an attachment
                parent_key = path[1]
                attachment_key = path[3]
                attachments = self.zot.children(parent_key)
                attachment = next((att for att in attachments if att["key"] == attachment_key), None)
                if attachment:
                    self.zot.delete_item(attachment)
                    self._invalidate_cache(parent_key)
                    return True
            
            elif len(path) == 2 and path[0] == "collections":
                # Delete a collection
                collection_key = path[1]
                collection = self._get_collection_by_key(collection_key)
                if collection:
                    self.zot.delete_collection(collection)
                    self._invalidate_cache()
                    return True
            
            return False
        except Exception:
            return False