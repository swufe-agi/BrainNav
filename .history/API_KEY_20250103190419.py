# API_KEY.py
from dotenv import load_dotenv
import os

# 加载 .env 文件中的环境变量
load_dotenv()

# COS 配置
COS_SECRET_ID = os.getenv('COS_SECRET_ID')
COS_SECRET_KEY = os.getenv('COS_SECRET_KEY')
COS_REGION = os.getenv('COS_REGION')
COS_BUCKET_NAME = os.getenv('COS_BUCKET_NAME')

# OpenAI API设置
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
