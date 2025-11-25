
print('导入大模型API模块')
from API_KEY import *
import openai

def llm_yi(PROMPT):
    '''
    零一万物大模型API
    '''

    API_BASE = "https://api.lingyiwanwu.com/v1"
    API_KEY = YI_KEY

    MODEL = 'yi-large'

    # 设置 API Key 和 Base URL
    openai.api_key = API_KEY
    openai.api_base = API_BASE

    # 调用 ChatCompletion 接口
    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role": "user", "content": PROMPT}]
        )
        # 获取并返回结果
        result = response.choices[0].message['content'].strip()
        return result
    except Exception as e:
        print(f"调用 API 时发生错误: {e}")
        return None
    

def test_llm_yi():
    # 模拟用户提问
    order = "今天星期几"

    # 调用大语言模型 API 获取回答
    result = llm_yi(order)
    print(result)

# 测试函数
test_llm_yi()