#!/usr/bin/python3
import sys
import getopt

from pyzotero.zotero import Zotero
from tqdm import tqdm
from config_functions import *
from sync_functions import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler(filename="sync.log"))

def push(zot: Zotero, webdav: bool, folders):
    logger.info("Syncing from Zotero to reMarkable")
    sync_items = zot.items(tag="to_sync")
    if sync_items:
        logger.info(f"Found {len(sync_items)} PDF attachments on the zotero to sync...")
        for item in tqdm(sync_items):
            if webdav:
                sync_to_rm_webdav(item, zot, webdav, folders)
            else:
                sync_to_rm(item, zot, folders)
        zot.delete_tags("to_sync")
    else:
        logger.info("Nothing to sync from Zotero")


def pull(zot: Zotero, webdav: bool, read_folder: str):
    logger.info("Syncing from reMarkable to Zotero")
    files_list = rmapi.get_files(read_folder)
    if files_list:
        logger.info(f"There are {len(files_list)} files to download from the reMarkable")
        for entity in tqdm(files_list):
            pdf_name = download_from_rm(entity, read_folder)
            if webdav:
                zotero_upload_webdav(pdf_name, zot, webdav)
            else:
                attach_pdf_to_zotero_document(pdf_name, zot)
    else:
        logger.info("No files ")


def main(argv):
    config_path = Path.cwd() / "config.yml"
    if not config_path.exists():
        write_config("config.yml")

    zot, webdav, folders = load_config("config.yml")
    read_folder = f"/Zotero/{folders['read']}/"
    
    try:
        opts, args = getopt.getopt(argv, "m:")
    except getopt.GetoptError:
        logger.error("No argument recognized")
        sys.exit()

    if not opts:
        opts = [["-m", "both"]]

    try:
        for opt, arg in opts:
            if opt == "-m":
                if arg == "push":
                    # Only sync files from Zotero to reMarkable
                    push(zot, webdav, folders)
                elif arg == "pull":
                    # Only get files from ReMarkable and upload to Zotero
                    pull(zot, webdav, read_folder)
                elif arg == "both":
                    # Upload...
                    push(zot, webdav, folders)
                    # ...and download, add highlighting and sync to Zotero.
                    pull(zot, webdav, read_folder)
                else:
                    logger.error("Invalid argument")
                    sys.exit()
    except Exception as e:
        logger.exception(e)
        

main(sys.argv[1:])
