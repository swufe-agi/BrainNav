import time
import cv2
import os
import base64
from utill_cos import *
import pyrealsense2 as rs
import numpy as np

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

    # def get_frame(self):
    #     """从已打开的摄像头获取图像"""
    #     if self.cap is None:
    #         print("摄像头未打开")
    #         return None
    #     success, frame = self.cap.read()
    #     if not success:
    #         print("无法获取图像")
    #         return None
    #     return frame

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
        print("图片的访问URL为:", image_url)
        return image_url
    else:
        # print("上传失败")
        return None

# 关闭摄像头（在程序结束时或需要时）
# camera_capture.close_camera()



# 定义获取图像并保存到本地的函数
def get_image_and_save_locally():
    # 获取图像
    frame = camera_capture.get_frame()
    if frame is None:
        return None

    # 创建保存图像的文件夹（如果不存在的话）
    output_folder = "output/image"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 使用时间戳生成唯一的文件名
    file_name = f'rgb_image_{int(time.time())}.jpg'
    file_path = os.path.join(output_folder, file_name)

    # 保存图像到本地
    cv2.imwrite(file_path, frame)

    # print({file_path})

    # 返回本地文件路径
    return file_path