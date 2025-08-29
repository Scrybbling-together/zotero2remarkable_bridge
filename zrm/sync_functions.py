# sync_functions.py
import logging
import os
import zipfile
import tempfile
import hashlib

from pyzotero.zotero import Zotero

import zrm.rmapi_shim as rmapi
import remarks
from pathlib import Path
from shutil import rmtree, copy
from time import sleep
from datetime import datetime

from zrm.adapters.ReMarkableAPI import ReMarkableAPI
from zrm.adapters.ZoteroAPI import ZoteroAPI

logger = logging.getLogger("zotero_rM_bridge.sync_functions")


def sync_to_rm(item, zot, folders):
    temp_path = Path(tempfile.gettempdir())
    item_id = item["key"]
    attachments = zot.children(item_id)
    logger.info(f"Syncing {len(attachments)} to reMarkable")
    for entry in attachments:
        if "contentType" in entry["data"] and entry["data"]["contentType"] == "application/pdf":
            attachment_id = attachments[attachments.index(entry)]["key"]
            item_data = zot.item(attachment_id)["data"]
            if item_data["linkMode"] == "linked_file":
                path = Path(item_data["path"])
                attachment_name = path.name
            else:
                path = None
                attachment_name = item_data["filename"]

            logger.info(f"Processing `{attachment_name}`")

            if path is None:
                # Get actual file and repack it in reMarkable's file format
                zot.dump(attachment_id, path=temp_path)
            else:
                logger.info(f"Copying linked file from {path}...")
                # Copy the linked file from its current location
                copy(path, temp_path)
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


def sync_to_rm_webdav(item, zot, webdav, folders):
    temp_path = Path(tempfile.gettempdir())
    item_id = item["key"]
    attachments = zot.children(item_id)
    for entry in attachments:
        if "contentType" in entry["data"] and entry["data"]["contentType"] == "application/pdf":
            attachment_id = attachments[attachments.index(entry)]["key"]
            attachment_name = zot.item(attachment_id)["data"]["filename"]
            logger.info(f"Processing `{attachment_name}`...")

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


def get_md5(pdf) -> None | str:
    if pdf.is_file():
        with open(pdf, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    return None


def get_mtime() -> str:
    return datetime.now().strftime('%s')


def fill_template(item_template, pdf_name):
    item_template["title"] = pdf_name.stem
    item_template["filename"] = pdf_name.name
    item_template["md5"] = get_md5(pdf_name)
    item_template["mtime"] = get_mtime()
    return item_template


def webdav_uploader(webdav, remote_path, local_path):
    for i in range(3):
        try:
            webdav.upload_sync(remote_path=remote_path, local_path=local_path)
        except:
            sleep(5)
        else:
            return True
    else:
        return False


def zotero_upload_webdav(pdf_name, zot, webdav):
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
                    logger.info("Failed to create attachment, aborting...")
                    continue

                attachment_zip = temp_path / f"{key}.zip"
                with zipfile.ZipFile(attachment_zip, "w") as zf:
                    zf.write(pdf_name, arcname=pdf_name.name)
                remote_attachment_zip = attachment_zip.name

                attachment_upload = webdav_uploader(webdav, remote_attachment_zip, attachment_zip)
                if attachment_upload:
                    logger.info("Attachment upload successful, proceeding...")
                else:
                    logger.error("Failed uploading attachment, skipping...")
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
                    logger.info("Propfile upload successful, proceeding...")
                else:
                    logger.error("Propfile upload failed, skipping...")
                    continue

                zot.add_tags(item, "read")
                logger.info(f"{pdf_name.name} uploaded to Zotero.")
                (temp_path / pdf_name).unlink()
                (temp_path / attachment_zip).unlink()
                (temp_path / propfile).unlink()
                return pdf_name
            return None
        return None
    return None


def sync_to_rm_filetree(handle: str, zotero_tree: ZoteroAPI, rm_tree: ReMarkableAPI, folders):
    """Sync an entry's PDF attachments from Zotero to reMarkable"""
    if not zotero_tree.item_exists(handle):
        logger.warning(f"No attachments found for item at {handle}")
        return

    attachments = zotero_tree.list_children(handle)
    attachments = [attachment for attachment in attachments if attachment.name.endswith(".pdf")]
    logger.info(f"Syncing {len(attachments)} attachments to reMarkable")

    all_attachments_synced = True

    for attachment in attachments:
        logger.info(f"Processing `{attachment}`")

        try:
            content = zotero_tree.get_file_content(attachment.handle)
            if rm_tree.upload_file(os.path.join("Zotero", folders['unread'], attachment.name), content):
                logger.info(f"Uploaded {attachment} to reMarkable.")
            else:
                all_attachments_synced = False
                logger.error(f"Failed to upload {attachment} to reMarkable.")
        except Exception as e:
            all_attachments_synced = False
            logger.error(f"Error processing {attachment}: {str(e)}")

    if all_attachments_synced:
        zotero_tree.add_tags(handle, ["synced"])
        zotero_tree.remove_tags(handle, ["to_sync"])


def attach_pdf_to_zotero_document(rendered_remarks_pdf: Path, zotero_tree: ZoteroAPI):
    """Attach annotated PDF back to Zotero using filetree interface."""
    document_name = rendered_remarks_pdf.stem.removesuffix(" _remarks")
    logger.info(f"Have an annotated PDF \"{document_name}\" to upload")

    for entry in zotero_tree.find_nodes_with_tag("synced"):
        attachments = zotero_tree.list_children(entry.handle)
        md_attachment = next(
            iter(att for att in attachments if (
                    Path(att.name).name.replace(document_name, "") == ".md" or
                    Path(att.path).name.replace(document_name, "") == ".md")), None)
        pdf_attachment = next(
            iter(att for att in attachments if (
                Path(att.name).name.replace(document_name, "") == ".pdf" or
                Path(att.path).name.replace(document_name, "") == ".pdf")), None)

        if pdf_attachment:
            with open(rendered_remarks_pdf, "rb") as f:
                pdf_content = f.read()

            new_attachment = zotero_tree.update_file_content(entry.handle, pdf_attachment.handle, pdf_content)
            if new_attachment:
                zotero_tree.add_tags(new_attachment, ["annotated"])
                logger.info(f"'{rendered_remarks_pdf}' PDF successfully attached to Zotero entry '{document_name}'.")
            else:
                logger.warning(f"Failed to create attachment for item at {entry}")

            md_path = rendered_remarks_pdf.with_name(f"{document_name} _obsidian.md")
            with open(md_path, "rb") as f:
                md_content = f.read()
            if md_attachment:
                new_attachment = zotero_tree.update_file_content(entry.handle, md_attachment.handle, md_content)
                if new_attachment:
                    zotero_tree.add_tags(new_attachment, ["annotated"])
                    logger.info(f"{md_attachment.name} MD successfully attached to Zotero entry '{document_name}'")
                else:
                    logger.warning(
                        f"Was unable to attach {md_attachment.name} MD to Zotero entry '{document_name}#{entry.handle}'")
            else:
                new_attachment = zotero_tree.create_file(entry.handle, document_name + ".md", md_content)
                if new_attachment:
                    zotero_tree.add_tags(new_attachment, ["annotated"])
                    logger.info(f"{document_name} MD successfully attached to Zotero entry '{document_name}'")
                else:
                    logger.warning(
                        f"Was unable to attach {md_attachment.name} MD to Zotero entry '{document_name}#{entry.handle}'")
            return

    logger.warning(
        f"There's an annotated PDF '{document_name}' to upload, but we're unable to find the appropriate item in Zotero")
