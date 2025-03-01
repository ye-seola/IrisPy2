from dataclasses import dataclass


@dataclass
class Message:
    id: int
    type: int
    msg: str
    attachment: str
    v: str


@dataclass
class Room:
    id: int
    name: str


@dataclass
class User:
    id: int
    name: str
