import pathlib
from .Document import Document as Document
from .metadata import (
    ReMarkableAnnotationsFileHeaderVersion as ReMarkableAnnotationsFileHeaderVersion,
)
from .utils import (
    get_document_filetype as get_document_filetype,
    get_ui_path as get_ui_path,
    get_visible_name as get_visible_name,
    is_document as is_document,
)

def run_remarks(input_dir: pathlib.Path, output_dir: pathlib.Path): ...
def process_document(
    metadata_path: pathlib.Path,
    relative_doc_path: pathlib.Path,
    output_dir: pathlib.Path,
): ...
