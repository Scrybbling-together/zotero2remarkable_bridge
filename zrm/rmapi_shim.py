# rmapi_shim.py
import os
import subprocess
import logging
import shutil
from typing import List

logger = logging.getLogger(__name__)

# First try to find rmapi in current working directory
current_dir = os.getcwd()
rmapi_path_in_cwd = os.path.join(current_dir, "rmapi")
if os.path.isfile(rmapi_path_in_cwd) and os.access(rmapi_path_in_cwd, os.X_OK):
    rmapi_location = rmapi_path_in_cwd
else:
    # If not found in cwd, try system PATH
    rmapi_location = shutil.which("rmapi")

if rmapi_location is None:
    raise FileNotFoundError("Could not find 'rmapi' in current working directory or on your system PATH.")


def check_rmapi():
    check = subprocess.run([rmapi_location, "ls"], capture_output=True, text=True)
    success = check.returncode == 0
    if not success:
        logger.info(check.stdout)
        logger.error(check.stderr)
    return success


def get_children(folder: str) -> bool | List[str]:
    """Get all children in a specific folder."""
    files = subprocess.run([rmapi_location, "ls", folder], capture_output=True, text=True)
    success = files.returncode == 0
    if success:
        files_list = files.stdout.split("\n")
        files_list_new = []
        for file in files_list:
            if file[:5] != " Time" and file != "":
                files_list_new.append(file[4:])
        return files_list_new
    else:
        logger.info(files.stdout)
        logger.error(files.stderr)
        return False

def get_files(folder: str) -> bool | List[str]:
    # Get all files from a specific folder. Output is sanitized and subfolders are excluded
    files = subprocess.run([rmapi_location, "ls", folder], capture_output=True, text=True)
    success = files.returncode == 0
    if success:
        files_list = files.stdout.split("\n")
        files_list_new = []
        for file in files_list:
            if file[:5] != " Time" and file[:3] != "[d]" and file != "":
                files_list_new.append(file[4:])
        return files_list_new
    else:
        logger.info(files.stdout)
        logger.error(files.stderr)
        return False


def download_file(file_path, working_dir):
    # Downloads a file (consisting of a zip file) to a specified directory
    downloader = subprocess.run([rmapi_location, "get", file_path], cwd=working_dir, capture_output=True, text=True)
    success = downloader.returncode == 0
    if not success:
        logger.info(downloader.stdout)
        logger.error(downloader.stderr)
    return success



def upload_file(file_path, target_folder):
    # Upload a file to its destination folder
    uploader = subprocess.run([rmapi_location, "put", file_path, target_folder], capture_output=True, text=True)
    success = uploader.returncode == 0
    if not success:
        # Check if failure was due to existing file
        if "entry already exists" in uploader.stderr:
            from pathlib import Path
            filename = Path(file_path).stem  # filename without extension
            full_remote_path = f"{target_folder}/{filename}"
            
            logger.info(f"File already exists, deleting and retrying upload...")
            # Try to delete the existing file
            if delete_file(full_remote_path):
                logger.info(f"Deleted existing file, retrying upload...")
                # Retry upload
                uploader_retry = subprocess.run([rmapi_location, "put", file_path, target_folder], capture_output=True, text=True)
                success = uploader_retry.returncode == 0
                if not success:
                    logger.info(uploader_retry.stdout)
                    logger.error(uploader_retry.stderr)
                else:
                    logger.info(f"Successfully overwritten file in {target_folder}")
            else:
                logger.error(f"Failed to delete existing file for overwrite")
        else:
            logger.info(uploader.stdout)
            logger.error(uploader.stderr)
    return success


def delete_file(path):
    deleter = subprocess.run([rmapi_location, "rm", path])
    success = deleter.returncode == 0
    if not success:
        logger.info(deleter.stdout)
        logger.error(deleter.stderr)
    return success
