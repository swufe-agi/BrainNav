import time
import openai  # 用于与 OpenAI API 交互
import base64  # 用于图像的 Base64 编码
import requests
import json
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


def gpt_infer(system, text, model="gpt-4o-2024-05-13", max_tokens=2000, response_format=None):
    """
    调用 GPT 模型进行推理，仅结合文本输入生成模型的输出。
    :param system: 系统角色描述，task_description
    :param text: 用户输入的文本（如任务描述和节点文字信息）environment_prompts
    :param model: 使用的 GPT 模型
    :param max_tokens: 最大 token 数
    :param response_format: 模型输出格式
    :return: 模型的输出内容和 token 使用情况
    """
    # 构建消息列表：系统角色 + 用户输入
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text}  # 这里的 text 是 nav_input["prompts"]
    ]

    # 调用 GPT 模型的 API
    chat_message = completion_with_backoff(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=max_tokens,
        response_format=response_format
    )

    try:
        # 提取输出内容和 token 消耗
        answer = chat_message['choices'][0]['message']['content']
        tokens = chat_message['usage']
    except KeyError as e:
        print(f"错误：缺少预期的键 '{e.args[0]}'")
        # print(f"响应结构：{chat_message}")
        raise e

    return answer, tokens



def gpt_infer_image(instruction, image_prompt, image_list, image_index=1, response_format=None):
    user_content = [
        {"type": "text", "text": f"当前指令是：{instruction}"},
        {"type": "text", "text": image_prompt}
    ]

    for i, image_url in enumerate(image_list):
        if image_url:
            user_content.append({"type": "text", "text": f"Image {image_index + i}:"})
            image_message = {
                "type": "image_url",
                "image_url": {"url": image_url, "detail": "low"}
            }
            user_content.append(image_message)

    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_content}
    ]

    # 打印请求内容
    # print("Request Messages:", messages)

    try:
        chat_message = completion_with_backoff(
            model="gpt-4-vision-preview",
            messages=messages,
            temperature=0,
            max_tokens=1000,
            response_format=response_format
        )
        # print("Response:", chat_message)  # 打印响应内容
        answer = chat_message['choices'][0]['message']['content']
        tokens = chat_message['usage']
    except KeyError as e:
        print(f"Error: Missing expected key '{e}' in the response")
        # print(f"Full Response: {chat_message}")
        answer = None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        answer = None

    return answer

def gpt_infer_with_item_list_and_check(file_path, instruction, system="任务指令与物品匹配查询", model="gpt-4o-2024-05-13", max_tokens=2000, response_format=None):
    """
    检查 item_list_storage.json 是否为空，如果不为空，则调用 GPT 模型推理，并根据指令返回相关物品的ID。
    :param file_path: 存储 item_list 的文件路径
    :param instruction: 当前的导航指令
    :param system: 系统角色描述
    :param model: 使用的 GPT 模型
    :param max_tokens: 最大 token 数
    :param response_format: 模型输出格式
    :return: 返回推理得到的物品ID，若文件为空或出错返回 None
    """
    try:
        # 读取 item_list_storage.json 文件
        with open(file_path, 'r') as f:
            item_list_data = json.load(f)

        # 如果文件不为空，进行推理
        if item_list_data:
            # 根据文件的数据结构（list 或 dict）处理
            item_list_text = ""
            # 遍历列表中的每个字典
            for idx, item_dict in enumerate(item_list_data):
                item_list_text += f"第 {idx+1} 组物品：\n"
                # 每组物品按键值对输出
                for key, value in item_dict.items():
                    item_list_text += f"{key}: {', '.join(value)}\n"

            # 构造提示词：加入指令
            prompt = f"以下是物品列表：\n{item_list_text}\n\n指令：{instruction}\n\n如果这份json文件中有和我的指令相关联的物品，请返回其对应的数字ID，只返回数字，不要附加其他字符。例如，如果是'image7'，请只返回 '7'。"

            # 构建消息列表：系统角色 + 用户输入 + item_list
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]

            # 调用 GPT 模型的 API
            chat_message = completion_with_backoff(
                model=model,
                messages=messages,
                temperature=0,
                max_tokens=max_tokens,
                response_format=response_format
            )

            # 提取模型输出
            try:
                answer = chat_message['choices'][0]['message']['content']
                tokens = chat_message['usage']
            except KeyError as e:
                print(f"错误：缺少预期的键 '{e.args[0]}'")
                raise e

            # 提取返回的数字ID
            # 假设返回的内容格式是 'image12'，我们只提取数字部分
            place_sign_id = ''.join(filter(str.isdigit, answer.strip()))  # 提取数字部分

            # 返回推理得到的物品ID
            if place_sign_id:
                return place_sign_id, tokens  # 返回物品ID和token信息
            else:
                return None, None

        else:
            # 如果文件为空
            print(f"{file_path} 为空，跳过大模型推理。")
            return None, None

    except Exception as e:
        print(f"处理 {file_path} 时发生错误：{e}")
        return None, None
