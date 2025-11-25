import sys
import time
from pylimo import limo
from camera import * 
import cv2
sys.path.append('/home/agilex/.local/lib/python3.8/site-packages')

limo = limo.LIMO()
limo.EnableCommand()


# 定义拍摄四个方向的图片函数
def capture_four_directions():
    image_urls = {}  # 使用字典存储各个方向的图片 URL

    # 向前拍照
    limo.SetMotionCommand(0, 0)  # 直线前进
    time.sleep(2)  # 停留2秒确保拍摄
    image_urls[0] = get_image_and_upload_to_cos()  # 拍照并上传
    # image_urls[0] = get_image_and_save_locally()  #保存在本地

    # 向右旋转90度
    limo.SetMotionCommand(0, 60)  # 右旋转
    time.sleep(1)  # 增加等待时间，确保旋转完成
    limo.SetMotionCommand(0, 1)
    time.sleep(2)  # 增加等待时间，确保旋转完成

    # 向左拍照
    image_urls[90] = get_image_and_upload_to_cos()  # 拍照并上传
    # image_urls[90] = get_image_and_save_locally()  #保存在本地

    # 向右旋转90度
    limo.SetMotionCommand(0, 60)  # 右旋转
    time.sleep(1)  # 增加等待时间，确保旋转完成
    limo.SetMotionCommand(0, 1)
    time.sleep(2)  # 增加等待时间，确保旋转完成

    # 向后拍照
    image_urls[180] = get_image_and_upload_to_cos()  # 拍照并上传
    # image_urls[180] = get_image_and_save_locally()  #保存在本地

    # 向右旋转90度
    limo.SetMotionCommand(0, 60)  # 右旋转
    time.sleep(1)  # 增加等待时间，确保旋转完成
    limo.SetMotionCommand(0, 1)
    time.sleep(2)  # 增加等待时间，确保旋转完成

    # 向右拍照
    image_urls[270] = get_image_and_upload_to_cos()
    # image_urls[270] = get_image_and_save_locally()    #保存在本地

    #复位
    limo.SetMotionCommand(0, 60)  # 右旋转
    time.sleep(1)  # 等待旋转完成
    limo.SetMotionCommand(0, 1) 
    time.sleep(1)  # 等待旋转完成

    # for absolute_heading, image in image_urls.items():
    #     print(f" {absolute_heading}: {image}")

    return image_urls  # 返回字典


image_urls =capture_four_directions()