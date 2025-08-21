import os
import tempfile
from pathlib import Path
from typing import List, Any, Dict, Optional

from pyzotero.zotero import Zotero

from zrm.filetreeAdapters.AbstractFiletree import TreeNode


class ZoteroAPI:
    def __init__(self, zotero_client: Zotero):
        self.zot = zotero_client
        self._item_cache = {}
        self._collection_cache = {}

    def _get_item_by_key(self, key: str) -> Optional[Dict]:
        """Get item by key with caching."""
        if key not in self._item_cache:
            self._item_cache[key] = self.zot.item(key)
        return self._item_cache[key]

    def _get_collection_by_key(self, key: str) -> Optional[Dict]:
        """Get collection by key with caching."""
        if key not in self._collection_cache:
            self._collection_cache[key] = self.zot.collection(key)
        return self._collection_cache[key]

    def _invalidate_cache(self, item_key: str = None):
        """Invalidate cache for specific item or all items."""
        if item_key:
            self._item_cache.pop(item_key, None)
        else:
            self._item_cache.clear()
            self._collection_cache.clear()

    def create_collection(self, path: List[str]) -> str:
        """Note, Zotero itself has a concept of "collections", by "collection" in the abstract tree
        The abstract file tree considers a folder or directory or anything else that can hold multiple other files or folders
        a "collection".

        Entries in a zotero library are modelled as "collections" in this API
        """
        # Create standalone item
        item_template = self.zot.item_template("document")
        item_template["title"] = path[0]
        result = self.zot.create_items([item_template])
        self._invalidate_cache()
        return result['successful']['0']['key']

    def create_file(self, handle: str, filename: str, content: bytes,
                    content_type: str = "application/octet-stream") -> str:
        """Create a file attachment"""
        with tempfile.TemporaryDirectory() as d:
            temp_path = str((Path(d) / Path(filename)).absolute())
            with open(temp_path, "wb") as f:
                f.write(content)
                f.flush()

                try:
                    # Create attachment using Zotero API
                    result = self.zot.attachment_simple([temp_path], handle)
                    if len(result['success']):
                        key_ = result['success'][0]['key']
                        self._invalidate_cache(handle)
                        return key_
                    elif len(result['unchanged']):
                        key_ = result['unchanged'][0]['key']
                        self._invalidate_cache(handle)
                        return key_
                finally:
                    # Clean up temporary file
                    Path(temp_path).unlink(missing_ok=True)

    def node_exists(self, handle: str) -> bool:
        """Check if a node exists at the given path."""
        return self._get_item_by_key(handle) is not None

    def get_file_content(self, handle: str) -> bytes | None:
        """Get the content of a file attachment."""

        with tempfile.TemporaryDirectory() as temp_dir:
            self.zot.dump(handle, path=temp_dir)
            # Find the downloaded file
            temp_path = Path(temp_dir)
            files = list(temp_path.glob("*"))
            if files:
                with open(files[0], "rb") as f:
                    return f.read()
            return None

    def update_file_content(self, parent_handle: str, attachment_handle: str, content: bytes) -> bool:
        """Update the content of an existing file attachment."""
        old_attachment = self._get_item_by_key(attachment_handle)
        name = old_attachment['data']['title']
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, name), "wb") as f:
                f.write(content)
                self.zot.delete_item(old_attachment)
                new_attachment = self.zot.attachment_simple([f.name], parent_handle)
                self._invalidate_cache(old_attachment['data']['key'])
                return new_attachment['success'][0]['key']

    def list_children(self, handle: str) -> List[TreeNode]:
        """List the children of a collection node."""
        children = self.zot.children(handle)
        return [TreeNode(handle=child['key'], name=child['data']['title'], type=child['data']['itemType'],
                         tags=child['data']['tags']) for child in children]

    def add_tags(self, handle: str, tags: List[str]) -> bool:
        """Add tags to an item."""
        item = self._get_item_by_key(handle)
        self.zot.add_tags(item, *tags)
        self._invalidate_cache(handle)
        return True

    def remove_tags(self, handle: str, tags: List[str]) -> bool:
        """Remove tags from an item."""
        item = self._get_item_by_key(handle)
        if item:
            current_tags = item.get("data", {}).get("tags", [])
            new_tags = [tag for tag in current_tags if tag.get("tag") not in tags]
            item["data"]["tags"] = new_tags
            self.zot.update_item(item)
            self._invalidate_cache(handle)
            return True
        return False

    def get_tags(self, handle: str) -> List[str]:
        """Get all tags for an item."""
        item = self._get_item_by_key(handle)
        if item:
            tags = item.get("data", {}).get("tags", [])
            return [tag.get("tag", "") for tag in tags if tag.get("tag")]
        return []

    def has_tags(self, handle: str, tags: List[str]) -> bool:
        """Check if an item has all specified tags."""
        try:
            current_tags = self.get_tags(handle)
            return all(tag in current_tags for tag in tags)
        except Exception:
            return False

    def find_nodes_with_tag(self, tag: str) -> List[TreeNode]:
        """Find all items with a specific tag."""
        items = self.zot.items(tag=tag)
        return [TreeNode(tags=item['data']['tags'], handle=item['key'], metadata=item, name=item['data']['title'],
            type=item['data']['itemType']) for item in items]

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
