from webdav3.exceptions import *
from _typeshed import Incomplete
from webdav3.urn import Urn as Urn

class ConnectionSettings:
    def is_valid(self) -> None: ...
    def valid(self): ...

class WebDAVSettings(ConnectionSettings):
    ns: str
    prefix: str
    keys: Incomplete
    hostname: Incomplete
    login: Incomplete
    password: Incomplete
    token: Incomplete
    root: Incomplete
    cert_path: Incomplete
    key_path: Incomplete
    recv_speed: Incomplete
    send_speed: Incomplete
    verbose: Incomplete
    disable_check: bool
    override_methods: Incomplete
    timeout: int
    chunk_size: int
    options: Incomplete
    def __init__(self, options) -> None: ...
    def is_valid(self): ...
