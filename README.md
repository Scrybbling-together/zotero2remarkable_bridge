# Zotero2reMarkable Bridge

This program can be used to sync attachments from Zotero to your ReMarkable
*and* sync them back to Zotero again.

It relies on both Zotero's and reMarkable's cloud APIs for Python. This means
sync must be enabled in Zotero to use this program. Both Zotero's storage and external WebDAV storage is supported, 
although Zotero's own cloud support is largely untested. Testing and bug reports/pull requests are highly appreciated.

## Usage

The workflow starts at Zotero. To pick which attachment to sync, add the `to_sync` tag to the entry.

When you run the script, these files will be synced to your "unread" folder on the reMarkable.

Once you're done reading and/or annotating, move the notebook from "unread" to "read" on your tablet.

Now, when you run the script again, your annotations will be synced back to zotero.

### How it works

To designate attachments that should be synced, add the tag "to_sync" to the entry.

After the files are synced, this tag is automatically removed and set to "synced".
Do not remove these tags as they are used to determine which files should be synced back.

The program uses [remarks](https://github.com/Scrybbling-together/remarks.git) to render files from ReMarkable and therefore has support both for annotations and smart highlights. Colors are supported.

The program will preserve the original file and add the marked file as a new attachment with `(Annot) ` added in front of the file name.
Entries that have been synced back will have the tag "read" added to them, so you can search for them.

- Supports sync via the ReMarkable API

### Setup

#### On reMarkable

- Create a folder named `Zotero` through the UI on your reMarkable. This folder must be on the top level of the file system and cannot be nested under other folders.
- Create two folders inside the `Zotero` folder, one for your unread documents (this is where new files from Zotero will land) and your read documents (this is where the program looks for files to be synced back to Zotero). 

#### On your PC

1. First, you need to download this project: `git clone https://github.com/Scrybbling-together/zotero2remarkable_bridge.git`

##### Dependencies

1. Next, make sure you have [poetry](https://python-poetry.org/) installed, if you're using nix, this is done automatically for you. If not, you can [install it here](https://python-poetry.org/)
2. You also need to have [rmapi](https://github.com/ddvk/rmapi/blob/master/README.md) set-up. Download the latest release, and run it once to set it up. Make sure to place it in the zotero2remarkable_bridge folder.
3. Third, [inkscape](https://inkscape.org/) needs to be available on your PATH, which is used to render the reMarkable annotations to PDF by remarks.
4. Last, you need to install the python dependencies for zotero2remarkable_bridge as follows: `poetry install`

##### Running

Whenever you want to run, you need to activate the virtual environment and run the program:

```bash
source $(poetry env info --path)/bin/activate
python ./zotero2remarkable_bridge.py
# At first run, it will guide you through creating a working
# config. It will help you setup authentication with Zotero, WebDAV (optional), and
# reMarkable.
```

##### Arguments

The program accepts the following arguments:

```
./zotero2remarkable_bridge.py [-m push|pull|both]

-m: Mode
push: Only push to ReMarkable

pull: Only pull from ReMarkable and sync to Zotero

both: Go both ways, adding new files to ReMarkable and syncing back
        to ReMarkable.
        
Defaults to "both".
```

## Development

### Testing

We have both end-to-end tests which require a real reMarkable as well as a real Zotero account.

To speed up development, we also have in-memory mocks of both the reMarkable as the Zotero API.
Run these with `pytest -k "not e2e"`