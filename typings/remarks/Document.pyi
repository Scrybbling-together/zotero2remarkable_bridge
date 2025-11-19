from _typeshed import Incomplete
from collections.abc import Generator
from remarks.dimensions import (
    REMARKABLE_DOCUMENT as REMARKABLE_DOCUMENT,
    ReMarkableDimensions as ReMarkableDimensions,
)
from remarks.utils import (
    get_document_filetype as get_document_filetype,
    get_document_tags as get_document_tags,
    get_page_tags as get_page_tags,
    get_pages_data as get_pages_data,
    get_visible_name as get_visible_name,
    is_duplicate_page as is_duplicate_page,
    is_inserted_page as is_inserted_page,
    list_ann_rm_files as list_ann_rm_files,
)

class Document:
    metadata_path: Incomplete
    doc_type: Incomplete
    name: Incomplete
    rm_tags: Incomplete
    rm_annotation_files: Incomplete
    def __init__(self, metadata_path) -> None: ...
    # def open_source_pdf(self) -> fitz.Document: ...
    def pages(self) -> Generator[Incomplete]: ...
    def get_page_tags_for_page(self, page_uuid: str) -> list[str]: ...

def sanitize_filename(filename: str) -> str: ...
