from zotero2remarkable_bridge.config_functions import normalize_remarkable_path

def test_normalize_remarkable_path():
    assert normalize_remarkable_path("") == ""
    assert normalize_remarkable_path("read") == "read"
    assert normalize_remarkable_path("/read") == "read"
    assert normalize_remarkable_path("zotero") == "zotero"
    assert normalize_remarkable_path("Zotero/read") == "read"
    assert normalize_remarkable_path("zotero/read") == "read"
    assert normalize_remarkable_path("ZOTERO/read") == "read"
    assert normalize_remarkable_path("Zotero/read/foo") == "read/foo"
    assert normalize_remarkable_path("zotero/read/") == "read/"
    assert normalize_remarkable_path("//zotero/read") == "read"
    assert normalize_remarkable_path(" /zotero/read") == "read"
    assert normalize_remarkable_path("  /zotero/read") == "read"
    assert normalize_remarkable_path("  //zotero/read") == "read"
    assert normalize_remarkable_path(" /zotero/read ") == "read"
    assert normalize_remarkable_path("foo/zotero/read") == "foo/zotero/read"