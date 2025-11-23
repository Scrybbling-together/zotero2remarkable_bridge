# rmapi_shim.py
import os
import subprocess
import logging
import shutil
from pathlib import Path
from typing import List
from functools import cache

logger = logging.getLogger(__name__)


@cache
def get_rmapi_location() -> str:
    """Get rmapi location or raise error"""
    location = shutil.which("rmapi") or shutil.which("./rmapi")
    if location is None:
        raise FileNotFoundError("Could not find 'rmapi' on your system PATH.")
    return location


def run_rmapi_command(
    args: List[str], **kwargs
) -> tuple[bool, subprocess.CompletedProcess]:
    """Run rmapi command and handle common success/failure logging."""
    result = subprocess.run(
        [get_rmapi_location()] + args, capture_output=True, text=True, **kwargs
    )
    success = result.returncode == 0
    if not success:
        logger.info(result.stdout)
        logger.error(result.stderr)
    return success, result


def check_rmapi():
    success, _ = run_rmapi_command(["ls"])
    return success


def get_children(folder: str) -> None | List[str]:
    """Get all children in a specific folder."""
    success, result = run_rmapi_command(["ls", folder])
    if success:
        children_list = result.stdout.split("\n")
        children_list_new = []
        for file in children_list:
            if file.startswith(" Time"):
                logger.warning(
                    f"Child `{file}` starts with ` Time` construct. What does this mean?"
                )
                logger.warning(
                    f"Full output of `rmapi ls` for context, {result.stdout}"
                )
            if file:
                children_list_new.append(file.split("\t", 1)[1])
        return children_list_new
    return None


def get_files(folder: str) -> None | List[str]:
    # Get all files from a specific folder. Output is sanitized and subfolders are excluded
    success, result = run_rmapi_command(["ls", folder])
    if success:
        files_list = result.stdout.split("\n")
        files_list_new = []
        for file in files_list:
            if file.startswith(" Time"):
                logger.warning(
                    f"File `{file}` starts with ` Time` construct. What does this mean?"
                )
                logger.warning(
                    f"Full output of `rmapi ls` for context, {result.stdout}"
                )
            if file.startswith("[f]\t"):
                files_list_new.append(file[len("[f]\t") :])
        return files_list_new
    return None


def download_file(file_path, working_dir):
    # Downloads a file (consisting of a zip file) to a specified directory
    success, _ = run_rmapi_command(["get", file_path], cwd=working_dir)
    return success


def upload_file(file_path, target_folder):
    # Upload a file to its destination folder
    success, result = run_rmapi_command(["put", file_path, target_folder])
    if not success:
        # Check if failure was due to existing file
        if "entry already exists" in result.stderr:
            from pathlib import Path

            filename = Path(file_path).stem  # filename without extension
            full_remote_path = f"{target_folder}/{filename}"

            logger.info(f"File already exists, deleting and retrying upload...")
            # Try to delete the existing file
            if delete_file(full_remote_path):
                logger.info(f"Deleted existing file, retrying upload...")
                # Retry upload
                success, _ = run_rmapi_command(["put", file_path, target_folder])
                if success:
                    logger.info(f"Successfully overwritten file in {target_folder}")
            else:
                logger.error(f"Failed to delete existing file for overwrite")
    return success


def delete_file(path):
    success, _ = run_rmapi_command(["rm", path])
    return success
