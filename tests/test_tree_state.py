"""
Simple tests to verify the MockTreeState implementation
"""
import pytest
from tree_state import MockTreeState


def test_basic_operations():
    tree = MockTreeState()
    
    # Root exists by default
    assert tree.node_exists([])
    assert tree.is_collection([])
    
    # Create collections
    assert tree.create_collection(["items"])
    assert tree.create_collection(["items", "paper1"])
    assert tree.create_collection(["items", "paper1", "attachments"])
    
    # Verify structure
    assert tree.node_exists(["items"])
    assert tree.is_collection(["items"])
    assert tree.list_children([]) == ["items"]
    assert tree.list_children(["items"]) == ["paper1"]
    
    # Create file
    content = b"PDF content here"
    assert tree.create_file(["items", "paper1", "attachments", "doc.pdf"], content, "application/pdf")
    assert tree.is_file(["items", "paper1", "attachments", "doc.pdf"])
    assert tree.get_file_content(["items", "paper1", "attachments", "doc.pdf"]) == content
    assert tree.get_file_content_type(["items", "paper1", "attachments", "doc.pdf"]) == "application/pdf"


def test_tags():
    tree = MockTreeState()
    tree.create_collection(["items"])
    tree.create_collection(["items", "paper1"])
    
    # Add tags
    assert tree.add_tags(["items", "paper1"], ["to_sync", "important"])
    assert tree.has_tags(["items", "paper1"], ["to_sync"])
    assert tree.has_tags(["items", "paper1"], ["important"])
    assert tree.has_tags(["items", "paper1"], ["to_sync", "important"])
    assert not tree.has_tags(["items", "paper1"], ["nonexistent"])
    
    # Get tags
    tags = tree.get_tags(["items", "paper1"])
    assert "to_sync" in tags
    assert "important" in tags
    
    # Find nodes with tag
    results = tree.find_nodes_with_tag("to_sync")
    assert ["items", "paper1"] in results
    
    # Remove tags
    assert tree.remove_tags(["items", "paper1"], ["to_sync"])
    assert not tree.has_tags(["items", "paper1"], ["to_sync"])
    assert tree.has_tags(["items", "paper1"], ["important"])


def test_metadata():
    tree = MockTreeState()
    tree.create_collection(["items"])
    
    # Set metadata
    assert tree.set_metadata(["items"], "created", "2024-01-01")
    assert tree.set_metadata(["items"], "author", "test")
    
    # Get metadata
    assert tree.get_metadata(["items"], "created") == "2024-01-01"
    assert tree.get_metadata(["items"], "author") == "test"
    assert tree.get_metadata(["items"], "nonexistent") is None
    
    # Get all metadata
    all_meta = tree.get_all_metadata(["items"])
    assert all_meta["created"] == "2024-01-01"
    assert all_meta["author"] == "test"


def test_error_conditions():
    tree = MockTreeState()
    
    # Cannot create without parent
    assert not tree.create_collection(["nonexistent", "child"])
    assert not tree.create_file(["nonexistent", "file.txt"], b"content")
    
    # Cannot create duplicate
    tree.create_collection(["test"])
    assert not tree.create_collection(["test"])  # Already exists
    
    # File operations on non-files should raise
    tree.create_collection(["folder"])
    with pytest.raises(ValueError):
        tree.get_file_content(["folder"])
    
    # Collection operations on non-collections should raise
    tree.create_file(["test.txt"], b"content")
    with pytest.raises(ValueError):
        tree.list_children(["test.txt"])


def test_deletion():
    tree = MockTreeState()
    tree.create_collection(["items"])
    tree.create_file(["test.txt"], b"content")
    
    # Delete file
    assert tree.delete_node(["test.txt"])
    assert not tree.node_exists(["test.txt"])
    
    # Delete collection
    assert tree.delete_node(["items"])
    assert not tree.node_exists(["items"])
    
    # Cannot delete non-existent
    assert not tree.delete_node(["nonexistent"])


if __name__ == "__main__":
    test_basic_operations()
    test_tags()
    test_metadata()
    test_error_conditions()  
    test_deletion()
    print("All tests passed!")