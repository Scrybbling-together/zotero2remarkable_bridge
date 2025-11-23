"""
Mock version of the sync round trip test using in-memory APIs.
"""

import logging
import pytest

from tests.mocks import MockZoteroAPI, MockReMarkableAPI
from zrm.zotero_rm_bridge import zotToRm, rmToZot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_PDF = "tests/On computable numbers - Turing.pdf"


@pytest.mark.mock
def test_sync_round_trip_mock():
    """Mock version of the e2e sync round trip test."""
    # Set up mock APIs
    mock_zotero = MockZoteroAPI()
    mock_rm = MockReMarkableAPI(
        files={}, folders={"", "Zotero", "Zotero/unread", "Zotero/read"}
    )
    folders = {"unread": "unread", "read": "read"}

    paper_name = "On computable numbers"

    # Step 1: Create collection in Zotero
    handle = mock_zotero.create_item([paper_name])

    # Step 2: Create file attachment
    with open(TEST_PDF, "rb") as f:
        pdf_content = f.read()
    mock_zotero.create_file(handle, "On computable numbers.pdf", pdf_content)
    mock_zotero.add_tags(handle, ["to_sync"])

    # Verify initial state
    assert "synced" not in mock_zotero.get_tags(handle)

    # Step 3: Push to reMarkable
    zotToRm(zotero=mock_zotero, rm=mock_rm, folders=folders)

    # Verify sync completed and tags were updated
    assert mock_zotero.has_tags(handle, ["synced"])
    assert mock_rm.is_file("Zotero/unread/On computable numbers.pdf")

    # Step 4: Simulate moving file from unread to read (user action)
    # In a real scenario, someone would make annotations and move the file
    # The API would have converted the PDF to rmDoc format internally
    assert mock_rm.delete_file_or_folder("Zotero/unread/On computable numbers.pdf")

    # When we download from reMarkable, we get the rmDoc (which contains the PDF + annotations)
    with open(
        "tests/on computable numbers - RMPP - highlighter tool v6.rmn", "rb"
    ) as f:
        rmdoc_content = f.read()

    result = mock_rm.upload_file("Zotero/read/On computable numbers.pdf", rmdoc_content)
    assert result

    # Step 5: Pull from reMarkable back to Zotero
    rmToZot(zotero=mock_zotero, rm=mock_rm, read_folder="read")

    # Step 6: Verify annotations were processed
    children = mock_zotero.list_children(handle)
    assert len(children) == 2
    for child in children:
        assert "annotated" in mock_zotero.get_tags(child.handle)


@pytest.mark.mock
def test_multiple_pdfs_in_one_collection():
    """Test syncing multiple PDFs within a single collection."""
    mock_zotero = MockZoteroAPI()
    mock_rm = MockReMarkableAPI(
        files={}, folders={"", "Zotero", "Zotero/unread", "Zotero/read"}
    )
    folders = {"unread": "unread", "read": "read"}

    item_name = "Multiple PDF attachments"

    # Create collection
    item_handle = mock_zotero.create_item([item_name])
    mock_zotero.add_tags(item_handle, ["to_sync"])

    # Create multiple PDF attachments
    pdf_files = ["paper1.pdf", "paper2.pdf", "paper3.pdf"]
    with open(
        TEST_PDF,
        "rb",
    ) as f:
        pdf_content = f.read()

    for pdf_name in pdf_files:
        mock_zotero.create_file(item_handle, pdf_name, pdf_content)

    # Verify initial state - collection has to_sync tag but not synced
    assert mock_zotero.has_tags(item_handle, ["to_sync"])
    assert not mock_zotero.has_tags(item_handle, ["synced"])

    # Sync to reMarkable
    zotToRm(zotero=mock_zotero, rm=mock_rm, folders=folders)

    # Verify all files were uploaded and collection tagged as synced
    assert mock_zotero.has_tags(item_handle, ["synced"])
    for pdf_name in pdf_files:
        assert mock_rm.is_file(f"Zotero/unread/{pdf_name}")


@pytest.mark.mock
def test_multiple_collections_sync_independently():
    """Test that multiple items with to_sync tags sync independently."""
    mock_zotero = MockZoteroAPI()
    mock_rm = MockReMarkableAPI(
        files={}, folders={"", "Zotero", "Zotero/unread", "Zotero/read"}
    )
    folders = {"unread": "unread", "read": "read"}

    # Create multiple items
    items = ["Collection A", "Collection B", "Collection C"]
    item_handles = []

    with open(
        TEST_PDF,
        "rb",
    ) as f:
        pdf_content = f.read()

    for collection_name in items:
        handle = mock_zotero.create_item([collection_name])
        item_handles.append(handle)

        # Add PDF to each collection
        mock_zotero.create_file(handle, f"{collection_name}.pdf", pdf_content)
        mock_zotero.add_tags(handle, ["to_sync"])

    # Verify initial state
    for handle in item_handles:
        assert mock_zotero.has_tags(handle, ["to_sync"])
        assert not mock_zotero.has_tags(handle, ["synced"])

    # Sync all items
    zotToRm(zotero=mock_zotero, rm=mock_rm, folders=folders)

    # Verify all items were synced independently
    for i, handle in enumerate(item_handles):
        assert mock_zotero.has_tags(handle, ["synced"])
        assert mock_rm.is_file(f"Zotero/unread/{items[i]}.pdf")


@pytest.mark.mock
def test_missing_unread_folder_warns_and_fails(caplog):
    """Test that missing Zotero/unread folder causes upload to fail gracefully."""
    mock_zotero = MockZoteroAPI()
    # Missing "Zotero/unread" folder - only has base folders
    mock_rm = MockReMarkableAPI(files={}, folders={"", "Zotero", "Zotero/read"})
    folders = {"unread": "unread", "read": "read"}

    # Create item with attachment
    item_handle = mock_zotero.create_item(["Test Paper"])
    mock_zotero.add_tags(item_handle, ["to_sync"])

    with open(
        TEST_PDF,
        "rb",
    ) as f:
        pdf_content = f.read()
    mock_zotero.create_file(item_handle, "test.pdf", pdf_content)

    # Verify initial state
    assert mock_zotero.has_tags(item_handle, ["to_sync"])
    assert not mock_zotero.has_tags(item_handle, ["synced"])

    # Capture logs during sync attempt
    with caplog.at_level(logging.INFO):
        zotToRm(zotero=mock_zotero, rm=mock_rm, folders=folders)

    # Verify item was NOT tagged as synced due to upload failure
    assert not mock_zotero.has_tags(item_handle, ["synced"])
    # File should not exist since upload failed
    assert not mock_rm.is_file("Zotero/unread/test.pdf")

    # Verify expected error log message is present
    assert any(
        "Failed to upload" in record.message
        for record in caplog.records
        if record.levelname == "ERROR"
    )


@pytest.mark.mock
def test_missing_read_folder_handled_gracefully(caplog):
    """Test that missing Zotero/read folder is handled gracefully during pull."""
    mock_zotero = MockZoteroAPI()
    # Missing "Zotero/read" folder - only has base folders
    mock_rm = MockReMarkableAPI(files={}, folders={"", "Zotero", "Zotero/unread"})

    # Capture logs during pull attempt
    with caplog.at_level(logging.INFO):
        rmToZot(zotero=mock_zotero, rm=mock_rm, read_folder="read")

    # Verify expected info log message is present about missing folder
    assert any(
        "does not exist on reMarkable" in record.message
        for record in caplog.records
        if record.levelname == "INFO"
    )


@pytest.mark.mock
def test_remarkable_api_unavailable_preserves_tags(caplog):
    """Test that when reMarkable API is unavailable, sync fails gracefully and preserves original tags."""
    mock_zotero = MockZoteroAPI()
    mock_rm = MockReMarkableAPI(
        files={}, folders={"", "Zotero", "Zotero/unread", "Zotero/read"}
    ).api_unavailable()
    folders = {"unread": "unread", "read": "read"}

    # Create item with attachment
    item_handle = mock_zotero.create_item(["Test Paper"])
    mock_zotero.add_tags(item_handle, ["to_sync"])

    with open(
        TEST_PDF,
        "rb",
    ) as f:
        pdf_content = f.read()
    mock_zotero.create_file(item_handle, "test.pdf", pdf_content)

    # Verify initial state
    assert mock_zotero.has_tags(item_handle, ["to_sync"])
    assert not mock_zotero.has_tags(item_handle, ["synced"])

    # Attempt sync with unavailable API
    with caplog.at_level(logging.INFO):
        zotToRm(zotero=mock_zotero, rm=mock_rm, folders=folders)

    # Verify tags are preserved - item should still have to_sync, not synced
    assert mock_zotero.has_tags(item_handle, ["to_sync"])
    assert not mock_zotero.has_tags(item_handle, ["synced"])

    # Verify error was logged
    assert any(
        "reMarkable API is unavailable" in record.message
        for record in caplog.records
        if record.levelname == "ERROR"
    )
    assert any(
        "Failed to upload" in record.message
        for record in caplog.records
        if record.levelname == "ERROR"
    )


@pytest.mark.mock
def test_duplicate_file_overwrites(caplog):
    """Test that pushing the same file again overwrites and logs appropriately."""
    mock_zotero = MockZoteroAPI()
    mock_rm = MockReMarkableAPI(
        files={}, folders={"", "Zotero", "Zotero/unread", "Zotero/read"}
    )
    folders = {"unread": "unread", "read": "read"}

    # Create item with attachment
    item_handle = mock_zotero.create_item(["Test Paper"])
    mock_zotero.add_tags(item_handle, ["to_sync"])

    with open(
        TEST_PDF,
        "rb",
    ) as f:
        pdf_content = f.read()
    mock_zotero.create_file(item_handle, "duplicate_test.pdf", pdf_content)

    # First sync - should succeed
    with caplog.at_level(logging.INFO):
        zotToRm(zotero=mock_zotero, rm=mock_rm, folders=folders)

    assert mock_zotero.has_tags(item_handle, ["synced"])
    assert mock_rm.is_file("Zotero/unread/duplicate_test.pdf")
    original_content = mock_rm.get_file_content("Zotero/unread/duplicate_test.pdf")

    # Clear logs for second attempt
    caplog.clear()

    # Create another item with same filename
    item_handle_2 = mock_zotero.create_item(["Another Paper"])
    mock_zotero.add_tags(item_handle_2, ["to_sync"])

    # Different content to verify overwrite
    modified_content = b"This is different content for overwrite test"
    mock_zotero.create_file(item_handle_2, "duplicate_test.pdf", modified_content)

    # Second sync - should overwrite
    with caplog.at_level(logging.INFO):
        zotToRm(zotero=mock_zotero, rm=mock_rm, folders=folders)

    # Verify second item was tagged as synced
    assert mock_zotero.has_tags(item_handle_2, ["synced"])

    # Verify file was overwritten with new content
    new_content = mock_rm.get_file_content("Zotero/unread/duplicate_test.pdf")
    assert new_content != original_content
    assert new_content == modified_content

    # Verify upload success was logged (overwrite is transparent)
    assert any(
        "Uploaded" in record.message
        and "duplicate_test.pdf" in record.message
        and "to reMarkable" in record.message
        for record in caplog.records
        if record.levelname == "INFO"
    )


@pytest.mark.mock
def test_rmToZot_updates_existing_markdown_attachment():
    """Test that rmToZot updates existing markdown attachment when PDF already exists."""
    mock_zotero = MockZoteroAPI()
    mock_rm = MockReMarkableAPI(
        files={}, folders={"", "Zotero", "Zotero/unread", "Zotero/read"}
    )

    paper_name = "On computable numbers"

    # Create item in Zotero with synced tag
    handle = mock_zotero.create_item([paper_name])
    mock_zotero.add_tags(handle, ["synced"])

    # Create existing PDF attachment
    with open(
        TEST_PDF,
        "rb",
    ) as f:
        pdf_content = f.read()
    mock_zotero.create_file(handle, "On computable numbers.pdf", pdf_content)

    # Create existing markdown attachment with original content
    original_md_content = b"# Original markdown\nSome existing notes."
    md_attachment_handle = mock_zotero.create_file(
        handle, "On computable numbers.md", original_md_content
    )

    # Add annotated file to reMarkable's read folder
    with open(
        "tests/on computable numbers - RMPP - highlighter tool v6.rmn", "rb"
    ) as f:
        rmdoc_content = f.read()
    mock_rm.upload_file("Zotero/read/On computable numbers.pdf", rmdoc_content)

    # Call rmToZot to pull from reMarkable
    rmToZot(zotero=mock_zotero, rm=mock_rm, read_folder="read")

    # Verify that the existing markdown attachment was updated (remarks includes a timestamp which'll be different)
    updated_content = mock_zotero.get_file_content(md_attachment_handle)
    assert (
        updated_content != original_md_content
    ), "Markdown content should have changed due to timestamp"

    # Verify that the markdown attachment has the "annotated" tag
    md_tags = mock_zotero.get_tags(md_attachment_handle)
    assert "annotated" in md_tags, "Markdown attachment should have annotated tag"


@pytest.mark.mock
def test_rmToZot_deletes_files_after_successful_sync():
    """Test that rmToZot deletes files from reMarkable after successful sync."""
    mock_zotero = MockZoteroAPI()
    mock_rm = MockReMarkableAPI(
        files={}, folders={"", "Zotero", "Zotero/unread", "Zotero/read"}
    )

    paper_name = "On computable numbers"

    # Create item in Zotero with synced tag
    handle = mock_zotero.create_item([paper_name])
    mock_zotero.add_tags(handle, ["synced"])

    # Create existing PDF attachment
    with open(
        TEST_PDF,
        "rb",
    ) as f:
        pdf_content = f.read()
    mock_zotero.create_file(handle, "On computable numbers.pdf", pdf_content)

    # Add annotated file to reMarkable's read folder
    with open(
        "tests/on computable numbers - RMPP - highlighter tool v6.rmn", "rb"
    ) as f:
        rmdoc_content = f.read()
    mock_rm.upload_file("Zotero/read/On computable numbers.pdf", rmdoc_content)

    # Verify file exists before sync
    assert mock_rm.is_file("Zotero/read/On computable numbers.pdf")

    # First call to rmToZot - should process and delete the file
    rmToZot(zotero=mock_zotero, rm=mock_rm, read_folder="read")

    # Verify file was deleted from reMarkable after successful sync
    assert not mock_rm.is_file("Zotero/read/On computable numbers.pdf")

    # Second call to rmToZot - should find no files to sync
    rmToZot(zotero=mock_zotero, rm=mock_rm, read_folder="read")

    # Verify read folder is empty (no files to process)
    files_in_read_folder = mock_rm.list_children("Zotero/read")
    assert len(files_in_read_folder) == 0
