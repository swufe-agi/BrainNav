import time
import openai  # 用于与 OpenAI API 交互
import base64  # 用于图像的 Base64 编码
import requests
from tenacity import retry, stop_after_attempt, wait_random_exponential  # 用于实现自动重试功能

# 定义 OpenAI API的自定义地址
BASE_URL = "https://api.zhizengzeng.com/v1/"  # 设置 API 基本地址

# 设置 OpenAI API 密钥
generation_key = "sk-zk2c4b213015f58f0d2957af61df98d72be6732fffaaa24e"  # 生成的 OpenAI 密钥
openai.api_key = generation_key  # 设置 OpenAI 密钥
openai.api_base = BASE_URL  # 设置 OpenAI API 的自定义地址

# 装饰器：用于自动重试 API 请求
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion_with_backoff(**kwargs):
    """
    调用 OpenAI 的聊天补全接口并实现自动重试的功能。
    在请求失败时会自动等待并重试，最多重试6次，等待时间遵循指数回退。
    """
    return openai.ChatCompletion.create(**kwargs)


def gpt_infer(system, text, image_list, model="gpt-4-vision-preview",  image_index =1 ,max_tokens=1000, response_format=None):
    """
    调用 GPT 模型进行推理，结合文本和图像信息生成模型的输出。
    """

    user_content = []

    # 准备用户输入内容，包括图像和文本
    for i, image in enumerate(image_list):
        if image is not None:
            user_content.append({"type": "text", "text": f"Image {image_index+i}:"})


            #打开本地文件的方法
            # # 打开并读取图像文件，将其编码为 Base64
            # try:
            #     with open(image, "rb") as image_file:
            #         image_base64 = base64.b64encode(image_file.read()).decode('utf-8')  # 将图像文件编码为 Base64 格式并解码为字符串

            #     # 调试：打印图像信息，检查图像是否成功读取并编码
            #     # print(f"Image {i} successfully encoded to Base64, length of encoded data: {len(image_base64)}")

            # except Exception as e:
            #     print(f"Error encoding image {i}: {e}")

            # # 创建图像消息对象，将图像作为 URL 传递
            # image_message = {
            #     "type": "image_url",
            #     "image_url": {
            #         "url": f"data:image/jpeg;base64,{image_base64}",  # 将 Base64 编码的图像嵌入 URL 中
            #         "detail": "low"  # 图像细节程度（低/中/高）
            #     }
            # }
            # user_content.append(image_message)  # 将图像消息添加到用户内容中

            # 采用cos的地址的方法
            image_message = {
                "type": "image_url",
                "image_url": {
                    "url": f"{image}",  # 传递图像的 URL
                    "detail": "low"
                }
            }
            user_content.append(image_message)

    # 添加用户的文本输入
    user_content.append({"type": "text", "text": text})

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content}
    ]

    # 调用 OpenAI API
    chat_message = completion_with_backoff(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=max_tokens,
        response_format=response_format
    )

    # # 打印完整的响应，检查其结构
    # print("完整的 API 响应：", chat_message)

    try:
        # 提取模型的回答和 token 消耗情况
        answer = chat_message['choices'][0]['message']['content']
        tokens = chat_message['usage']
    except KeyError as e:
        print(f"错误：缺少预期的键 '{e.args[0]}'，响应结构如下：")
        print(f"响应结构：{chat_message}")
        raise e

    return answer, tokens













# import base64
# import requests
# import time

# def download_and_encode_image(image_url, max_retries=3, timeout=10):
#     """
#     下载图像并将其编码为 base64 格式。
#     """
#     attempt = 0
#     while attempt < max_retries:
#         try:
#             response = requests.get(image_url, timeout=timeout)
#             response.raise_for_status()  # 如果请求失败，抛出异常
#             # 转换图像为 base64 编码
#             encoded_image = base64.b64encode(response.content).decode('utf-8')
#             return encoded_image  # 返回编码后的图像内容
#         except requests.exceptions.RequestException as e:
#             attempt += 1
#             print(f"下载失败，尝试第 {attempt} 次，错误：{e}")
#             time.sleep(2)  # 等待 2 秒再重试
#     raise Exception(f"图像下载失败：{image_url}")

# # 在 gpt_infer 函数中使用下载并编码的图像内容
# def gpt_infer(system, text, image_list, model="gpt-4-vision-preview", max_tokens=1000, response_format=None):
#     user_content = []

#     for i, image in enumerate(image_list):
#         if image is not None:
#             user_content.append({"type": "text", "text": f"Image {i+1}:"})

#             # 下载并编码图像
#             try:
#                 encoded_image = download_and_encode_image(image)
#                 image_message = {
#                     "type": "image_data",
#                     "image_data": encoded_image
#                 }
#                 user_content.append(image_message)
#             except Exception as e:
#                 print(f"图像下载或编码失败: {e}")
#                 continue  # 如果下载或编码失败，跳过这张图像

#     user_content.append({"type": "text", "text": text})

#     messages = [
#         {"role": "system", "content": system},
#         {"role": "user", "content": user_content}
#     ]

#     chat_message = completion_with_backoff(
#         model=model,
#         messages=messages,
#         temperature=0,
#         max_tokens=max_tokens,
#         response_format=response_format
#     )

#     # 检查响应结构并获取答案
#     try:
#         answer = chat_message['choices'][0]['message']['content']
#         tokens = chat_message['usage']
#     except KeyError as e:
#         print(f"错误：缺少预期的键 '{e.args[0]}'，响应结构如下：")
#         print(f"响应结构：{chat_message}")
#         raise e

#     return answer, tokens