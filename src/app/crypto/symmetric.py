"""
Symmetric cryptographic operations.

:author: Max Milazzo
"""



import base64
import secrets
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from typing import Union



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
        key: Union[bytes, None] = None,
        iv: Union[bytes, None] = None
    ) -> None:
        """
        AES encryption object initialization.

        :param key_size: key size (in bits)
        :param key: encryption key to use (if present)
        :param iv: IV bytes to use (if present)
        """

        if key_size != 128 and key_size != 192 and key_size != 256:
            raise Exception("AES: invalid key length")
            # raise exception if invalid key size is passed

        self.key_size = key_size
        # store key size
        
        self.block_size = BLOCK_SIZE // BYTE_SIZE
        # calculate block size in bytes
        
        if key is None:
            self.key = AES.key(self.key_size)
            # generate key if none passed

        else:
            self.key = key
            # set passed key

        if iv is None:
            self.iv = SKC.iv()
            # generate IV if none passed

        else:
            self.iv = iv
            # set passed IV

        self.cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv))
        # initialize cipher


    def encrypt(
        self,
        plaintext: Union[bytes, str],
        byte_output: bool = False
    ) -> Union[bytes, str]:
        """
        Perform AES encryption.

        :param plaintext: plaintext to be encrypted
        :param byte_output: specifies whether to return encrypted data as bytes
            or base64-encoded string
        :return: encrypted data
        """

        encryptor = self.cipher.encryptor()
        # initialize encryptor

        if type(plaintext) == str:
            plaintext = plaintext.encode("utf-8")
            # encode plaintext string to bytes

        padder = padding.PKCS7(self.block_size * BYTE_SIZE).padder()
        padded_plaintext = padder.update(plaintext) + padder.finalize()
        # add padding to plaintext

        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        # encrypt data

        if not byte_output:
            ciphertext = base64.b64encode(ciphertext).decode("utf-8")
            # encode ciphertext as a base64 string

        return ciphertext


    def decrypt(
        self,
        ciphertext: Union[bytes, str],
        byte_output: bool = False
    ) -> Union[bytes, str]:
        """
        Perform AES decryption.

        :param ciphertext: ciphertext to decrypt
        :param byte_output: specifies whether to return decrypted data as bytes
            or decoded UTF-8 string
        :return: decrypted data
        """

        decryptor = self.cipher.decryptor()
        # initialize decryptor

        if type(ciphertext) == str:
            ciphertext = base64.b64decode(ciphertext)
            # decode ciphertext base64 string to bytes

        unpadder = padding.PKCS7(self.block_size * BYTE_SIZE).unpadder()
        # initialize "unnpadder" to remove padding from decrypted plaintext

        plaintext = (
            unpadder.update(decryptor.update(ciphertext)) +
            unpadder.finalize()
        )
        # decrypt data

        if not byte_output:
            plaintext = plaintext.decode("utf-8")
            # decode plaintext as a UTF-8 string

        return plaintext
    

    def iv_b64(self) -> str:
        """
        Return the base64 encoded cipher IV.

        :return: base64 encoded cipher IV
        """

        return base64.b64encode(self.iv).decode("utf-8")


   
SKC = AES
# standard symmetric key encryption object