from cryptography.fernet import Fernet
import os
import logging

logger = logging.getLogger(__name__)

class CryptoService:
    """Service for encrypting and decrypting sensitive data like API keys."""

    def __init__(self):
        fernet_key = os.getenv("FERNET_KEY")
        if not fernet_key:
            raise ValueError("FERNET_KEY environment variable not set")

        try:
            self.cipher = Fernet(fernet_key.encode())
        except Exception as e:
            logger.error(f"Failed to initialize Fernet cipher: {e}")
            raise

    def encrypt(self, value: str) -> str:
        """Encrypt a string value.

        Args:
            value: Plain text string to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        try:
            encrypted_bytes = self.cipher.encrypt(value.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted: str) -> str:
        """Decrypt an encrypted string.

        Args:
            encrypted: Encrypted string (base64 encoded)

        Returns:
            Decrypted plain text string
        """
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
