"""
Symmetric encryption utilities for protecting user connection secrets.
Uses AES-256-GCM with a master key from settings.
"""

from typing import Tuple
import os
import hashlib

from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore


def _derive_key(master_key: str) -> bytes:
    """Derive a 32-byte key from the given master key using SHA-256."""
    return hashlib.sha256(master_key.encode("utf-8")).digest()


def encrypt_secret(plaintext: str, master_key: str) -> Tuple[bytes, bytes]:
    """Encrypt plaintext using AES-256-GCM.

    Returns (iv, ciphertext).
    """
    key = _derive_key(master_key)
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    return iv, ciphertext


def decrypt_secret(ciphertext: bytes, iv: bytes, master_key: str) -> str:
    """Decrypt AES-256-GCM ciphertext with the provided iv."""
    key = _derive_key(master_key)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, ciphertext, None)
    return plaintext.decode("utf-8")
