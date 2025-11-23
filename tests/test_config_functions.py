from zrm.config_functions import normalize_rm_path


def test_normalize_rm_path():
    assert normalize_rm_path("") == ""
    assert normalize_rm_path("read") == "read"
    assert normalize_rm_path("/read") == "read"
    assert normalize_rm_path("zotero") == "zotero"
    assert normalize_rm_path("Zotero/read") == "read"
    assert normalize_rm_path("zotero/read") == "read"
    assert normalize_rm_path("ZOTERO/read") == "read"
    assert normalize_rm_path("Zotero/read/foo") == "read/foo"
    assert normalize_rm_path("zotero/read/") == "read/"
    assert normalize_rm_path("//zotero/read") == "read"
    assert normalize_rm_path(" /zotero/read") == "read"
    assert normalize_rm_path("  /zotero/read") == "read"
    assert normalize_rm_path("  //zotero/read") == "read"
    assert normalize_rm_path(" /zotero/read ") == "read"
    assert normalize_rm_path("foo/zotero/read") == "foo/zotero/read"
