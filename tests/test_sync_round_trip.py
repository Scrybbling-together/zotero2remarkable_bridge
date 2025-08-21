"""
Tests for sync round trip functionality using mock filetrees.
"""
import logging

from config_functions import load_config
from filetreeAdapters.RemarkableFiletreeAdapter import RemarkableFiletreeAdapter
from filetreeAdapters.ZoteroFiletreeAdapter import ZoteroFiletreeAdapter
from tree_state import MockTreeState
from zoteroRmBridge import zotToRm, rmToZot

VALID_RM_DOCUMENT = "tests/on computable numbers - RMPP - highlighter tool v6.rmn"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_rm_filetree():
    """Sets up a minimum reMarkable filetree for use with zot2rm"""
    rm = MockTreeState()

    rm.create_collection(["Zotero"])
    rm.create_collection(["Zotero", "unread"])
    rm.create_collection(["Zotero", "read"])

    return rm


def test_sync_round_trip_real():
    zot, webdav, folders = load_config("config.yml")
    zotero_tree = ZoteroFiletreeAdapter(zotero_client=zot)
    rm_tree = RemarkableFiletreeAdapter()

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
    assert rm_tree.delete_node("Zotero/unread/" + paper_name)
    result = rm_tree.create_file("Zotero/read/" + paper_name + ".pdf", pdf_content, "application/pdf")
    assert result

    rmToZot(zotero=zotero_tree, rm=rm_tree, read_folder="read")
    children = zotero_tree.list_children(handle)
    assert len(children) == 2
    for child in children:
        print(f"child of {handle} is {child}#{child.handle}")
        assert "annotated" in zotero_tree.get_tags(child.handle)

#
# def test_sync_round_trip():
#     """Test complete round trip: Zotero tagged item → reMarkable → back to Zotero with annotations"""
#     zotero_tree = MockTreeState()
#     rm_tree = setup_rm_filetree()
#
#     paper_name = "On computable numbers"
#
#     zotero_tree.create_collection([paper_name])
#
#     initial_pdf_content = b"%PDF-1.4 Original paper content..."
#     zotero_tree.create_file([paper_name, "On computable numbers.pdf"], initial_pdf_content, "application/pdf")
#     zotero_tree.add_tags([paper_name], ["to_sync"])
#
#     assert "synced"  not in zotero_tree.get_tags([paper_name])
#     zotToRm(zotero=zotero_tree, rm=rm_tree, folders={
#         "unread": "unread",
#         "read": "read"
#     })
#
#     assert zotero_tree.has_tags([paper_name], ["synced"])
#     assert rm_tree.is_file(["Zotero", "unread", paper_name + ".pdf"])
#
#     # In a real scenario, someone would make some annotations on-device for the newly created file
#     # Afterward, when done annotating, they move it to the read folder
#
#     # these two operations mimic an "mv" from unread to read
#     rm_tree.delete_node(["Zotero", "unread", paper_name + ".pdf"])
#     # mimic the real reMarkable api by putting an .rmn in the place of the file
#     # rmapi doesn't give PDFs, it gives .rmn files
#     with open(VALID_RM_DOCUMENT, "rb") as f:
#         rm_tree.create_file("Zotero/read/" + paper_name + ".pdf", f.read(), "application/pdf")
#
#     rmToZot(zotero=zotero_tree, rm=rm_tree, read_folder="read")
#     assert "annotated" in zotero_tree.get_tags([paper_name, paper_name + ".pdf"])
#     assert "annotated" in zotero_tree.get_tags([paper_name, paper_name + ".md"])



