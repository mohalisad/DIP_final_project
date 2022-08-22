import requests

class jpeg_telegram:
    def __init__(self, bot_token):
        self.bot_token = bot_token
    
    def __send_request(self, endpoint, params, files=None):
        url = f"https://api.telegram.org/bot{self.bot_token}/{endpoint}?{params}"
        if files is None:
            files = []
        response = requests.get(url, files=files)
        return response.json()
    
    def __send_img(self, path):
        files=[('photo', ('stegano.jpg', open(path, 'rb'), 'image/jpeg'))]
        return self.__send_request('sendPhoto', 'chat_id=@cv2jpegchannel', files)

    def __get_img(self, file_id):
        return self.__send_request('getFile', f'file_id={file_id}')

    def __download_file(self, file_path):
        url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
        return requests.get(url)

    def save_as_telegram(self, orig_path, dst_path):
        send_img_resp = self.__send_img(orig_path)
        images = sorted(send_img_resp['result']['photo'], key=lambda x: x['file_size'])
        file_id = images[-1]['file_id']

        get_img_resp = self.__get_img(file_id)
        file_path = get_img_resp['result']['file_path']

        file_resp = self.__download_file(file_path)
        with open(dst_path, 'wb') as f:
            f.write(file_resp.content)