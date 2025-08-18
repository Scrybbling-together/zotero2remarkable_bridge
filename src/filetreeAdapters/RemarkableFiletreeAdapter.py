from typing import List, Any, Dict
from pathlib import Path
import tempfile

from src.filetreeAdapters.AbstractFiletree import AbstractFiletree
from src import rmapi_shim as rmapi


class RemarkableFiletreeAdapter(AbstractFiletree):
    """
    Adapter that implements AbstractFiletree interface for reMarkable via rmapi.
    
    Path convention:
    - Root: []
    - Folder: ["folder_name"] 
    - Nested folder: ["folder_name", "subfolder"]
    - File: ["folder_name", "file_name"]
    """
    
    def __init__(self):
        # Verify rmapi is working
        if not rmapi.check_rmapi():
            raise RuntimeError("rmapi is not properly configured or accessible")
    
    def _path_to_rmapi_path(self, path: List[str]) -> str:
        """Convert path list to rmapi-style path string."""
        if not path:
            return "/"
        return "/" + "/".join(path)
    
    def create_collection(self, path: List[str]) -> bool:
        """Create a folder in reMarkable. rmapi creates folders automatically when uploading."""
        # rmapi creates folders automatically when needed, so we just check if it's valid
        try:
            rmapi_path = self._path_to_rmapi_path(path)
            # We can't actually create empty folders with rmapi, but we can mark this as successful
            # The folder will be created when the first file is uploaded to it
            return True
        except Exception:
            return False
    
    def create_file(self, path: List[str], content: bytes, content_type: str = "application/octet-stream") -> bool:
        """Upload a file to reMarkable."""
        try:
            if len(path) < 1:
                return False
                
            filename = path[-1]
            folder_path = path[:-1]
            rmapi_folder = self._path_to_rmapi_path(folder_path)
            
            # Save content to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                # Upload using rmapi
                success = rmapi.upload_file(temp_path, rmapi_folder)
                return success
            finally:
                # Clean up temporary file
                Path(temp_path).unlink(missing_ok=True)
                
        except Exception:
            return False
    
    def node_exists(self, path: List[str]) -> bool:
        """Check if a file or folder exists."""
        try:
            if not path:
                return True  # Root always exists
            
            rmapi_path = self._path_to_rmapi_path(path)
            
            # For files, check if they exist in the parent folder
            if len(path) >= 1:
                parent_path = path[:-1]
                filename = path[-1]
                
                parent_rmapi_path = self._path_to_rmapi_path(parent_path)
                files = rmapi.get_files(parent_rmapi_path)
                
                if files:
                    return filename in files
                    
            return False
        except Exception:
            return False
    
    def is_collection(self, path: List[str]) -> bool:
        """Check if the path represents a folder."""
        try:
            if not path:
                return True  # Root is always a collection
                
            # In rmapi, we determine if something is a collection by checking if it has children
            rmapi_path = self._path_to_rmapi_path(path)
            files = rmapi.get_files(rmapi_path)
            
            # If get_files succeeds and returns a list, it's a folder
            return isinstance(files, list)
        except Exception:
            return False
    
    def is_file(self, path: List[str]) -> bool:
        """Check if the path represents a file."""
        if not path:
            return False  # Root is not a file
            
        return self.node_exists(path) and not self.is_collection(path)
    
    def get_file_content(self, path: List[str]) -> bytes:
        """Download and return file content."""
        try:
            if not path:
                raise FileNotFoundError("Cannot get content of root")

            rmapi_path = self._path_to_rmapi_path(path)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                success = rmapi.download_file(rmapi_path, temp_dir)
                if not success:
                    raise FileNotFoundError(f"Failed to download file from {rmapi_path}")
                
                # Find the downloaded file
                temp_path = Path(temp_dir)
                files = list(temp_path.glob("*"))
                if not files:
                    raise FileNotFoundError(f"No files found after download from {rmapi_path}")
                
                with open(files[0], "rb") as f:
                    return f.read()
                    
        except Exception as e:
            raise FileNotFoundError(f"Could not retrieve file content: {str(e)}")
    
    def get_file_content_type(self, path: List[str]) -> str:
        """Get content type. reMarkable primarily handles PDFs."""
        if not path:
            return "application/octet-stream"
            
        filename = path[-1]
        if filename.lower().endswith('.pdf'):
            return "application/pdf"
        elif filename.lower().endswith('.epub'):
            return "application/epub+zip"
        else:
            return "application/octet-stream"
    
    def update_file_content(self, path: List[str], content: bytes) -> bool:
        """Update file content by re-uploading."""
        # reMarkable doesn't have direct update, so we re-upload
        return self.create_file(path, content, self.get_file_content_type(path))
    
    def list_children(self, path: List[str]) -> List[str]:
        """List files in a folder."""
        try:
            rmapi_path = self._path_to_rmapi_path(path)
            files = rmapi.get_files(rmapi_path)
            
            if isinstance(files, list):
                return files
            else:
                return []
        except Exception:
            return []
    
    def add_tags(self, path: List[str], tags: List[str]) -> bool:
        """reMarkable doesn't support tags directly."""
        return True  # No-op, but return success
    
    def remove_tags(self, path: List[str], tags: List[str]) -> bool:
        """reMarkable doesn't support tags directly."""
        return True  # No-op, but return success
    
    def get_tags(self, path: List[str]) -> List[str]:
        """reMarkable doesn't support tags directly."""
        return []  # No tags available
    
    def has_tags(self, path: List[str], tags: List[str]) -> bool:
        """reMarkable doesn't support tags directly."""
        return len(tags) == 0  # Only return true if no tags are requested
    
    def find_nodes_with_tag(self, collection_path: List[str], tag: str) -> List[List[str]]:
        """reMarkable doesn't support tags directly."""
        return []  # No tagged files
    
    def set_metadata(self, path: List[str], key: str, value: Any) -> bool:
        """Set metadata using rmapi (limited support)."""
        # reMarkable has limited metadata support through rmapi
        return False  # Most metadata operations not supported
    
    def get_metadata(self, path: List[str], key: str) -> Any:
        """Get metadata using rmapi."""
        try:
            if not path:
                return None
                
            rmapi_path = self._path_to_rmapi_path(path)
            metadata = rmapi.get_metadata(rmapi_path)
            
            if metadata and isinstance(metadata, dict):
                return metadata.get(key)
            return None
        except Exception:
            return None
    
    def get_all_metadata(self, path: List[str]) -> Dict[str, Any]:
        """Get all metadata using rmapi."""
        try:
            if not path:
                return {}
                
            rmapi_path = self._path_to_rmapi_path(path)
            metadata = rmapi.get_metadata(rmapi_path)
            
            if metadata and isinstance(metadata, dict):
                return metadata
            return {}
        except Exception:
            return {}
    
    def delete_node(self, path: List[str]) -> bool:
        """Delete a file or folder. Note: rmapi has limited delete support."""
        try:
            if not path:
                return False  # Cannot delete root
                
            # rmapi doesn't have a direct delete command in the current implementation
            # This would need to be implemented in rmapi_shim if delete functionality is needed
            return False
        except Exception:
            return False