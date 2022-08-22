import abc
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class CryptoBase():
    @abc.abstractmethod
    def encrypt(self, message: bytes) -> bytes: pass
    
    @abc.abstractmethod
    def decrypt(self, message: bytes) -> bytes: pass

    @staticmethod
    def bytes_diff(first: bytes, second: bytes):
        if len(first) == len(second):
            bytes_xor = map(lambda b: b[0] ^ b[1], zip(first, second))
            diff = sum(map(lambda b: bin(b).count('1'), bytes_xor))
            return f'diff bits count={diff}'
        else:
            return 'diff length'

class NoCrypto(CryptoBase):
    def encrypt(self, message: bytes) -> bytes:
        return message

    def decrypt(self, message: bytes) -> bytes:
        return message

class RSACrypto(CryptoBase):
    def __init__(self, private_key = None, public_key = None):
        if private_key is not None:
            self.private_key = private_key
            self.public_key = private_key.public_key()
        elif public_key is not None:
            self.public_key = public_key
        else:
            raise Exception("You must pass one of the keys")

    def encrypt(self, message: bytes) -> bytes:
        if self.public_key is not None:
            return self.public_key.encrypt(
                message,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        else:
            raise Exception("You cant do that")

    def decrypt(self, message: bytes) -> bytes:
        if self.private_key is not None:
            return self.private_key.decrypt(
                message,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        else:
            raise Exception("You cant do that")

    @staticmethod
    def generate_private_key(output_path=None):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        if output_path is not None:
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            with open(f'{output_path}/key.pem', 'wb') as f:
                f.write(pem)
            
            public_key = private_key.public_key()
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            with open(f'{output_path}/public_key.pem', 'wb') as f:
                f.write(pem)

        return private_key