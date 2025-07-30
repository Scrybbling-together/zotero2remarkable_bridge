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
    input("Couldn't find config file. Let's create one! Press Enter to continue...")
    config_data["UNREAD_FOLDER"] = input("Which ReMarkable folder should files be synced to? ")
    config_data["READ_FOLDER"] = input("Which ReMarkable folder should files be synced from? ")
    print("You can find your library ID on this page")
    print("Under Applications > user ID, \"Your user ID for use in API calls is {COPY THIS}\"")
    print("https://www.zotero.org/settings/security")
    config_data["LIBRARY_ID"] = input("Enter Zotero library ID: ")
    config_data["LIBRARY_TYPE"] = input("Enter Zotero library type (user/group): ")
    config_data["API_KEY"] = input("Enter Zotero API key: ")
    config_data["USE_WEBDAV"] = input("Does Zotero use WebDAV storage for file sync (True/False)? ")
    if config_data["USE_WEBDAV"] == "True":
        config_data["WEBDAV_HOSTNAME"] = input("Enter path to WebDAV folder (same as in Zotero config): ")
        config_data["WEBDAV_USER"] = input("Enter WebDAV username: ")
        config_data["WEBDAV_PWD"] = input("Enter WebDAV password (consider creating an app token as password is safed in clear text): ")

    with open(file_name, "w") as file:
        yaml.dump(config_data, file)
    logger.info(f"Config written to {file_name}\n If something went wrong, please edit config manually.")

