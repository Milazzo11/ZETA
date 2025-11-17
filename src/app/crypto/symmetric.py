"""
Symmetric cryptographic operations.

:author: Max Milazzo
"""



import base64
import secrets
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes



KEY_SIZE = 256
# symmetric key size (in bits)


BLOCK_SIZE = 128
# symmetric block size (in bits)


BYTE_SIZE = 8
# assumed byte size (in bits)



class AES:
    """
    AES (CBC) cryptography object.
    """

    key: bytes
    iv: bytes


    @staticmethod
    def key(key_size: int = KEY_SIZE) -> bytes:
        """
        Random AES static key generation function.

        :param key_size: key size (in bits)
        :return: generated key
        """

        return secrets.token_bytes(key_size // BYTE_SIZE)
    
    
    @staticmethod
    def iv() -> bytes:
        """
        Random AES IV generation function.
        """

        return secrets.token_bytes(BLOCK_SIZE // BYTE_SIZE)


    def __init__(
        self, key_size: int = KEY_SIZE,
        key: bytes | None = None,
        iv: bytes | None = None
    ) -> None:
        """
        AES encryption object initialization.

        :param key_size: key size (in bits)
        :param key: encryption key to use (generated if not present)
        :param iv: IV bytes to use (generated if not present)
        """

        if key_size != 128 and key_size != 192 and key_size != 256:
            raise Exception("AES: invalid key length")
            # raise exception if invalid key size is passed

        if key is None:
            self.key = AES.key(key_size)
            # generate key if none passed

        else:
            self.key = key
            # set passed key

        if iv is None:
            self.iv = AES.iv()
            # generate IV if none passed

        else:
            self.iv = iv
            # set passed IV

        self.cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv))
        # initialize cipher


    def encrypt(self, plaintext: str) -> str:
        """
        Perform AES encryption.

        :param plaintext: plaintext string to be encrypted
        :return: encrypted base64 string
        """

        plaintext = plaintext.encode("utf-8")

        padder = padding.PKCS7(BLOCK_SIZE).padder()
        padded_plaintext = padder.update(plaintext) + padder.finalize()
        # add padding to plaintext

        encryptor = self.cipher.encryptor()
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        # encrypt data

        return base64.b64encode(ciphertext).decode("utf-8")


    def decrypt(self, ciphertext: str) -> str:
        """
        Perform AES decryption.

        :param ciphertext: base64 ciphertext string to decrypt
        :return: decrypted data string
        """

        ciphertext = base64.b64decode(ciphertext)

        unpadder = padding.PKCS7(BLOCK_SIZE).unpadder()
        # initialize "unnpadder" to remove padding from decrypted plaintext

        decryptor = self.cipher.decryptor()
        plaintext = (
            unpadder.update(decryptor.update(ciphertext)) +
            unpadder.finalize()
        )
        # decrypt data

        return plaintext.decode("utf-8")



SKC = AES
# standard symmetric key encryption object