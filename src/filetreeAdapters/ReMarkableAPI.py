import logging
from typing import List
from pathlib import Path
import tempfile

from src import rmapi_shim as rmapi

logger = logging.getLogger(__name__)


class ReMarkableAPI:
    def __init__(self):
        # Verify rmapi is working
        if not rmapi.check_rmapi():
            raise RuntimeError("rmapi is not properly configured or accessible")

    def create_file(self, path: str, content: bytes, content_type: str = "application/octet-stream") -> bool:
        """Upload a file to reMarkable."""
        try:
            if len(path) < 1:
                return False

            path = Path(path)
            filename = path.name

            with tempfile.TemporaryDirectory() as d:
                with open(str(Path(d) / Path(filename)), "wb") as f:
                    f.write(content)
                    f.flush()

                    try:
                        success = rmapi.upload_file(f.name, str(path.parent))
                        return success
                    except Exception as e:
                        logger.error(e)
                    finally:
                        Path(f.name).unlink(missing_ok=True)

        except Exception as e:
            logger.error(e)
            return False

    def node_exists(self, path: str) -> bool:
        """Check if a file or folder exists."""
        path = Path(path)

        d = str(path.parent)
        if not path:
            # Root always exists
            return True

        files = rmapi.get_children(d)

        if files:
            return path.name.replace(".pdf", "") in files

        return False

    def is_collection(self, path: List[str]) -> bool:
        """Check if the path represents a folder."""
        if not path:
            return True  # Root is always a collection

        # In rmapi, we determine if something is a collection by checking if it has children
        files = rmapi.get_files(path)

        # If get_files succeeds and returns a list, it's a folder
        return isinstance(files, list)

    def is_file(self, path: str) -> bool:
        """Check if the path represents a file."""
        if not path:
            return False  # Root is not a file
            
        return self.node_exists(path) and not self.is_collection(path)
    
    def get_file_content(self, path: str) -> bytes:
        """Download and return file content."""
        try:
            if not path:
                raise FileNotFoundError("Cannot get content of root")

            with tempfile.TemporaryDirectory() as temp_dir:
                success = rmapi.download_file(path, temp_dir)
                if not success:
                    raise FileNotFoundError(f"Failed to download file from {path}")
                
                # Find the downloaded file
                temp_path = Path(temp_dir)
                files = list(temp_path.glob("*"))
                if not files:
                    raise FileNotFoundError(f"No files found after download from {path}")
                
                with open(files[0], "rb") as f:
                    return f.read()
                    
        except Exception as e:
            raise FileNotFoundError(f"Could not retrieve file content: {str(e)}")

    def list_children(self, path: str) -> List[str]:
        """List files in a folder."""
        files = rmapi.get_files(path)

        if isinstance(files, list):
            return files
        else:
            return []

    def delete_file_or_folder(self, path: str) -> bool:
        """Delete a file or folder."""
        if not path:
            return False

        return rmapi.delete_file(path)