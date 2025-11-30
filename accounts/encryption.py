"""
Encryption utility for sensitive data like LDAP passwords
Uses Fernet symmetric encryption from the cryptography library
"""
import base64
import hashlib
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_encryption_key():
    """
    Derive a Fernet encryption key from Django's SECRET_KEY
    Fernet requires a 32-byte key, so we use PBKDF2 to derive it
    """
    # Use SECRET_KEY as the password and a fixed salt (derived from SECRET_KEY)
    secret_key = settings.SECRET_KEY.encode('utf-8')
    salt = hashlib.sha256(secret_key).digest()[:16]  # 16-byte salt
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key))
    return key


def encrypt_password(plaintext_password):
    """
    Encrypt a plaintext password using Fernet encryption
    
    Args:
        plaintext_password: The password to encrypt (string)
    
    Returns:
        Encrypted password as a string, or empty string if input is empty
    """
    if not plaintext_password:
        return ''
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(plaintext_password.encode('utf-8'))
        return encrypted.decode('utf-8')
    except Exception as e:
        # Log error but don't expose it
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error encrypting password: {str(e)}")
        raise


def decrypt_password(encrypted_password):
    """
    Decrypt an encrypted password using Fernet decryption
    
    Args:
        encrypted_password: The encrypted password (string)
    
    Returns:
        Decrypted password as a string, or empty string if input is empty
    """
    if not encrypted_password:
        return ''
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        # If decryption fails, it might be plaintext (for existing records)
        # Try to detect if it's already plaintext by checking if it's valid base64
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error decrypting password (might be plaintext): {str(e)}")
        # Return as-is if it looks like it might be plaintext
        # This handles migration of existing plaintext passwords
        return encrypted_password


def is_encrypted(value):
    """
    Check if a value appears to be encrypted (Fernet format)
    
    Args:
        value: The value to check
    
    Returns:
        True if the value appears to be encrypted, False otherwise
    """
    if not value:
        return False
    
    try:
        # Fernet tokens are base64-encoded and have a specific format
        # They should be valid base64 and have a certain length
        # Fernet tokens start with a specific byte pattern and are URL-safe base64
        decoded = base64.urlsafe_b64decode(value.encode('utf-8'))
        # Fernet tokens have a minimum structure:
        # - Version byte (1 byte)
        # - Timestamp (8 bytes)
        # - IV (16 bytes)
        # - HMAC (32 bytes)
        # - Ciphertext (variable, but at least some bytes)
        # Minimum would be around 57+ bytes, but we'll be more lenient
        # Also check if it's valid base64 and has reasonable length
        if len(decoded) < 50:
            return False
        # Try to decrypt to verify it's actually encrypted
        # If decryption works, it's encrypted
        key = get_encryption_key()
        fernet = Fernet(key)
        fernet.decrypt(value.encode('utf-8'))
        return True
    except Exception:
        # If decryption fails, it's likely not encrypted (or wrong key, but that's unlikely)
        return False

