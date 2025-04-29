import hashlib


def calculate_userhash(chat_id: str, user_id: str):
    hashlib.sha256(f"person_{chat_id}:{user_id}".encode()).hexdigest()
