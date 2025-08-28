# config_functions.py
import logging

import yaml
from pyzotero import zotero
from webdav3.client import Client as wdClient

logger = logging.getLogger("zotero_rM_bridge.config")


def load_config(config_file):
    with open(config_file, "r") as stream:
        try:
            config_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logger.exception(exc)

    zot = zotero.Zotero(config_dict["LIBRARY_ID"], config_dict["LIBRARY_TYPE"], config_dict["API_KEY"])
    folders = get_folders(config_dict)
    if config_dict["USE_WEBDAV"] == "True":
        webdav_data = {
            "webdav_hostname": config_dict["WEBDAV_HOSTNAME"],
            "webdav_login": config_dict["WEBDAV_USER"],
            "webdav_password": config_dict["WEBDAV_PWD"],
            "webdav_timeout": 300
        }
        webdav = wdClient(webdav_data)
    else:
        webdav = False
    return zot, webdav, folders


def write_config(file_name):
    config_data = {}
    input("Couldn't find config file. Let's create one! Press Enter to continue...\n")
    print("On your ReMarkable you should have created a folder called Zotero in the root directory.\nIn the following specify ONLY the names of the subfolders, e. g 'read' instead of 'zotero/read'.\n")
    # TODO: Ask user for root folder config_data["ROOT-FOLDER"] = input("")
    config_data["UNREAD_FOLDER"] = input("Which ReMarkable folder should files be synced to? ")
    config_data["READ_FOLDER"] = input("Which ReMarkable folder should files be synced from? ")
    print("You can find your library ID on this page")
    print("Under Applications > user ID, \"Your user ID for use in API calls is {COPY THIS}\"")
    print("https://www.zotero.org/settings/security")
    config_data["LIBRARY_ID"] = input("Enter Zotero library ID: ")
    config_data["LIBRARY_TYPE"] = input("Enter Zotero library type (user/group): ")
    config_data["API_KEY"] = input("Enter Zotero API key: ")
    config_data["USE_WEBDAV"] = input("Does Zotero use WebDAV storage for file sync (True/False)? ")
    if config_data["USE_WEBDAV"].lower() == "true":
        config_data["WEBDAV_HOSTNAME"] = input("Enter path to WebDAV folder (same as in Zotero config): ")
        config_data["WEBDAV_USER"] = input("Enter WebDAV username: ")
        config_data["WEBDAV_PWD"] = input("Enter WebDAV password (consider creating an app token as password is safed in clear text): ")

    with open(file_name, "w") as file:
        yaml.dump(config_data, file)
        if config_data["USE_WEBDAV"].lower() != "true":
            file.write("\n## Uncomment the following 3 lines if you want to use WebDAV")
            file.write("\n#WEBDAV_HOSTNAME: ")
            file.write("\n#WEBDAV_USER: ")
            file.write("\n#WEBDAV_PWD: ")
    logger.info(f"Config written to {file_name}\n If something went wrong, please edit config manually.")


# Default constants. Might be useful for refining the setup process, for ex. opt-in to create default folders on RM.
DEFAULT_ROOT = "Zotero"
DEFAULT_READ = "read"
DEFAULT_UNREAD = "write"

def get_folders(config_dict: dict[str, str]) -> dict[str, str]:
    """Creates dict of folders. Uses dict.get() function that sets default values if key doesn't exist.
    Normalizes every path, stripping it of whitespaces and slashes. Subfolders are also stripped of leading 'Zotero/'.
    TODO: Maybe make this robust against empty entries as well?
    """
    root_folder = normalize_path(config_dict.get("ROOT-FOLDER", DEFAULT_ROOT))
    unread_folder = normalize_rm_path(config_dict.get("UNREAD_FOLDER", DEFAULT_UNREAD))
    read_folder = normalize_rm_path(config_dict.get("READ_FOLDER", DEFAULT_READ))
    return{"unread": "/" + root_folder + "/" + unread_folder + "/", "read": "/" + root_folder + "/" + read_folder + "/"}


def normalize_rm_path(path: str) -> str:
    """Performs cleanup of folder names, mainly for cases like 'Zotero/read' which should just be 'read'"""
    if normalize_path(path).lower().startswith("zotero/"):
        return path[7:] # removes "zotero/" (case insensitive)
    else:
        return normalize_path(path)
    

def normalize_path(path: str) -> str:
    match path:        
        case str(s) if s.startswith("/") or s.startswith(" "):
            return normalize_path(s[1:]) # recursively removes all leading slashes and whitespaces
        case str(s) if s.endswith("/") or s.endswith(" "):
            return normalize_path(s[:-1]) # recursively removes trailing whitespace
        case _:
            return path