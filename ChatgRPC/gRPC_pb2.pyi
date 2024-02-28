from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AuthenticationToken(_message.Message):
    __slots__ = ["password", "username"]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    password: str
    username: str
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class ChatMessage(_message.Message):
    __slots__ = ["message", "receiver_username", "sender_username"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_USERNAME_FIELD_NUMBER: _ClassVar[int]
    SENDER_USERNAME_FIELD_NUMBER: _ClassVar[int]
    message: str
    receiver_username: str
    sender_username: str
    def __init__(self, receiver_username: _Optional[str] = ..., sender_username: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ListUsernamesParams(_message.Message):
    __slots__ = ["wildcard"]
    WILDCARD_FIELD_NUMBER: _ClassVar[int]
    wildcard: str
    def __init__(self, wildcard: _Optional[str] = ...) -> None: ...

class Note(_message.Message):
    __slots__ = ["message", "name"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    message: str
    name: str
    def __init__(self, name: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class PendingMessagesPayload(_message.Message):
    __slots__ = ["msg"]
    MSG_FIELD_NUMBER: _ClassVar[int]
    msg: _containers.RepeatedCompositeFieldContainer[ChatMessage]
    def __init__(self, msg: _Optional[_Iterable[_Union[ChatMessage, _Mapping]]] = ...) -> None: ...

class ReturnStatusPayload(_message.Message):
    __slots__ = ["serverMsg", "success", "successPayload"]
    SERVERMSG_FIELD_NUMBER: _ClassVar[int]
    SUCCESSPAYLOAD_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    serverMsg: str
    success: bool
    successPayload: PendingMessagesPayload
    def __init__(self, success: bool = ..., serverMsg: _Optional[str] = ..., successPayload: _Optional[_Union[PendingMessagesPayload, _Mapping]] = ...) -> None: ...

class SendParams(_message.Message):
    __slots__ = ["msg", "receiver_username", "sender_username"]
    MSG_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_USERNAME_FIELD_NUMBER: _ClassVar[int]
    SENDER_USERNAME_FIELD_NUMBER: _ClassVar[int]
    msg: str
    receiver_username: str
    sender_username: str
    def __init__(self, receiver_username: _Optional[str] = ..., sender_username: _Optional[str] = ..., msg: _Optional[str] = ...) -> None: ...

class SuccessStatus(_message.Message):
    __slots__ = ["success"]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class Username(_message.Message):
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class Usernames(_message.Message):
    __slots__ = ["usernames"]
    USERNAMES_FIELD_NUMBER: _ClassVar[int]
    usernames: _containers.RepeatedCompositeFieldContainer[Username]
    def __init__(self, usernames: _Optional[_Iterable[_Union[Username, _Mapping]]] = ...) -> None: ...
