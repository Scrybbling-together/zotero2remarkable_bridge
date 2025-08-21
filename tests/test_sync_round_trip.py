"""
Tests for sync round trip functionality using mock filetrees.
"""
import logging


from zrm.config_functions import load_config
from zrm.filetreeAdapters.ReMarkableAPI import ReMarkableAPI
from zrm.filetreeAdapters.ZoteroAPI import ZoteroAPI
from zrm.zotero_rm_bridge import zotToRm, rmToZot

VALID_RM_DOCUMENT = "tests/on computable numbers - RMPP - highlighter tool v6.rmn"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sync_round_trip_real():
    zot, webdav, folders = load_config("config.yml")
    zotero_tree = ZoteroAPI(zotero_client=zot)
    rm_tree = ReMarkableAPI()

    paper_name = "On computable numbers"

    handle = zotero_tree.create_collection([paper_name])

    with open("1936 On Computable Numbers, with an Application to the Entscheidungsproblem - A. M. Turing _remarks.pdf", "rb") as f:
        pdf_content = f.read()
    zotero_tree.create_file(handle, "On computable numbers.pdf", pdf_content, "application/pdf")
    zotero_tree.add_tags(handle, ["to_sync"])

    assert "synced" not in zotero_tree.get_tags(handle)
    zotToRm(zotero=zotero_tree, rm=rm_tree, folders={
        "unread": "unread",
        "read": "read"
    })

    assert zotero_tree.has_tags(handle, ["synced"])
    assert rm_tree.is_file("Zotero/unread/" + paper_name + ".pdf")

    # In a real scenario, someone would make some annotations on-device for the newly created file
    # Afterward, when done annotating, they move it to the read folder
    # these two operations mimic an "mv" from unread to read
    assert rm_tree.delete_file_or_folder("Zotero/unread/" + paper_name)
    result = rm_tree.create_file("Zotero/read/" + paper_name + ".pdf", pdf_content, "application/pdf")
    assert result

    rmToZot(zotero=zotero_tree, rm=rm_tree, read_folder="read")
    children = zotero_tree.list_children(handle)
    assert len(children) == 2
    for child in children:
        assert "annotated" in zotero_tree.get_tags(child.handle)

