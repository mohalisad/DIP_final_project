import cv2
import struct
import bitstring
import numpy as np

from coding import *
from crypto import *

class steganography:
    class YCC_Image(object):
        def __init__(self, cover_image):
            self.height, self.width = cover_image.shape[:2]
            self.channels = [
                            self.split_image_into_blocks(cover_image[:,:,0]),
                            self.split_image_into_blocks(cover_image[:,:,1]),
                            self.split_image_into_blocks(cover_image[:,:,2]),
                            ]
        @staticmethod
        def split_image_into_blocks(image):
            blocks = []
            for vert_slice in np.vsplit(image, int(image.shape[0] / 8)):
                for horiz_slice in np.hsplit(vert_slice, int(image.shape[1] / 8)):
                    blocks.append(horiz_slice)
            return blocks

        @staticmethod
        def merge_blocks(Nc, block_segments):
            image_rows = []
            temp = []
            for i in range(len(block_segments)):
                if i > 0 and not(i % int(Nc / 8)):
                    image_rows.append(temp)
                    temp = [block_segments[i]]
                else:
                    temp.append(block_segments[i])
            image_rows.append(temp)

            return np.block(image_rows)

    def __init__(self, crypto_obj = None, source_coder=None, channel_coders=None):
        self.Q_table = np.asarray([ [16, 11, 10, 16,  24, 40,   51,  61],
                                    [12, 12, 14, 19,  26, 58,   60,  55],
                                    [14, 13, 16, 24,  40, 57,   69,  56],
                                    [14, 17, 22, 29,  51, 87,   80,  62],
                                    [18, 22, 37, 56,  68, 109, 103,  77],
                                    [24, 36, 55, 64,  81, 104, 113,  92],
                                    [49, 64, 78, 87, 103, 121, 120, 101],
                                    [72, 92, 95, 98, 112, 100, 103,  99]],
                                    dtype = np.float32)
        if crypto_obj is None:
            crypto_obj = NoCrypto()
        if source_coder is None:
            source_coder = SourceCodingBase()
        if channel_coders is None:
            channel_coders = [ChannelCodingBase()]

        self.crypto_obj = crypto_obj
        self.source_coder = source_coder
        self.channel_coders = channel_coders

    def zigzag(self, input):
        h = 0
        v = 0
        vmin = 0
        hmin = 0
        vmax = input.shape[0] # 8
        hmax = input.shape[1] # 8
        i = 0
        output = np.zeros(( vmax * hmax))

        while ((v < vmax) and (h < hmax)):

            if ((h + v) % 2) == 0:                 # going up
                if (v == vmin):
                    output[i] = input[v, h]        # if we got to the first line
                    if (h == hmax):
                        v = v + 1
                    else:
                        h = h + 1
                    i = i + 1

                elif ((h == hmax -1 ) and (v < vmax)):   # if we got to the last column
                    output[i] = input[v, h]
                    v = v + 1
                    i = i + 1

                elif ((v > vmin) and (h < hmax -1 )):    # all other cases
                    output[i] = input[v, h]
                    v = v - 1
                    h = h + 1
                    i = i + 1


            else:                                    # going down
                if ((v == vmax -1) and (h <= hmax -1)):       # if we got to the last line
                    output[i] = input[v, h]
                    h = h + 1
                    i = i + 1

                elif (h == hmin):                  # if we got to the first column
                    output[i] = input[v, h]
                    if (v == vmax -1):
                        h = h + 1
                    else:
                        v = v + 1
                    i = i + 1

                elif ((v < vmax -1) and (h > hmin)):     # all other cases
                    output[i] = input[v, h]
                    v = v + 1
                    h = h - 1
                    i = i + 1

            if ((v == vmax-1) and (h == hmax-1)):          # bottom right element
                output[i] = input[v, h]
                break

        return output

    def inverse_zigzag(self, input, vmax, hmax):
        h = 0
        v = 0
        vmin = 0
        hmin = 0
        output = np.zeros((vmax, hmax))
        i = 0

        while ((v < vmax) and (h < hmax)):
            if ((h + v) % 2) == 0:                 # going up
                if (v == vmin):
                    output[v, h] = input[i]        # if we got to the first line
                    if (h == hmax):
                        v = v + 1
                    else:
                        h = h + 1
                    i = i + 1

                elif ((h == hmax -1 ) and (v < vmax)):   # if we got to the last column
                    output[v, h] = input[i]
                    v = v + 1
                    i = i + 1

                elif ((v > vmin) and (h < hmax -1 )):    # all other cases
                    output[v, h] = input[i]
                    v = v - 1
                    h = h + 1
                    i = i + 1

            else:                                    # going down

                if ((v == vmax -1) and (h <= hmax -1)):       # if we got to the last line
                    output[v, h] = input[i]
                    h = h + 1
                    i = i + 1

                elif (h == hmin):                  # if we got to the first column
                    output[v, h] = input[i]
                    if (v == vmax -1):
                        h = h + 1
                    else:
                        v = v + 1
                    i = i + 1

                elif((v < vmax -1) and (h > hmin)):     # all other cases
                    output[v, h] = input[i]
                    v = v + 1
                    h = h - 1
                    i = i + 1

            if ((v == vmax-1) and (h == hmax-1)):          # bottom right element
                output[v, h] = input[i]
                break

        return output


    def _extract_encoded_data_from_DCT(self, dct_blocks):
        extracted_data = ""
        for current_dct_block in dct_blocks:
            for i in range(1, len(current_dct_block)):
                curr_coeff = np.int32(current_dct_block[i])
                if (curr_coeff > 1):
                    curr_bit = (np.uint8(current_dct_block[i]) & 0x01) ^ (np.uint8(current_dct_block[i]) & 0x80)
                    extracted_data += bitstring.pack('uint:1', curr_bit)
        return extracted_data

    def _embed_encoded_data_into_DCT(self, encoded_bits, dct_blocks):
        data_complete = False
        encoded_bits.pos = 0
        encoded_data_len = bitstring.pack('uint:32', len(encoded_bits))
        converted_blocks = []
        for current_dct_block in dct_blocks:
            for i in range(1, len(current_dct_block)):

                curr_coeff = np.int32(current_dct_block[i])

                if curr_coeff > 1:
                    curr_coeff = np.uint8(current_dct_block[i])

                    if encoded_bits.pos == len(encoded_bits) - 1: 
                        data_complete = True; break

                    pack_coeff = bitstring.pack('uint:8', curr_coeff)
                    if encoded_data_len.pos <= len(encoded_data_len) - 1: 
                        data_bit = encoded_data_len.read(1)

                    else: 
                        data_bit = encoded_bits.read(1)

                    if pack_coeff[0] == True:
                        msb = bitstring.BitStream(bin='1')
                    else:
                        msb = bitstring.BitStream(bin='0')

                    pack_coeff[-1] = data_bit ^ msb
                    # Replace converted coefficient
                    current_dct_block[i] = np.float32(pack_coeff.read('uint:8'))
            converted_blocks.append(current_dct_block)

        if not(data_complete): raise ValueError("Data didn't fully embed into cover image!")

        return converted_blocks

    def __encode(self, message):
        message = self.source_coder.encode(message)
        message = self.crypto_obj.encrypt(message)
        for coder in self.channel_coders:
            message = coder.encode(message)
        return message
    
    def __decode(self, message):
        for coder in reversed(self.channel_coders):
            message = coder.decode(message)
        message = self.crypto_obj.decrypt(message)
        message = self.source_coder.decode(message)
        return message

    def conceal(self, src_path, msg, export_raw=False):
        encoded_msg = self.__encode(msg)
        raw_cover_image = cv2.imread(src_path, flags=cv2.IMREAD_COLOR)
        try:
            height, width, no_channels = raw_cover_image.shape
        except:
            height, width = raw_cover_image.shape
            no_channels = 1
        # Force Image Dimensions to be 8x8 compliant
        while(height % 8): height += 1 # Rows
        while(width  % 8): width  += 1 # Cols
        valid_dim = (width, height)
        padded_image    = cv2.resize(raw_cover_image, valid_dim)
        cover_image_f32 = np.float32(padded_image)
        cover_image_YCC = self.YCC_Image(cv2.cvtColor(cover_image_f32, cv2.COLOR_BGR2YCrCb))

        # Placeholder for holding stego image data
        stego_image = np.empty_like(cover_image_f32)

        for chan_index in range(no_channels):
            # FORWARD DCT STAGE
            dct_blocks = [cv2.dct(block) for block in cover_image_YCC.channels[chan_index]]

            # QUANTIZATION STAGE
            dct_quants = [np.around(np.divide(item, self.Q_table)) for item in dct_blocks]

            # Sort DCT coefficients by frequency
            sorted_coefficients = [self.zigzag(block) for block in dct_quants]

            # Embed data in Luminance layer
            if (chan_index == 0):
                # DATA INSERTION STAGE
                secret_data = ""
                for char in encoded_msg: 
                    secret_data += bitstring.pack('uint:8', char)
                embedded_dct_blocks   = self._embed_encoded_data_into_DCT(secret_data, sorted_coefficients)
                desorted_coefficients = [self.inverse_zigzag(block, vmax=8,hmax=8) for block in embedded_dct_blocks]
            else:
                # Reorder coefficients to how they originally were
                desorted_coefficients = [self.inverse_zigzag(block, vmax=8,hmax=8) for block in sorted_coefficients]

            # DEQUANTIZATION STAGE
            dct_dequants = [np.multiply(data, self.Q_table) for data in desorted_coefficients]

            # Inverse DCT Stage
            idct_blocks = [cv2.idct(block) for block in dct_dequants]

            # Rebuild full image channel
            stego_image[:,:,chan_index] = np.asarray(self.YCC_Image.merge_blocks(cover_image_YCC.width, idct_blocks))
        #-------------------------------------------------------------------------------------------------------------------#

        # Convert back to RGB (BGR) Colorspace
        stego_image_BGR = cv2.cvtColor(stego_image, cv2.COLOR_YCR_CB2BGR)

        # Clamp Pixel Values to [0 - 255]
        final_stego_image = np.uint8(np.clip(stego_image_BGR, 0, 255))

        if export_raw:
            return final_stego_image, encoded_msg

        return final_stego_image

    def reveal(self, src_path, export_raw=False):
        stego_image = cv2.imread(src_path, flags=cv2.IMREAD_COLOR)
        stego_image_f32 = np.float32(stego_image)
        stego_image_YCC = self.YCC_Image(cv2.cvtColor(stego_image_f32, cv2.COLOR_BGR2YCrCb))

        # FORWARD DCT STAGE
        dct_blocks = [cv2.dct(block) for block in stego_image_YCC.channels[0]]  # Only care about Luminance layer

        # QUANTIZATION STAGE
        dct_quants = [np.around(np.divide(item, self.Q_table)) for item in dct_blocks]

        # Sort DCT coefficients by frequency
        sorted_coefficients = [self.zigzag(block) for block in dct_quants]

        # DATA EXTRACTION STAGE
        recovered_data = self._extract_encoded_data_from_DCT(sorted_coefficients)

        # Determine length of secret message
        data_len = int(recovered_data.read('uint:32') / 8)

        # Extract secret message from DCT coefficients
        extracted_data = bytes()
        for _ in range(data_len): 
            extracted_data += struct.pack('>B', recovered_data.read('uint:8'))
        
        if export_raw:
            return extracted_data

        return self.__decode(extracted_data)