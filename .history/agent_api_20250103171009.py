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

    try:
        answer = chat_message['choices'][0]['message']['content']
        tokens = chat_message['usage']
    except KeyError as e:
        print(f"错误：缺少预期的键 '{e.args[0]}'，响应结构如下：")
        print(f"响应结构：{chat_message}")
        raise e

    return answer, tokens