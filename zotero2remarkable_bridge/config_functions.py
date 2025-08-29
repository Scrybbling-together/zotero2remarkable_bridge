# config_functions.py
import logging

import yaml
from pyzotero import zotero
from webdav3.client import Client as wdClient

# Default constants. Might be useful for refining the setup process, for ex. opt-in to create default folders on RM.
DEFAULT_ROOT = "Zotero"
DEFAULT_READ = "read"
DEFAULT_UNREAD = "write"


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
def write_config(file_name):
    config_data = {}
    print("\nZotero to ReMarkable Bridge Setup\n" + "="*30)
    print(f"""
Folder structure on ReMarkable:
- You need a folder in the root of the device (default: {DEFAULT_ROOT})
- Inside it, you need two subfolders:
  1. An 'unread' folder for new documents from Zotero.
  2. A 'read' folder for documents you've finished reading.

You can name them as you wish. The default configuration is:
- Root folder: {DEFAULT_ROOT}
- Unread folder: {DEFAULT_UNREAD} (for new documents)
- Read folder: {DEFAULT_READ} (for finished documents)
""")
    
    use_defaults = input("Would you like to use these default folders? (y/n): ").lower()
    
    if use_defaults.startswith('y'):
        config_data["ROOT_FOLDER"] = DEFAULT_ROOT
        config_data["UNREAD_FOLDER"] = DEFAULT_UNREAD
        config_data["READ_FOLDER"] = DEFAULT_READ
    else:
        config_data["ROOT_FOLDER"] = input("Specify your root folder: ")
        print("\nSpecify your subfolder (without the leading '[ROOT]/')")
        config_data["UNREAD_FOLDER"] = "Zotero/" + input("Name for unread documents folder: ")
        config_data["READ_FOLDER"] = "Zotero/" + input("Name for read documents folder: ")
    # At this point we could ask if an automatic setup of the folders with rmapi should be done.
    print("\nNext, enter your Zotero library ID. You can find it on this page:")
    print("https://www.zotero.org/settings/security")
    print("Under Applications > user ID, \"Your user ID for use in API calls is {COPY THIS}\"")
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
    

def normalize_path(path: str) -> str:
    """Removes all leading and trailing slashes and whitespaces of a String."""
    match path:        
        case str(s) if s.startswith("/") or s.startswith(" "):
            return normalize_path(s[1:]) # recursively removes all leading slashes and whitespaces
        case str(s) if s.endswith("/") or s.endswith(" "):
            return normalize_path(s[:-1]) # recursively removes trailing whitespace
        case _:
            return path

def normalize_rm_path(path: str) -> str:
    """Normalizes a String and removes leading 'Zotero/' afterwards."""
    if normalize_path(path).lower().startswith("zotero/"):
        return normalize_path(path)[7:] # removes "zotero/" (case insensitive)
    else:
        return normalize_path(path)        
        

def validate_folder(folder: str, default: str) -> str:
    """Returns default if folder=="", otherwhise returns folder"""
    return default if not folder.strip() else folder

def get_folders(config_dict: dict[str, str]) -> dict[str, str]:
    """Returns dictionary containing the two full paths to the unread and read folder on RM.
    If any of the information in the config_dict is missing, this function will fall back to default values.
    """
    root_folder = normalize_path(validate_folder(
        config_dict.get("ROOT_FOLDER", ""), DEFAULT_ROOT))
    
    unread_folder = normalize_rm_path(validate_folder(
        config_dict.get("UNREAD_FOLDER", ""), DEFAULT_UNREAD))
    
    read_folder = normalize_rm_path(validate_folder(
        config_dict.get("READ_FOLDER", ""), DEFAULT_READ))
    
    return {
        "unread": f"/{root_folder}/{unread_folder}/", 
        "read": f"/{root_folder}/{read_folder}/"
    }       