from _typeshed import Incomplete

class WebDavException(Exception): ...
class NotValid(WebDavException): ...

class OptionNotValid(NotValid):
    name: Incomplete
    value: Incomplete
    ns: Incomplete
    def __init__(self, name, value, ns: str = "") -> None: ...

class CertificateNotValid(NotValid): ...
class NotFound(WebDavException): ...

class LocalResourceNotFound(NotFound):
    path: Incomplete
    def __init__(self, path) -> None: ...

class RemoteResourceNotFound(NotFound):
    path: Incomplete
    def __init__(self, path) -> None: ...

class RemoteParentNotFound(NotFound):
    path: Incomplete
    def __init__(self, path) -> None: ...

class MethodNotSupported(WebDavException):
    name: Incomplete
    server: Incomplete
    def __init__(self, name, server) -> None: ...

class ConnectionException(WebDavException):
    exception: Incomplete
    def __init__(self, exception) -> None: ...

class NoConnection(WebDavException):
    hostname: Incomplete
    def __init__(self, hostname) -> None: ...

class NotConnection(WebDavException):
    hostname: Incomplete
    def __init__(self, hostname) -> None: ...

class ResponseErrorCode(WebDavException):
    url: Incomplete
    code: Incomplete
    message: Incomplete
    def __init__(self, url, code, message) -> None: ...

class NotEnoughSpace(WebDavException):
    message: str
    def __init__(self) -> None: ...

class ResourceLocked(WebDavException):
    path: Incomplete
    def __init__(self, path) -> None: ...
