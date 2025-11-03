"""
Asymmetric key encryption object definition.

:author: Max Milazzo
"""

import base64
from jwcrypto import jws, jwk
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from typing import Union
import json


KEY_SIZE = 4096
# asymmetric key size (in bits)


PUBLIC_EXPONENT = 65537
# standard public exponent


class RSA:
    """
    RSA encryption object.
    """

    @staticmethod
    def _json_canon(data: dict) -> bytes:
        return json.dumps(
            data,
            separators=(",", ":"), # remove whitespace
            sort_keys=True        # stable key order
        ).encode()


    def __init__(
        self,
        key_size: int = KEY_SIZE,
        private_key: Union[bytes, str, None] = None,
        public_key: Union[bytes, str, None] = None
    ) -> None:
        """
        RSA encryption object initialization.

        :param key_size: key size (in bits)
        :param public_key: public encryption key to use (if present)
        :param private_key: private decryption key to use (if present)
        """

        if key_size != 1024 and key_size != 2048 and key_size != 4096:
            raise Exception("RSA: invalid key length")
            # raise exception if invalid key size is passed

        self.key_size = key_size
        # store key size

        if private_key is None and public_key is None:
            self.private_key, self.public_key = self._generate_key_pair(self.key_size)
            # generate new key pair

        else:
            self.private_key = private_key
            self.public_key = public_key
            # set passed keys

            if type(self.private_key) == str:
                self.private_key = self.private_key.encode("utf-8")
                # convert public key string to bytes

            if type(self.public_key) == str:
                self.public_key = self.public_key.encode("utf-8")
                # convert public key string to bytes

        if self.private_key is not None:
            self._private_key = serialization.load_pem_private_key(
                self.private_key, password=None, backend=default_backend()
            )
            # initialize private key object for decryption

        if self.public_key is not None:
            self._public_key = serialization.load_pem_public_key(
                self.public_key, backend=default_backend()
            )
            # initialize public key object for encryption


    def _generate_key_pair(self, key_size: int) -> tuple:
        """
        Generate RSA key pair.

        :param key_size: key size (in bits)
        :return: private and public key pair
        """

        private_key = rsa.generate_private_key(
            public_exponent=PUBLIC_EXPONENT,
            key_size=key_size,
            backend=default_backend()
        )
        # generate new private key

        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        # encode and format private key bytes

        public_key_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        # generate associated public key bytes

        return private_key_bytes, public_key_bytes


    def encrypt(
        self, plaintext: Union[bytes, str], byte_output: bool = False
    ) -> Union[bytes, str]:
        """
        Perform RSA encryption.

        :param plaintext: plaintext to be encrypted
        :param byte_output: specifies whether to return encrypted data as bytes
            or base64-encoded string

        :return: encrypted data
        """

        if type(plaintext) == str:
            plaintext = plaintext.encode("utf-8")
            # encode plaintext string to bytes

        ciphertext = self._public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        # encrypt data

        if not byte_output:
            ciphertext = base64.b64encode(ciphertext).decode("utf-8")
            # encode ciphertext as a base64 string

        return ciphertext


    def decrypt(
        self, ciphertext: Union[bytes, str], byte_output: bool = True
    ) -> Union[bytes, str]:
        """
        Perform RSA decryption.

        :param ciphertext: ciphertext to decrypt
        :param byte_output: specifies whether to return decrypted data as bytes
            or decoded UTF-8 string

        :return: decrypted data
        """

        if type(ciphertext) == str:
            ciphertext = base64.b64decode(ciphertext)
            # decode ciphertext base64 string to bytes

        plaintext = self._private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        # decrypt data

        if not byte_output:
            plaintext = base64.b64encode(plaintext).decode("utf-8")
            # decode plaintext as a UTF-8 string

        return plaintext

    def sign(
        self, message: Union[dict, bytes, str], byte_output: bool = False
    ) -> Union[bytes, str]:
        """
        Generate a digital signature.

        :param message: message text to digitally sign
        :param byte_output: specifies whether to return encrypted data as bytes
            or base64-encoded string

        :return: digital signature
        """

        if type(message) == dict:
            # JWS (compact, embedded payload). Same RSA key, alg stays RS256.
            key = jwk.JWK.from_pem(self.private_key)
            t = jws.JWS(self._json_canon(message))
            t.add_signature(key, protected={"alg": "RS256"})
            return t.serialize(compact=True)  # looks like "<hdr>.<payload>.<sig>"

        if type(message) == str:
            message = message.encode("utf-8")
            # encode message string to bytes

        signature = self._private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        # sign the message using RSA and SHA-256

        if not byte_output:
            signature = base64.b64encode(signature).decode("utf-8")
            # decode plaintext as a UTF-8 string

        return signature


    def verify(
        self, signature: Union[bytes, str], message: Union[dict, bytes, str]
    ) -> bool:
        """
        Verify a digital signature.

        :param signature: the digital signature to verify
        :param message: message text that was digitally signed

        :return: True if valid and False otherwise
        """

        if type(message) == dict:
            try:
                key = jwk.JWK.from_pem(self.public_key)
                t = jws.JWS()
                t.deserialize(signature)  # accepts compact JWS string
                t.verify(key)             # raises on failure

                return True
            except:
                return False

        if type(message) == str:
            message = message.encode("utf-8")
            # encode message string to bytes

        if type(signature) == str:
            signature = base64.b64decode(signature)
            # decode signature base64 string to bytes

        try:
            self._public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            # verify the signature

            return True
            # return true if valid

        except:
            return False
            # return true if invalid


AKE = RSA
# standard asymmetric key encryption object