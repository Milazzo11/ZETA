"""
Asymmetric cryptographic signature operations.

:author: Max Milazzo
"""



import base64
import json
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding



KEY_SIZE = 4096
# asymmetric key size (in bits)


PUBLIC_EXPONENT = 2 ** 16 + 1
# standard public exponent



class RSA:
    """
    RSA cryptography signing object.
    """

    private_key: str | None
    public_key: str


    @staticmethod
    def _json_canon(data: dict) -> bytes:
        """
        Generate canonicalized JSON bytes from dictionary.

        :param data: data to convert
        :return: canonicalized JSON bytes
        """

        return json.dumps(data, separators=(",", ":"), sort_keys=True).encode()


    def __init__(
        self,
        key_size: int = KEY_SIZE,
        private_key: str | None = None,
        public_key: str | None = None
    ) -> None:
        """
        RSA signing / verification object.

        :param key_size: key size (in bits)
        :param private_key: private key PEM string (signer mode)
        :param public_key: public key PEM string (verifier mode or ignored if
            private_key provided)
        """

        if key_size not in (1024, 2048, 4096):
            raise Exception("RSA: invalid key length")

        if private_key is None and public_key is None:
            self._init_from_new_key(key_size)
            # signer mode: generate new signer key pair

        elif private_key is not None:
            self._init_from_private_key(private_key)
            # signer mode: private key provided

        else:
            self._init_from_public_key(public_key)
            # verifier-only mode: must have public key


    def _init_from_new_key(self, key_size: int) -> None:
        """
        Generate a new private key and initialize signer fields.

        :param key_size: key size (in bits)
        """

        private_key = rsa.generate_private_key(
            public_exponent=PUBLIC_EXPONENT,
            key_size=key_size,
            backend=default_backend(),
        )

        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        self.private_key = private_key_bytes.decode("utf-8")
        self._private_key = private_key

        public_key_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.public_key = public_key_bytes.decode("utf-8")


    def _init_from_private_key(self, private_key: str) -> None:
        """
        Initialize signer mode from an existing private key PEM.

        :param private_key: private key PEM string
        """

        self.private_key = private_key
        self._private_key = serialization.load_pem_private_key(
            private_key.encode("utf-8"),
            password=None,
            backend=default_backend(),
        )

        public_key_bytes = self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.public_key = public_key_bytes.decode("utf-8")


    def _init_from_public_key(self, public_key: str) -> None:
        """
        Initialize verifier-only mode from a public key PEM.

        :param public_key: public key PEM string
        """

        self.private_key = None
        self.public_key = public_key
        self._public_key = serialization.load_pem_public_key(
            public_key.encode("utf-8"),
            backend=default_backend(),
        )


    def sign(self, message: dict) -> str:
        """
        Generate a digital signature.

        :param message: message JSON dictionary to digitally sign
        :return: base64 digital signature string
        """

        message = self._json_canon(message)
        signature = self._private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        # sign the message using RSA and SHA-256

        return base64.b64encode(signature).decode("utf-8")


    def verify(self, signature: str, message: dict) -> bool:
        """
        Verify a digital signature.

        :param signature: the base64 digital signature string to verify
        :param message: digitally signed message JSON dictionary
        :return: True if valid and False otherwise
        """

        message = self._json_canon(message)
        signature = base64.b64decode(signature)

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

        except InvalidSignature:
            return False
            # return true if invalid



AKC = RSA
# standard asymmetric key signature object (multi-use)