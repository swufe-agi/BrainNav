# API_KEY.py

from dotenv import load_dotenv
import os




# 零一万物大模型开放平台
YI_KEY=013565e5b3154a8cb5f91e7113dbc04a
OPENAI_API_BASE=https://api.lingyiwanwu.com/v1
OPENAI_API_KEY=013565e5b3154a8cb5f91e7113dbc04a

# 百度智能云千帆ModelBuilder
QIANFAN_API_KEY=VtOJDzsN8rk5OsgesGQ4GI5b
QIANFAN_SECRET_KEY=uJKeunrIrb4ZEAvblzILoVIu5mFCUfMa

# 百度智能云千帆AppBuilder-SDK
APPBUILDER_TOKEN=bce-v3/ALTAK-7jr20xkZl4cDmhbQKA4ml/f560e5dc3XXXXXXX059XXXXXXXXX

# 腾讯云的语音合成模型
VOICE_SECRET_ID=AKIDKWau76xiN0Vny67uvjcVYP2Xs8B3tUs2
VOICE_SECRET_KEY=3tZzugNwJXZN0TimcO0QgrtnUyGTXQNQ

# COS 配置
COS_SECRET_ID=AKIDrdUQKJHD3pTxHkASzeSEtPvdRHFMbzIb
COS_SECRET_KEY=Po9PZdns2BHG9sY7fErV6d7e9mS7nLn8
COS_REGION=ap-chengdu
COS_BUCKET_NAME=limo-1324771867



# 加载 .env 文件中的环境变量
load_dotenv()

# 零一万物大模型开放平台：基础指令的大模型
# https://platform.lingyiwanwu.com
YI_KEY = os.getenv('YI_KEY')

# 百度智能云千帆ModelBuilder：用来做语音识别和语音转换的
# https://qianfan.cloud.baidu.com
QIANFAN_API_KEY = os.getenv('QIANFAN_API_KEY')
QIANFAN_SECRET_KEY = os.getenv('QIANFAN_SECRET_KEY')

# 百度智能云千帆AppBuilder-SDK
APPBUILDER_TOKEN = os.getenv('APPBUILDER_TOKEN')

# 腾讯云的语音合成模型
VOICE_SECRET_ID = os.getenv('VOICE_SECRET_ID')
VOICE_SECRET_KEY = os.getenv('VOICE_SECRET_KEY')

# COS 配置
COS_SECRET_ID = os.getenv('COS_SECRET_ID')
COS_SECRET_KEY = os.getenv('COS_SECRET_KEY')
COS_REGION = os.getenv('COS_REGION')
COS_BUCKET_NAME = os.getenv('COS_BUCKET_NAME')

# OpenAI API设置
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
