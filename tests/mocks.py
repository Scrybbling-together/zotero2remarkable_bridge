"""
Mock implementations that inherit from the real API classes for cleaner testing.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
import logging

from zrm.adapters.TreeNode import TreeNode
from zrm.adapters.ZoteroAPI import ZoteroAPI
from zrm.adapters.ReMarkableAPI import ReMarkableAPI

logger = logging.getLogger(__name__)


class MockZoteroAPI(ZoteroAPI):
    """Mock implementation that overrides ZoteroAPI methods."""

    def __init__(self):
        # Don't call super().__init__ to avoid needing real Zotero client
        self._items: Dict[str, Dict] = {}
        self._attachments: Dict[str, bytes] = {}  # handle -> content

    def create_item(self, path: List[str]) -> str:
        """Create a mock collection (item)."""
        handle = str(uuid.uuid4())
        self._items[handle] = {
            "key": handle,
            "data": {"title": path[0], "itemType": "document", "tags": []},
        }
        return handle

    def create_file(self, handle: str, filename: str, content: bytes) -> str:
        """Create a mock file attachment."""
        attachment_handle = str(uuid.uuid4())
        self._items[attachment_handle] = {
            "key": attachment_handle,
            "data": {
                "title": filename,
                "itemType": "attachment",
                "parentItem": handle,
                "tags": [],
            },
        }
        self._attachments[attachment_handle] = content
        return attachment_handle

    def item_exists(self, handle: str) -> bool:
        """Check if item exists."""
        return handle in self._items

    def get_file_content(self, handle: str) -> Optional[bytes]:
        """Get file content."""
        return self._attachments.get(handle)

    def update_file_content(
        self, parent_handle: str, attachment_handle: str, content: bytes
    ) -> str:
        """Update file content."""
        if attachment_handle in self._items:
            self._attachments[attachment_handle] = content
            return attachment_handle
        return ""

    def list_children(self, handle: str) -> List[TreeNode]:
        """List children of an item."""
        children = []
        for item_handle, item in self._items.items():
            if item["data"].get("parentItem") == handle:
                children.append(
                    TreeNode(
                        handle=item_handle,
                        name=item["data"]["title"],
                        type=item["data"]["itemType"],
                        path=item["data"].get("path", ""),
                        tags=item["data"]["tags"],
                    )
                )
        return children

    def add_tags(self, handle: str, tags: List[str]) -> bool:
        """Add tags to item."""
        if handle in self._items:
            current_tags = self._items[handle]["data"].get("tags", [])
            for tag in tags:
                if not any(t.get("tag") == tag for t in current_tags):
                    current_tags.append({"tag": tag})
            self._items[handle]["data"]["tags"] = current_tags
            return True
        return False

    def remove_tags(self, handle: str, tags: List[str]) -> bool:
        """Remove tags from item."""
        if handle in self._items:
            current_tags = self._items[handle]["data"].get("tags", [])
            new_tags = [t for t in current_tags if t.get("tag") not in tags]
            self._items[handle]["data"]["tags"] = new_tags
            return True
        return False

    def get_tags(self, handle: str) -> List[str]:
        """Get tags for item."""
        if handle in self._items:
            tags = self._items[handle]["data"].get("tags", [])
            return [tag.get("tag", "") for tag in tags if tag.get("tag")]
        return []

    def has_tags(self, handle: str, tags: List[str]) -> bool:
        """Check if item has all specified tags."""
        current_tags = self.get_tags(handle)
        return all(tag in current_tags for tag in tags)

    def find_nodes_with_tag(self, tag: str) -> List[TreeNode]:
        """Find all items with specified tag."""
        results = []
        for handle, item in self._items.items():
            tags = [t.get("tag", "") for t in item["data"].get("tags", [])]
            if tag in tags:
                results.append(
                    TreeNode(
                        handle=handle,
                        name=item["data"]["title"],
                        type=item["data"]["itemType"],
                        tags=item["data"]["tags"],
                        path=item["data"].get("path", ""),
                        metadata=item,
                    )
                )
        return results


class MockReMarkableAPI(ReMarkableAPI):
    """Mock implementation that overrides ReMarkableAPI methods."""

    def __init__(self, files: Dict[str, bytes], folders: set):
        # Don't call super().__init__ to avoid rmapi check
        self._files: Dict[str, bytes] = files
        self._folders: set = folders
        self._api_unavailable: bool = False

    def api_unavailable(self):
        """Configure mock to simulate API unavailability."""
        self._api_unavailable = True
        return self

    def upload_file(self, path: str, content: bytes) -> bool:
        """Upload a file."""
        if self._api_unavailable:
            logger.error("reMarkable API is unavailable")
            return False

        # Ensure parent directory exists
        parent = str(Path(path).parent)
        if parent not in self._folders:
            return False

        # Real rmapi now handles duplicates with delete-then-upload
        if path in self._files:
            logger.info("File already exists, deleting and retrying upload...")
            # Delete existing file
            if self.delete_file_or_folder(path):
                logger.info("Deleted existing file, retrying upload...")
                logger.info(f"Successfully overwritten file in {parent}")
            else:
                logger.error("Failed to delete existing file for overwrite")
                return False

        self._files[path] = content
        return True

    def file_or_folder_exists(self, path: str) -> bool:
        """Check if file or folder exists."""
        return path in self._files or path in self._folders

    def is_folder(self, path: str) -> bool:
        """Check if path is a folder."""
        return path in self._folders

    def is_file(self, path: str) -> bool:
        """Check if path is a file."""
        return path in self._files

    def get_file_content(self, path: str) -> bytes:
        """Get file content."""
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path]

    def list_children(self, path: str) -> List[str]:
        """List children in folder."""
        if path not in self._folders:
            return []

        children = []
        path_prefix = path + "/" if path else ""

        # Find files in this directory
        for file_path in self._files:
            if file_path.startswith(path_prefix):
                relative_path = file_path[len(path_prefix) :]
                if "/" not in relative_path:  # Direct child, not nested
                    children.append(relative_path)

        return children

    def delete_file_or_folder(self, path: str) -> bool:
        """Delete file or folder."""
        if path in self._files:
            del self._files[path]
            return True
        elif path in self._folders:
            # Remove folder and all its contents
            self._folders.discard(path)
            files_to_remove = [f for f in self._files if f.startswith(path + "/")]
            for file_path in files_to_remove:
                del self._files[file_path]
            return True
        return False
