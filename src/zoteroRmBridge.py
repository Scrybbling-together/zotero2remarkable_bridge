#!/usr/bin/python3
import sys
import getopt

from tqdm import tqdm
from config_functions import *
from sync_functions import *
from src.filetreeAdapters.ZoteroFiletreeAdapter import ZoteroFiletreeAdapter
from src.filetreeAdapters.RemarkableFiletreeAdapter import RemarkableFiletreeAdapter
import logging.config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(), logging.FileHandler(filename="sync.log")])


def zotToRm(zotero: AbstractFiletree, rm: AbstractFiletree, folders):
    """Push files from Zotero to reMarkable using filetree interface."""
    logger.info("Syncing from Zotero to reMarkable")
    
    sync_items = zotero.find_nodes_with_tag("to_sync")
    
    if sync_items:
        logger.info(f"Found {len(sync_items)} items to sync...")
        for item_path in tqdm(sync_items):
            sync_to_rm_filetree(item_path, zotero, rm, folders)
        
        # Remove "to_sync" tag from all items
        for item_path in sync_items:
            zotero.remove_tags(item_path, ["to_sync"])
    else:
        logger.info("Nothing to sync from Zotero")


def rmToZot(zotero: AbstractFiletree, rm: AbstractFiletree, read_folder: str):
    """Pull files from reMarkable to Zotero using filetree interface."""
    logger.info("Syncing from reMarkable to Zotero")
    rm_folder_path = ["Zotero", read_folder.strip("/")]
    if rm.node_exists(rm_folder_path):
        files_list = rm.list_children(rm_folder_path)
        
        if files_list:
            logger.info(f"There are {len(files_list)} files to download from the reMarkable")
            for filename in tqdm(files_list):
                path = rm_folder_path + [filename]
                content = rm.get_file_content(path)
                filename = path[-1]
                temp_path = tempfile.mkdtemp()
                if filename.endswith('.pdf'):
                    with open(temp_path + "/process_me.rmn", "wb") as f:
                        f.write(content)
                    download_path = [n for n in path]
                    download_path[-1] = filename
                    remarks.run_remarks(temp_path + "/process_me.rmn", temp_path)
                rendered_pdf = [file for file in os.listdir(temp_path) if file.endswith(" _remarks.pdf")]
                if not rendered_pdf[0]:
                    logging.error("Was unable to find the processed pdf")
                attach_remarks_render_to_zotero_entry(Path(temp_path) / (rendered_pdf[0]), zotero)
        else:
            logger.info("No files to sync from reMarkable")
    else:
        logger.info(f"Read folder {rm_folder_path} does not exist on reMarkable")


def main():
    argv = sys.argv[1:]
    config_path = Path.cwd() / "config.yml"
    if not config_path.exists():
        write_config("config.yml")

    zot, webdav, folders = load_config("config.yml")
    read_folder = folders['read']

    # Initialize filetree adapters
    try:
        zotero_tree = ZoteroFiletreeAdapter(zot)
        rm_tree = RemarkableFiletreeAdapter()
        logger.info("Filetree adapters initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize filetree adapters: {e}")
        sys.exit()

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
                    zotToRm(zotero_tree, rm_tree, folders)
                elif arg == "pull":
                    rmToZot(zotero_tree, rm_tree, read_folder)
                elif arg == "both":
                    zotToRm(zotero_tree, rm_tree, folders)
                    rmToZot(zotero_tree, rm_tree, read_folder)
                else:
                    logger.error("Invalid argument")
                    sys.exit()
    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":
    main()
