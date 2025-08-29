from zotero2remarkable_bridge.config_functions import normalize_path, normalize_rm_path, validate_folder, get_folders, DEFAULT_READ, DEFAULT_ROOT, DEFAULT_UNREAD

def test_normalize_path():
    assert normalize_path("read") == "read"
    assert normalize_path("/read") == "read"
    assert normalize_path("read/") == "read"
    assert normalize_path("//read//") == "read"
    assert normalize_path(" read") == "read"
    assert normalize_path("read ") == "read"
    assert normalize_path("  read  ") == "read"
    assert normalize_path("  / /read / ") == "read"
    assert normalize_path("/read/foo/") == "read/foo"
    assert normalize_path("read/foo /bar /") == "read/foo /bar"


def test_normalize_rm_path():
    assert normalize_rm_path("") == ""
    assert normalize_rm_path("read") == "read"
    assert normalize_rm_path("/read") == "read"
    assert normalize_rm_path("zotero") == "zotero"
    assert normalize_rm_path("Zotero/read") == "read"
    assert normalize_rm_path("zotero/read") == "read"
    assert normalize_rm_path("ZOTERO/read") == "read"
    assert normalize_rm_path("Zotero/read/foo") == "read/foo"
    assert normalize_rm_path("zotero/read/") == "read"
    assert normalize_rm_path("//zotero/read") == "read"
    assert normalize_rm_path(" /zotero/read") == "read"
    assert normalize_rm_path("  /zotero/read") == "read"
    assert normalize_rm_path("  //zotero/read") == "read"
    assert normalize_rm_path(" /zotero/read ") == "read"
    assert normalize_rm_path("foo/zotero/read") == "foo/zotero/read"


def test_validate_folder():
    assert validate_folder("foo", "bar") == "foo"
    assert validate_folder(" foo", "bar") == " foo"
    assert validate_folder("", "bar") == "bar"
    assert validate_folder(" ", "bar") == "bar"
    

def test_get_folders():
    # All information in dict
    assert get_folders({"ROOT_FOLDER": "foo", 
                        "UNREAD_FOLDER": "bar",
                        "READ_FOLDER": "zee"}) == {"unread": "/foo/bar/",
                                                     "read": "/foo/zee/"}
    # Empty dict
    assert get_folders({}) == {"unread": f"/{DEFAULT_ROOT}/{DEFAULT_UNREAD}/",
                               "read": f"/{DEFAULT_ROOT}/{DEFAULT_READ}/"}
    # ROOT_FOLDER empty
    assert get_folders({"ROOT_FOLDER": "", 
                        "UNREAD_FOLDER": "bar",
                        "READ_FOLDER": "zee"}) == {"unread": f"/{DEFAULT_ROOT}/bar/",
                                                     "read": f"/{DEFAULT_ROOT}/zee/"}
    # Missing entry for ROOT_FOLDER
    assert get_folders({"UNREAD_FOLDER": "bar",
                        "READ_FOLDER": "zee"}) == {"unread": f"/{DEFAULT_ROOT}/bar/",
                                                     "read": f"/{DEFAULT_ROOT}/zee/"}
    # UNREAD_FOLDER empty
    assert get_folders({"ROOT_FOLDER": "foo", 
                        "UNREAD_FOLDER": "",
                        "READ_FOLDER": "zee"}) == {"unread": f"/foo/{DEFAULT_UNREAD}/",
                                                     "read": "/foo/zee/"}    
    # Missing entry for UNREAD-FOLDER
    assert get_folders({"ROOT_FOLDER": "foo", 
                        "READ_FOLDER": "zee"}) == {"unread": f"/foo/{DEFAULT_UNREAD}/",
                                                     "read": "/foo/zee/"}
    # READ_FOLDER empty
    assert get_folders({"ROOT_FOLDER": "foo", 
                        "UNREAD_FOLDER": "bar",
                        "READ_FOLDER": ""}) == {"unread": "/foo/bar/",
                                                     "read": f"/foo/{DEFAULT_READ}/"}
    # Missing entry for READ_FOLDER
    assert get_folders({"ROOT_FOLDER": "foo", 
                        "UNREAD_FOLDER": "bar"}) == {"unread": "/foo/bar/",
                                                     "read": f"/foo/{DEFAULT_READ}/"}