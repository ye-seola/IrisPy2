# https://github.com/jiru/kakaodecrypt

import base64
import hashlib
from Crypto.Cipher import AES


def gen_salt(user_id: int, enc_type: int):
    if user_id <= 0:
        return b"\0" * 16

    # fmt: off
    prefixes = ["","","12","24","18","30","36","12","48","7","35","40","17","23","29",
                "isabel","kale","sulli","van","merry","kyle","james", "maddux",
                "tony", "hayden", "paul", "elijah", "dorothy", "sally", "bran",
                "extr.ursra", "veil"]
    # fmt: on

    try:
        salt = prefixes[enc_type] + str(user_id)
    except IndexError:
        raise ValueError("Unsupported encoding type %i" % enc_type)

    salt = salt.ljust(16, "\x00")[0:16]
    return salt.encode("UTF-8")


def pkcs16adjust(a, a_off, b):
    x = (b[len(b) - 1] & 0xFF) + (a[a_off + len(b) - 1] & 0xFF) + 1
    a[a_off + len(b) - 1] = x % 256
    x = x >> 8
    for i in range(len(b) - 2, -1, -1):
        x = x + (b[i] & 0xFF) + (a[a_off + i] & 0xFF)
        a[a_off + i] = x % 256
        x = x >> 8


def derive_key(password: bytes, salt: bytes, iterations: int, d_key_size: int):
    password = (password + b"\0").decode("ascii").encode("utf-16-be")

    hasher = hashlib.sha1()
    v = hasher.block_size
    u = hasher.digest_size

    D = [1] * v
    S = [0] * v * int((len(salt) + v - 1) / v)
    for i in range(0, len(S)):
        S[i] = salt[i % len(salt)]
    P = [0] * v * int((len(password) + v - 1) / v)
    for i in range(0, len(P)):
        P[i] = password[i % len(password)]

    I = S + P

    B = [0] * v
    c = int((d_key_size + u - 1) / u)

    d_key = [0] * d_key_size
    for i in range(1, c + 1):
        hasher = hashlib.sha1()
        hasher.update(bytes(D))
        hasher.update(bytes(I))
        A = hasher.digest()

        for j in range(1, iterations):
            hasher = hashlib.sha1()
            hasher.update(A)
            A = hasher.digest()

        A = list(A)
        for j in range(0, len(B)):
            B[j] = A[j % len(A)]

        for j in range(0, int(len(I) / v)):
            pkcs16adjust(I, j * v, B)

        start = (i - 1) * u
        if i == c:
            d_key[start:d_key_size] = A[0 : d_key_size - start]
        else:
            d_key[start : start + len(A)] = A[0 : len(A)]

    return bytes(d_key)


key_cache = {}


def decrypt(user_id: int, enc_type: int, b64_ciphertext: str):
    key = b"\x16\x08\x09\x6f\x02\x17\x2b\x08\x21\x21\x0a\x10\x03\x03\x07\x06"
    iv = b"\x0f\x08\x01\x00\x19\x47\x25\xdc\x15\xf5\x17\xe0\xe1\x15\x0c\x35"

    salt = gen_salt(user_id, enc_type)
    if salt in key_cache:
        key = key_cache[salt]
    else:
        key = derive_key(key, salt, 2, 32)
        key_cache[salt] = key

    encoder = AES.new(key, AES.MODE_CBC, iv)
    return encoder.decrypt(base64.b64decode(b64_ciphertext)).decode()
