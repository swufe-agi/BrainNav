import time
import cv2
import os
import base64
import pyrealsense2 as rs
import numpy as np
import sys
import qcloud_cos
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import logging
from API_KEY import *  # 导入你的 COS 配置信息
from pylimo import limo
sys.path.append('/home/agilex/.local/lib/python3.8/site-packages')

limo = limo.LIMO()
limo.EnableCommand()

# 配置COS客户端
config = CosConfig(Region=COS_REGION, SecretId=COS_SECRET_ID, SecretKey=COS_SECRET_KEY)
client = CosS3Client(config)

def upload_image(image_data, object_key):
    """
    上传图像数据到COS，并指定文件夹路径。

    :param image_data: 二进制图像数据。
    :param object_key: 上传后在COS中的对象键（文件名）。
    :return: 上传成功的图片URL或错误信息。
    """
    try:
        # 指定文件夹路径
        object_key = f'llm_api/{object_key}'

        # 直接上传二进制数据
        response = client.put_object(
            Bucket=COS_BUCKET_NAME,
            Body=image_data,
            Key=object_key,
            ContentType='image/jpeg'  # 设定内容类型
        )
        # 构建图片的访问URL
        image_url = f'https://{COS_BUCKET_NAME}.cos.{COS_REGION}.myqcloud.com/{object_key}'
        return image_url

    except Exception as e:
        logging.error(f"上传文件失败: {e}")
        return None


class CameraCapture:
    def __init__(self, cap_num=0):
        self.cap_num = cap_num
        self.cap = None

    def open_camera(self):
        """打开摄像头"""
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.cap_num)
            if not self.cap.isOpened():
                print("无法打开摄像头")
                return None
        return self.cap

    def close_camera(self):
        """释放摄像头"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def get_frame(self):
        """从已打开的摄像头获取图像"""
        if self.cap is None:
            print("摄像头未打开")
            return None

        # 丢弃多余的帧以确保获取最新图像
        for _ in range(5):  # 读取多次丢弃缓存
            self.cap.grab()

        success, frame = self.cap.read()
        if not success:
            print("无法获取图像")
            return None
        return frame

# 初始化摄像头（在程序启动时）
camera_capture = CameraCapture()
cap = camera_capture.open_camera()


# 获取图像的函数
def get_image_and_upload_to_cos():
    # 获取图像
    frame = camera_capture.get_frame()
    if frame is None:
        return None

    # 将图像编码为JPEG格式的二进制数据
    _, buffer = cv2.imencode('.jpg', frame)
    image_data = buffer.tobytes()  # 转换为字节数据

    # 上传图片到腾讯云 COS
    object_key = f'rgb_image_{int(time.time())}.jpg'  # 使用时间戳生成唯一文件名
    image_url = upload_image(image_data, object_key)  # 调用上传函数

    if image_url:
        # print("图片的访问URL为:", image_url)
        return image_url
    else:
        # print("上传失败")
        return None
    

# 定义拍摄四个方向的图片函数
def capture_four_directions():
    image_urls = {}  # 使用字典存储各个方向的图片 URL

    # 向前拍照
    limo.SetMotionCommand(0, 0)  # 直线前进
    time.sleep(2)  # 停留2秒确保拍摄
    image_urls[0] = get_image_and_upload_to_cos()  # 拍照并上传

    # 向右旋转90度
    limo.SetMotionCommand(0, 50)  # 右旋转
    time.sleep(1)  # 增加等待时间，确保旋转完成
    limo.SetMotionCommand(0, -1)
    time.sleep(2)  # 增加等待时间，确保旋转完成

    # 向左拍照
    image_urls[90] = get_image_and_upload_to_cos()  # 拍照并上传
    
    # # 向右旋转90度
    # limo.SetMotionCommand(0, -60)  # 右旋转
    # time.sleep(1)  # 增加等待时间，确保旋转完成
    # limo.SetMotionCommand(0, -1)
    # time.sleep(2)  # 增加等待时间，确保旋转完成

    # # 向后拍照
    # image_urls[180] = get_image_and_upload_to_cos()  # 拍照并上传
    

    # # 向右旋转90度
    # limo.SetMotionCommand(0, -60)  # 右旋转
    # time.sleep(1)  # 增加等待时间，确保旋转完成
    # limo.SetMotionCommand(0, -1)
    # time.sleep(2)  # 增加等待时间，确保旋转完成

    # # 向右拍照
    # image_urls[270] = get_image_and_upload_to_cos()
    

    # #复位
    # limo.SetMotionCommand(0, -60)  # 右旋转
    # time.sleep(1)  # 等待旋转完成
    # limo.SetMotionCommand(0, -1) 
    # time.sleep(1)  # 等待旋转完成

    # return image_urls  # 返回字典


capture_four_directions()