from coding import *
from crypto import *
from steganography import *
from telegram import *

TG_KEY = '5711287527:AAHQMFrzh31umMnzxD7rqXrb_oXwfdI19dM'

INPUT_FILE_NAME = 'samples/lenna.png'
STEG_FILE_NAME = 'stegano.jpg'
TGOUT_FILE_NAME = 'tgout.jpg'

KEY_PATH = '.'

PERMUTE_SEED = 42

MESSAGE = 'Group 7 Digital Image Processing:\nMohammad Ali Sadraei Javaheri\nSeyed Ali Yaghoub Nejad\nMohammad Aref Jahanmir Yazdi\nAli Amirinejad'

RSACrypto.generate_private_key(KEY_PATH)

#_______Conceal Part_______
with open(f"{KEY_PATH}/public_key.pem", "rb") as f:
    public_key = serialization.load_pem_public_key(
        f.read()
    )

encrypto = RSACrypto(public_key=public_key)
source_coder = SourceCodingZlib()
channel_coders = [ChannelCodingPermute(PERMUTE_SEED), ChannelCodingHamming74()]
stegano = steganography(crypto_obj=encrypto, source_coder=source_coder, channel_coders=channel_coders)
tg_api = jpeg_telegram(TG_KEY)

stegano_image, encoded_msg = stegano.conceal(INPUT_FILE_NAME, MESSAGE, export_raw=True)
cv2.imwrite(STEG_FILE_NAME, stegano_image, [cv2.IMWRITE_JPEG_QUALITY, 100])
tg_api.save_as_telegram(STEG_FILE_NAME, TGOUT_FILE_NAME)

#_______Reveal Part_______
with open(f"{KEY_PATH}/key.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(
        f.read(),
        password=None
    )

encrypto = RSACrypto(private_key=private_key)
source_coder = SourceCodingZlib()
channel_coders = [ChannelCodingPermute(PERMUTE_SEED), ChannelCodingHamming74()]
stegano = steganography(crypto_obj=encrypto, source_coder=source_coder, channel_coders=channel_coders)

try:
    recover_msg = stegano.reveal(TGOUT_FILE_NAME)
    print(recover_msg)
except:
    after_encoded_msg = stegano.reveal(TGOUT_FILE_NAME, export_raw=True)
    print("Couldn't decode reason:")
    print(CryptoBase.bytes_diff(encoded_msg, after_encoded_msg))