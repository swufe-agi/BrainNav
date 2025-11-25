import cv2
import base64
import time
import openai
import requests
from API_KEY import OPENAI_API_BASE,OPENAI_API_KEY

# OpenAI API设置
openai.api_base = OPENAI_API_BASE
openai.api_key = OPENAI_API_KEY


def call_mllm_for_images(rgb_image_url,depth_image_url, order):
    """
    分析单张图像，并返回分析结果。

    参数:
    - depth_image_url: 包含深度图像的url路径。
    - rgb_image_url: 包含RGB图像的url路径。
    - order: 传入的指令

    返回:
    - 分析结果字符串，由大模型生成。
    """
    prompt = (
        '''
        你收到照片了吗？照片里面有什么，分别分析第一张rgb图像和第二张深度图像：

【我现在的指令是：】  
        '''
    )

    for _ in range(3):  # 尝试重试3次
        try:
            # 准备消息，包含 RGB 图像和深度图像
            messages = [
                {"role": "system", "content": prompt + order},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "这是你前方的RGB图像："
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": rgb_image_url
                            }
                        },
                        {
                            "type": "text",
                            "text": "这是对应的深度图像，展示了物品的位置信息："
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": depth_image_url
                            }
                        }
                    ]
                }
            ]

            # 调用 OpenAI API，进行图像信息的分析
            completion = openai.ChatCompletion.create(
                model="yi-vision",  # 确保模型支持图像分析
                messages=messages
            )

            # 获取分析结果
            analysis_result = completion.choices[0].message['content']
            return analysis_result

        except openai.error.APIError as e:
            print(f"API Error: {e}, Retrying...")
            time.sleep(5)  # 等待5秒后重试
            continue  # 继续重试
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}, Retrying...")
            time.sleep(5)

    return None  # 如果重试3次仍失败，返回None。

# 行动建议
def call_mllm_to_actions(rgb_image_url, depth_image_url, order):
    """
    分析两张图像（RGB 和深度图像），并返回分析结果。

    参数:
    - depth_image_url: 包含深度图像的url路径。
    - rgb_image_url: 包含RGB图像的url路径。
    - order: 传入的指令

    返回:
    - 分析结果字符串，由大模型生成。
    """
    prompt = (
        '''
        你是我的智能小车助手，我有以下功能，请你根据我的指令，以json形式输出要运行的对应函数和你给我的回复

【以下是所有内置函数介绍】  
1、 `limo.SetMotionCommand(self, linear_vel, angular_vel)`  
- **作用**: 发送运动控制指令，设置线速度、角速度。  
- **参数**:  
  - `linear_vel`: 线速度。  
  - `angular_vel`: 角速度。  
-传参与运动方向：第一位传参控制前后，第二位传参控制方向（与第一位传参：同正或同负为左，不同为右）
示例：
  - limo.SetMotionCommand(-0.3, -0.2)：同为负数，向左后退
  - limo.SetMotionCommand(0.3, 0.2) :同为正数，向左前进
  - limo.SetMotionCommand(0.3, -0.2)：向右前进
  - limo.SetMotionCommand(-0.3, 0.2) :向右后退
  - limo.SetMotionCommand(1, 0) :直线前进
  - limo.SetMotionCommand(1, 0) :直线后退

【输出json格式】  
输出不能照搬例子！！！！不要输出包含 ```json 的开头或结尾！！！  
你直接输出json即可，从 `{` 开始，不要输出包含 ```json 的开头或结尾,不要包含`这个符号。  
在 'function' 键中，输出函数名列表，每个元素代表一个要运行的函数名称和参数。函数可以按顺序依次运行。  
在 'response' 键中，根据我的指令和你编排的动作，以第一人称输出你回复我的话。不要超过20个字，可以幽默、使用互联网热梗或名场面台词。  
在 'analysis' 键中，基于图像的信息，输出对当前环境的分析结果，描述图片有什么，小车处于什么地方，结合RGB图像和深度图像的信息。

【以下是一些具体的例子】  
输出不能照搬例子！！！！  
我的指令：发送运动指令，向左前进
你输出：
`{ 'function': ['limo.SetMotionCommand(0.3, 0.2)'], 'response': '小车向左前进，角速度0.2', 'analysis': 'RGB图像显示小车在一个宽阔的房间内，周围有桌椅，空间充足。深度图像显示前方2米内没有障碍物，可以安全前进。' }`

我的指令：发送运动指令，向左后退
你输出：
`{ 'function': ['limo.SetMotionCommand(-0.3, -0.2)'], 'response': '小车向左后退，速度-0.3', 'analysis': 'RGB图像显示一个室外停车场，旁边停着几辆车。深度图像显示，小车后方1.5米内无障碍物，安全后退。' }`

我的指令：发送运动指令，向右前进
你输出：
`{ 'function': ['limo.SetMotionCommand(0.3, -0.2)'], 'response': '小车向右前进，角速度-0.2', 'analysis': 'RGB图像显示在一条走廊上，左右两边有几扇门。深度图像显示前方3米处有空旷区域，前进无阻。' }`

我的指令：发送运动指令，向右后退
你输出：
`{ 'function': ['limo.SetMotionCommand(-0.3, 0.2)'], 'response': '小车向右后退，速度-0.3', 'analysis': 'RGB图像显示小车停在室内，旁边有一些办公家具。深度图像显示小车后方2米处无障碍，安全后退。' }`

我的指令：发送运动指令，直线前进
你输出：
`{ 'function': ['limo.SetMotionCommand(1, 0)'], 'response': '直线前进，速度1m/s', 'analysis': 'RGB图像显示在一条宽阔的道路上，前方开阔没有障碍物。深度图像显示，小车前方物体距离大于5米，可以直线前进。' }`

我的指令：发送运动指令，直线后退
你输出：
`{ 'function': ['limo.SetMotionCommand(-1, 0)'], 'response': '直线后退，速度-1m/s', 'analysis': 'RGB图像显示在室外空旷区域，后方视野开阔。深度图像显示，小车后方3米内无障碍，后退安全。' }`

不要输出包含 ```json 的开头或结尾！！！

【一些互联网热梗和名场面】  
“路见不平，拔刀相助。”  
“不知道，就问问小编。”  
“有事没事找我，反正我很闲。”

【我现在的指令是：】  
    '''
    )

    for _ in range(3):  # 尝试重试3次
        try:
            # 准备消息，包含 RGB 图像和深度图像
            messages = [
                {"role": "system", "content": prompt + order},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "这是你前方的RGB图像："
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": rgb_image_url
                            }
                        },
                        {
                            "type": "text",
                            "text": "这是对应的深度图像，展示了物品的位置信息："
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": depth_image_url
                            }
                        }
                    ]
                }
            ]

            # 调用 OpenAI API，进行图像信息的分析
            completion = openai.ChatCompletion.create(
                model="yi-vision",  # 确保模型支持图像分析
                messages=messages
            )

            # 获取分析结果
            analysis_result = completion.choices[0].message['content']
            return analysis_result

        except openai.error.APIError as e:
            print(f"API Error: {e}, Retrying...")
            time.sleep(5)  # 等待5秒后重试
            continue  # 继续重试
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}, Retrying...")
            time.sleep(5)

    return None  # 如果重试3次仍失败，返回None。
