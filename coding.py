import zlib
import operator 
import random
import numpy as np

class SourceCodingBase():
    def encode(self, message: str) -> bytes:
        return message.encode('utf-8')
    
    def decode(self, message: bytes) -> str:
        return message.decode('utf-8')

class SourceCodingZlib(SourceCodingBase):
    def encode(self, message: str) -> bytes:
        return zlib.compress(super().encode(message))
    
    def decode(self, message: bytes) -> str:
        return super().decode(zlib.decompress(message))

class ChannelCodingBase():
    def encode(self, message: bytes) -> bytes:
        return message
    
    def decode(self, message: bytes) -> bytes:
        return message

class ChannelCodingPermute(ChannelCodingBase):
    def __init__(self, seed):
        self.seed = seed
        
    def __generate_permutation(self, l):
        return_value = list(range(l))
        random.Random(self.seed).shuffle(return_value)
        return return_value
    
    def __reverse_permutation(self, l):
        orig = self.__generate_permutation(l)
        reverse_dict = {k: v for v, k in enumerate(orig)}
        return list(map(reverse_dict.get, range(l)))

    def __permute(self, message, permutation):
        return bytes([message[idx] for idx in permutation])

    def encode(self, message: bytes) -> bytes:
        return self.__permute(message, self.__generate_permutation(len(message)))
    
    def decode(self, message: bytes) -> bytes:
        return self.__permute(message, self.__reverse_permutation(len(message)))

class ChannelCodingHamming74(ChannelCodingBase):
    def __init__(self):
        self.__h = np.array([[1, 0, 1, 0, 1, 0, 1],
                             [0, 1, 1, 0, 0, 1, 1],
                             [0, 0, 0, 1, 1, 1, 1]])
        
        self.__g = np.array([[1, 1, 0, 1],
                             [1, 0, 1, 1],
                             [1, 0, 0, 0],
                             [0, 1, 1, 1],
                             [0, 1, 0, 0],
                             [0, 0, 1, 0],
                             [0, 0, 0, 1]]).T

    def __encode_block(self, block):
        all_res = []
        for row in self.__g.T:
            row_res = 0
            for mask, b in zip(row, block):
                if mask:
                    row_res = row_res ^ b
            all_res.append(row_res)
        return bytes(all_res)

    def __check_decode_error(self, block):
        all_res = []
        for row in self.__h:
            row_res = 0
            for mask, b in zip(row, block):
                if mask:
                    row_res = row_res ^ b
            all_res.append(row_res)
        return bytes(all_res)

    def __decode_block(self, block):
        z = self.__check_decode_error(block)
        z_np = np.array(list(z), 'uint8')
        if any(z): # We need an error to correct!
            print('Log: Hamming found an error')
            e = [0] * 7
            for i in range(8):
                z_m = ((z_np & (1 << i)) > 0).astype('uint8')
                e_loc = z_m[0] + 2 * z_m[1] + 4 * z_m[2]
                if e_loc != 0:
                    e[e_loc-1] += 1 << i

            block = list(map(lambda x: x[0] ^ x[1], zip(e, block)))

        return bytes([block[2], *block[4:]])
    
    def encode(self, message: bytes) -> bytes:
        result = b''
        for i in range(0, len(message), 4):
            if i+4 <= len(message):
                result += self.__encode_block(message[i: i+4])
            else:
                result += message[i: i+4]
        return result
    
    def decode(self, message: bytes) -> bytes:
        result = b''
        for i in range(0, len(message), 7):
            if i+7 <= len(message):
                result += self.__decode_block(message[i: i+7])
            else:
                result += message[i: i+7]
        return result