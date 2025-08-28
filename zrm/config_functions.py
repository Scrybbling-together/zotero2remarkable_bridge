# config_functions.py
import logging

import yaml
from pyzotero import zotero
from webdav3.client import Client as wdClient

logger = logging.getLogger(__name__)

def load_config(config_file):
    with open(config_file, "r") as stream:
        try:
            config_dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logger.exception(exc)
    zot = zotero.Zotero(config_dict["LIBRARY_ID"], config_dict["LIBRARY_TYPE"], config_dict["API_KEY"])
    folders = {"unread": config_dict["UNREAD_FOLDER"], "read": config_dict["READ_FOLDER"]}
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
    config_data["UNREAD_FOLDER"] = normalize_rm_path(input("Which ReMarkable folder should files be synced to? "))
    config_data["READ_FOLDER"] = normalize_rm_path(input("Which ReMarkable folder should files be synced from? "))
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


def normalize_rm_path(folder_name: str) -> str:
    """Performs cleanup of folder names, mainly for cases like 'Zotero/read' which should just be 'read'"""
    match folder_name:        
        case str(s) if s.startswith("/") or s.startswith(" "):
            return normalize_rm_path(s[1:]) # recursively removes all leading slashes and whitespaces
        case str(s) if s.endswith(" "):
            return normalize_rm_path(s[:-1]) # recursively removes trailing whitespace
        case str(s) if s.lower().startswith("zotero/"):
            return s[7:] # removes "zotero/" (case insensitive)
        case _:
            return folder_name