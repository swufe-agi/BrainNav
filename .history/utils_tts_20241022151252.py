# import base64
# import hashlib
# import hmac
# import json
# import time
# from datetime import datetime
# from http.client import HTTPSConnection
# import os
# import wave
# import pyaudio
# from voice_recognition import *
# from utils_llm import *

# # 从 API_KEY.py 文件导入密钥和 ID
# from API_KEY import VOICE_SECRET_ID, VOICE_SECRET_KEY
# token = ""

# # 请求相关参数
# service = "tts"
# host = "tts.tencentcloudapi.com"
# region = "ap-chengdu"
# version = "2019-08-23"
# action = "TextToVoice"
# endpoint = "https://tts.tencentcloudapi.com"
# algorithm = "TC3-HMAC-SHA256"

# # 播放音频的函数
# def play_audio_file(file_path):
#     chunk = 1024
#     wf = wave.open(file_path, 'rb')
#     p = pyaudio.PyAudio()

#     # 打开音频流
#     stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
#                     channels=wf.getnchannels(),
#                     rate=wf.getframerate(),
#                     output=True)

#     # 读取并播放音频数据
#     data = wf.readframes(chunk)
#     while data:
#         stream.write(data)
#         data = wf.readframes(chunk)

#     # 关闭流和 PyAudio
#     stream.stop_stream()
#     stream.close()
#     p.terminate()

# # 签名函数
# def sign(key, msg):
#     return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

# # 获取下一个文件名
# def get_next_filename(folder_path):
#     # 确保文件夹存在
#     if not os.path.exists(folder_path):
#         os.makedirs(folder_path)

#     # 获取所有已存在的文件
#     existing_files = [f for f in os.listdir(folder_path) if f.startswith("text_voice") and f.endswith(".wav")]

#     # 找到最新的文件编号
#     if existing_files:
#         last_number = max(int(f.split("text_voice")[1].split(".wav")[0]) for f in existing_files)
#         next_number = last_number + 1
#     else:
#         next_number = 1

#     return os.path.join(folder_path, f"text_voice{next_number}.wav")

# # 生成语音并保存的函数
# def generate_and_play_audio(text):
#     # 时间戳和日期
#     timestamp = int(time.time())
#     date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

#     # 拼接请求载荷
#     payload = json.dumps({"Text": text, "SessionId": "session-1234"})

#     # 拼接规范请求串
#     http_request_method = "POST"
#     canonical_uri = "/"
#     canonical_querystring = ""
#     ct = "application/json; charset=utf-8"
#     canonical_headers = f"content-type:{ct}\nhost:{host}\nx-tc-action:{action.lower()}\n"
#     signed_headers = "content-type;host;x-tc-action"
#     hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
#     canonical_request = (http_request_method + "\n" +
#                          canonical_uri + "\n" +
#                          canonical_querystring + "\n" +
#                          canonical_headers + "\n" +
#                          signed_headers + "\n" +
#                          hashed_request_payload)

#     # 拼接待签名字符串
#     credential_scope = f"{date}/{service}/tc3_request"
#     hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
#     string_to_sign = (algorithm + "\n" +
#                       str(timestamp) + "\n" +
#                       credential_scope + "\n" +
#                       hashed_canonical_request)

#     # 计算签名
#     secret_date = sign(("TC3" + VOICE_SECRET_KEY).encode("utf-8"), date)
#     secret_service = sign(secret_date, service)
#     secret_signing = sign(secret_service, "tc3_request")
#     signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

#     # 拼接 Authorization
#     authorization = (algorithm + " " +
#                      "Credential=" + VOICE_SECRET_ID + "/" + credential_scope + ", " +
#                      "SignedHeaders=" + signed_headers + ", " +
#                      "Signature=" + signature)

#     # 请求头
#     headers = {
#         "Authorization": authorization,
#         "Content-Type": ct,
#         "Host": host,
#         "X-TC-Action": action,
#         "X-TC-Timestamp": str(timestamp),
#         "X-TC-Version": version
#     }
#     if region:
#         headers["X-TC-Region"] = region
#     if token:
#         headers["X-TC-Token"] = token

#     # 发起请求并处理响应
#     try:
#         req = HTTPSConnection(host)
#         req.request("POST", "/", headers=headers, body=payload.encode("utf-8"))
#         resp = req.getresponse()
#         response_data = json.loads(resp.read().decode("utf-8"))

#         # 获取 Base64 编码的 WAV 数据
#         if 'Audio' in response_data['Response']:
#             audio_base64 = response_data['Response']['Audio']

#             # 解码并保存 WAV 文件
#             output_folder = "output/text_voice"
#             output_file = os.path.join(output_folder, "text_voice.wav")
#             audio_data = base64.b64decode(audio_base64)
#             with open(output_file, "wb") as wav_file:
#                 wav_file.write(audio_data)

#             print("WAV 文件已保存至", output_file)

#             # 播放 WAV 文件
#             play_audio_file(output_file)

#         else:
#             print("请求失败：未能获取音频数据")

#     except Exception as err:
#         print("发生错误:", err)

# # 调用函数进行文本转换和播放
# text_to_speech = "您好，我是Limo—002332。"
# generate_and_play_audio(text_to_speech)

# def agent_voice_mode():
#     '''
#     语音问答模式
#     '''
#     text_to_speech = "您已选择语音输入，请开始说话。"
#     generate_and_play_audio(text_to_speech)

#     # 调用录音函数并进行语音识别
#     record()
#     order = recognize_speech(WAVE_OUTPUT_FILENAME)

#     if order:
#         print(f"语音识别的指令：{order}")
#     else:
#         text_to_speech = "未能识别语音，请重试。"
#         generate_and_play_audio(text_to_speech)
#         return

#     # 调用大模型生成内容并播放
#     result = llm_yi(order)
#     if result:
#         generate_and_play_audio(result)
#     else:
#         generate_and_play_audio("抱歉，生成内容失败。")


import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from http.client import HTTPSConnection
import os
import wave
import pyaudio
from voice_recognition import *
from utils_llm import *
import logging

# 配置日志记录器，将错误信息写入文件，而不输出到控制台
logging.basicConfig(filename='error.log', level=logging.ERROR)

# 从 API_KEY.py 文件导入密钥和 ID
from API_KEY import VOICE_SECRET_ID, VOICE_SECRET_KEY
token = ""

# 请求相关参数
service = "tts"
host = "tts.tencentcloudapi.com"
region = "ap-chengdu"
version = "2019-08-23"
action = "TextToVoice"
endpoint = "https://tts.tencentcloudapi.com"
algorithm = "TC3-HMAC-SHA256"

# 播放音频的函数
def play_audio_file(file_path):
    try:
        chunk = 1024
        wf = wave.open(file_path, 'rb')
        p = pyaudio.PyAudio()

        # 打开音频流
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        # 读取并播放音频数据
        data = wf.readframes(chunk)
        while data:
            stream.write(data)
            data = wf.readframes(chunk)

        # 关闭流和 PyAudio
        stream.stop_stream()
        stream.close()
        p.terminate()
    except Exception as e:
        logging.error("Error playing audio file:", exc_info=True)

# 签名函数
def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

# 获取下一个文件名
def get_next_filename(folder_path):
    try:
        # 确保文件夹存在
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # 获取所有已存在的文件
        existing_files = [f for f in os.listdir(folder_path) if f.startswith("text_voice") and f.endswith(".wav")]

        # 找到最新的文件编号
        if existing_files:
            last_number = max(int(f.split("text_voice")[1].split(".wav")[0]) for f in existing_files)
            next_number = last_number + 1
        else:
            next_number = 1

        return os.path.join(folder_path, f"text_voice{next_number}.wav")
    except Exception as e:
        logging.error("Error getting next filename:", exc_info=True)

# 生成语音并保存的函数
def generate_and_play_audio(text):
    try:
        # 时间戳和日期
        timestamp = int(time.time())
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

        # 拼接请求载荷
        payload = json.dumps({"Text": text, "SessionId": "session-1234"})

        # 拼接规范请求串
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        ct = "application/json; charset=utf-8"
        canonical_headers = f"content-type:{ct}\nhost:{host}\nx-tc-action:{action.lower()}\n"
        signed_headers = "content-type;host;x-tc-action"
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (http_request_method + "\n" +
                             canonical_uri + "\n" +
                             canonical_querystring + "\n" +
                             canonical_headers + "\n" +
                             signed_headers + "\n" +
                             hashed_request_payload)

        # 拼接待签名字符串
        credential_scope = f"{date}/{service}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = (algorithm + "\n" +
                          str(timestamp) + "\n" +
                          credential_scope + "\n" +
                          hashed_canonical_request)

        # 计算签名
        secret_date = sign(("TC3" + VOICE_SECRET_KEY).encode("utf-8"), date)
        secret_service = sign(secret_date, service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # 拼接 Authorization
        authorization = (algorithm + " " +
                         "Credential=" + VOICE_SECRET_ID + "/" + credential_scope + ", " +
                         "SignedHeaders=" + signed_headers + ", " +
                         "Signature=" + signature)

        # 请求头
        headers = {
            "Authorization": authorization,
            "Content-Type": ct,
            "Host": host,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": version
        }
        if region:
            headers["X-TC-Region"] = region
        if token:
            headers["X-TC-Token"] = token

        # 发起请求并处理响应
        req = HTTPSConnection(host)
        req.request("POST", "/", headers=headers, body=payload.encode("utf-8"))
        resp = req.getresponse()
        response_data = json.loads(resp.read().decode("utf-8"))

        # 获取 Base64 编码的 WAV 数据
        if 'Audio' in response_data['Response']:
            audio_base64 = response_data['Response']['Audio']

            # 解码并保存 WAV 文件
            output_folder = "output/text_voice"
            output_file = os.path.join(output_folder, "text_voice.wav")
            audio_data = base64.b64decode(audio_base64)
            with open(output_file, "wb") as wav_file:
                wav_file.write(audio_data)

            print("WAV 文件已保存至", output_file)

            # 播放 WAV 文件
            play_audio_file(output_file)

        else:
            print("请求失败：未能获取音频数据")

    except Exception as e:
        logging.error("Error generating or playing audio:", exc_info=True)

# 调用函数进行文本转换和播放
text_to_speech = "您好，我是Limo—002332。"
generate_and_play_audio(text_to_speech)

def agent_voice_mode():
    '''
    语音问答模式
    '''
    try:
        text_to_speech = "您已选择语音输入，请开始说话。"
        generate_and_play_audio(text_to_speech)

        # 调用录音函数并进行语音识别
        record()
        order = recognize_speech(WAVE_OUTPUT_FILENAME)

        if order:
            print(f"语音识别的指令：{order}")
        else:
            text_to_speech = "未能识别语音，请重试。"
            generate_and_play_audio(text_to_speech)
            return

        # 调用大模型生成内容并播放
        result = llm_yi(order)
        if result:
            generate_and_play_audio(result)
        else:
            generate_and_play_audio("抱歉，生成内容失败。")
    except Exception as e:
        logging.error("Error in agent_voice_mode:", exc_info=True)