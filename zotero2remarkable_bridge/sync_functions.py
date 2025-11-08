# sync_functions.py
import logging
import os
import zipfile
import tempfile
import hashlib
from pprint import pprint

from pyzotero.zotero import Zotero

from webdav3.client import Client as wdClient

import zotero2remarkable_bridge.rmapi_shim as rmapi
import remarks
from pathlib import Path
from shutil import rmtree
from time import sleep
from datetime import datetime

from typing import Any, List

logger = logging.getLogger("zotero_rM_bridge.sync_functions")


def sync_to_rm(item: Any, zot: Zotero, folders: Any):
    """Sync items from Zotero to Remarkable"""
    temp_path = Path(tempfile.gettempdir())
    item_id = item["key"]
    attachments = zot.children(item_id)
    logger.info(f"Syncing {len(attachments)} to reMarkable")
    for entry in attachments:
        if "contentType" in entry["data"] and entry["data"]["contentType"] == "application/pdf":
            attachment_id = attachments[attachments.index(entry)]["key"]
            attachment_name = zot.item(attachment_id)["data"]["filename"]
            logger.info(f"Processing {attachment_name}...")

            # Get actual file and repack it in reMarkable's file format
            zot.dump(attachment_id, path=temp_path)
            file_name = temp_path / attachment_name
            if file_name:
                if rmapi.upload_file(file_name, f"/Zotero/{folders['unread']}"):
                    zot.add_tags(item, "synced")
                    os.remove(file_name)
                    logger.info(f"Uploaded {attachment_name} to reMarkable.")
                else:
                    logger.error(f"Failed to upload {attachment_name} to reMarkable.")
        else:
            logger.warning("Found attachment, but it's not a PDF, skipping...")


def sync_to_rm_webdav(item: Any, zot: Zotero, webdav: wdClient, folders: Any):
    """Sync items from Zotero to Remarkable using WebDAV"""
    temp_path = Path(tempfile.gettempdir())
    item_id = item["key"]
    attachments = zot.children(item_id)
    for entry in attachments:
        if "contentType" in entry["data"] and entry["data"]["contentType"] == "application/pdf":
            attachment_id = attachments[attachments.index(entry)]["key"]
            attachment_name = zot.item(attachment_id)["data"]["filename"]
            logger.info(f"Processing {attachment_name}...")

            # Get actual file from webdav, extract it and repack it in reMarkable's file format
            file_name = f"{attachment_id}.zip"
            file_path = Path(temp_path / file_name)
            unzip_path = Path(temp_path / f"{file_name}-unzipped")
            webdav.download_sync(remote_path=file_name, local_path=file_path)
            with zipfile.ZipFile(file_path) as zf:
                zf.extractall(unzip_path)
                zf.extractall(".")
            if (unzip_path / attachment_name).is_file():
                uploader = rmapi.upload_file(str(unzip_path / attachment_name), f"/Zotero/{folders['unread']}")
            else:
                """ #TODO: Sometimes Zotero does not seem to rename attachments properly,
                    leading to reported file names diverging from the actual one.
                    To prevent this from stopping the whole program due to missing
                    file errors, skip that file. Probably it could be worked around better though."""
                logger.warning(
                    "PDF not found in downloaded file. Filename might be different. Try renaming file in Zotero, sync and try again.")
                break
            if uploader:
                zot.add_tags(item, "synced")
                file_path.unlink()
                rmtree(unzip_path)
                logger.info(f"Uploaded {attachment_name} to reMarkable.")
            else:
                logger.error(f"Failed to upload {attachment_name} to reMarkable.")
        else:
            logger.info("Found attachment, but it's not a PDF, skipping...")


def download_from_rm(entity: str, folder: str) -> Path:
    """Download item from Remarkable"""
    temp_path = Path(tempfile.gettempdir())
    logger.info(f"Processing {entity}...")
    zip_name = f"{entity}.rmdoc"
    file_path = temp_path / zip_name
    unzip_path = temp_path / f"{entity}-unzipped"
    download = rmapi.download_file(f"{folder}{entity}", str(temp_path))
    if download:
        logger.info("File downloaded")
    else:
        logger.warning("Failed to download file")

    with zipfile.ZipFile(file_path, "r") as zf:
        zf.extractall(unzip_path)

    remarks.run_remarks(str(unzip_path), temp_path)
    logging.info("PDF rendered")
    pdf = (temp_path / f"{entity} _remarks.pdf")
    pdf = pdf.rename(pdf.with_stem(f"{entity}"))
    pdf_name = pdf.name

    logging.info("PDF written")
    file_path.unlink()
    rmtree(unzip_path)

    return Path(temp_path / pdf_name)


def zotero_upload(pdf_path: Path, zot: Zotero):
    """Upload PDF to Zotero"""
    md_name = f"{pdf_path.stem} _obsidian.md"
    md_path = pdf_path.with_name(md_name)

    annotated_name = f"(Annotated) {pdf_path.stem}{pdf_path.suffix}"
    annotated_path = pdf_path.with_name(annotated_name)
    logging.info(f"Have an annotated PDF {str(pdf_path)} to upload")

    pdf_path.rename(str(annotated_path) + ".pdf")

    for item in zot.items(tag="synced"):
        already_uploaded_annotation = len([1 for tag in item["data"].get('tags') if tag["tag"] == "annotated"]) > 0
        item_id = item["key"]
        item_name = item.get("data", {}).get("title") or item_id
        for attachment in zot.children(item_id):
            if attachment["data"].get("filename", "") == pdf_path.name and not already_uploaded_annotation:
                files_to_upload = [str(annotated_path)]
                if md_path.exists():
                    files_to_upload.append(str(md_path))

                upload = zot.attachment_simple(files_to_upload, item_id)
                if upload.get("success") or upload.get('unchanged'):
                    logging.info(f"{pdf_path} attached to Zotero item '{item_name}'.")
                    zot.add_tags(item, "annotated")
                elif already_uploaded_annotation:
                    logging.warning(f"Uploading {pdf_path} to Zotero item '{item_name}' failed")
                    logging.warning(f"Reason for upload failure: {upload.get('failure')}")
                return
            elif already_uploaded_annotation:
                return

    logging.warning(
        f"Have an annotated PDF '{annotated_name}' to upload, but cannot find the appropriate item in Zotero")


def get_md5(pdf) -> None | str:
    """Get MD5 for pdf file"""
    if pdf.is_file():
        with open(pdf, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    return None


def get_mtime() -> str:
    """Generate mtime corresponding to current time"""
    return datetime.now().strftime('%s')


def fill_template(item_template: Any, pdf_name: Any) -> Any:
    """Fill an item template for upload to Zotero"""
    item_template["title"] = pdf_name.stem
    item_template["filename"] = pdf_name.name
    item_template["md5"] = get_md5(pdf_name)
    item_template["mtime"] = get_mtime()
    return item_template


def webdav_uploader(webdav: wdClient, remote_path: str, local_path: Path) -> bool:
    """Upload a file using WebDAV"""
    for i in range(3):
        try:
            webdav.upload_sync(remote_path=remote_path, local_path=local_path)
        except:
            sleep(5)
        else:
            return True
    else:
        return False


def zotero_upload_webdav(pdf_name: Path, zot: Zotero, webdav: wdClient) -> Path | None:
    """Upload a pdf file to Zotero using WebDAV, creating the attachment if needed"""
    temp_path = Path(tempfile.gettempdir())
    item_template = zot.item_template("attachment", "imported_file")
    for item in zot.items(tag=["synced", "-read"]):
        item_id = item["key"]
        for attachment in zot.children(item_id):
            if "filename" in attachment["data"] and attachment["data"]["filename"] == pdf_name:
                pdf_name = temp_path / pdf_name
                new_pdf_name = pdf_name.with_stem(f"(Annot) {pdf_name.stem}")
                pdf_name.rename(new_pdf_name)
                pdf_name = new_pdf_name
                filled_item_template = fill_template(item_template, pdf_name)
                create_attachment = zot.create_items([filled_item_template], item_id)

                if create_attachment["success"]:
                    key = create_attachment["success"]["0"]
                else:
                    logging.info("Failed to create attachment, aborting...")
                    continue

                attachment_zip = temp_path / f"{key}.zip"
                with zipfile.ZipFile(attachment_zip, "w") as zf:
                    zf.write(pdf_name, arcname=pdf_name.name)
                remote_attachment_zip = attachment_zip.name

                attachment_upload = webdav_uploader(webdav, remote_attachment_zip, attachment_zip)
                if attachment_upload:
                    logging.info("Attachment upload successful, proceeding...")
                else:
                    logging.error("Failed uploading attachment, skipping...")
                    continue

                """For the file to be properly recognized in Zotero, a propfile needs to be
                uploaded to the same folder with the same ID. The content needs
                to match exactly Zotero's format."""
                propfile_content = f'<properties version="1"><mtime>{item_template["mtime"]}</mtime><hash>{item_template["md5"]}</hash></properties>'
                propfile = temp_path / f"{key}.prop"
                with open(propfile, "w") as pf:
                    pf.write(propfile_content)
                remote_propfile = f"{key}.prop"

                propfile_upload = webdav_uploader(webdav, remote_propfile, propfile)
                if propfile_upload:
                    logging.info("Propfile upload successful, proceeding...")
                else:
                    logging.error("Propfile upload failed, skipping...")
                    continue

                zot.add_tags(item, "read")
                logging.info(f"{pdf_name.name} uploaded to Zotero.")
                (temp_path / pdf_name).unlink()
                (temp_path / attachment_zip).unlink()
                (temp_path / propfile).unlink()
                return pdf_name
            return None
        return None
    return None


def get_sync_status(zot: Zotero) -> List[Any]:
    """Get the list of synced items"""
    read_list = []
    for item in zot.items(tag="read"):
        for attachment in zot.children(item["key"]):
            if "contentType" in attachment["data"] and attachment["data"]["contentType"] == "application/pdf":
                read_list.append(attachment["data"]["filename"])

    return read_list
