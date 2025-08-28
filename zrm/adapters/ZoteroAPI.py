import os
import tempfile
from pathlib import Path
from typing import List, Any, Dict, Optional

from pyzotero.zotero import Zotero

from zrm.adapters.TreeNode import TreeNode


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

    def create_item(self, path: List[str]) -> str:
        # Create standalone item
        item_template = self.zot.item_template("document")
        item_template["title"] = path[0]
        result = self.zot.create_items([item_template])
        self._invalidate_cache()
        return result['successful']['0']['key']

    def create_file(self, handle: str, filename: str, content: bytes) -> str:
        """Create a file attachment"""
        with tempfile.TemporaryDirectory() as d:
            temp_path = str((Path(d) / Path(filename)).absolute())
            with open(temp_path, "wb") as f:
                f.write(content)
                f.flush()

                # Create attachment using Zotero API
                result = self.zot.attachment_simple([temp_path], handle)
                if len(result['success']):
                    key = result['success'][0]['key']
                    self._invalidate_cache(handle)
                    return key
                elif len(result['unchanged']):
                    key = result['unchanged'][0]['key']
                    self._invalidate_cache(handle)
                    return key

        raise RuntimeError(f"was unable to create Zotero file {filename} for {handle}")

    def item_exists(self, handle: str) -> bool:
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

    def update_file_content(self, parent_handle: str, attachment_handle: str, content: bytes) -> str:
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
        """List the children of a collection node.
        """
        children = self.zot.children(handle)

        return_list = []
        for child in children:
            data = child.get("data", {})
            return_list.append(
                TreeNode(handle=child['key'], name=data.get('filename', ""), type=data.get('itemType', ''),
                         tags=data.get('tags', []), path=data.get('path', '')))
        return return_list

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

        return_list = []
        for child in items:
            data = child.get("data", {})
            return_list.append(
                TreeNode(handle=child['key'], name=data.get('filename', ""), type=data.get('itemType', ''),
                         tags=data.get('tags', []), path=data.get('path', '')))
        return return_list

