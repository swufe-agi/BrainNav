from pyorbbecsdk import Pipeline, Config, OBSensorType, OBFormat  # 导入Orrbec SDK中相关的类和模块
import cv2  # OpenCV库，用于处理图像
import numpy as np  # 数组处理库
import time  # 时间处理库，用于时间戳等
import os  # 操作系统相关库，用于文件和路径处理
from utill_cos import upload_image  # 导入自定义的 `upload_image` 函数，用于将图像上传到服务器或云存储

# 常量定义
ESC_KEY = 27  # ESC键的ASCII值，用于退出程序
PRINT_INTERVAL = 1  # 打印信息的时间间隔（单位：秒）
MIN_DEPTH = 20  # 最小深度值（毫米），过滤掉低于此值的深度数据
MAX_DEPTH = 10000  # 最大深度值（毫米），过滤掉高于此值的深度数据

# 创建存放输出图像的目录路径
output_dir = os.path.join(os.path.dirname(__file__), 'output/depth_image')
os.makedirs(output_dir, exist_ok=True)  # 如果输出目录不存在，则创建该目录

class TemporalFilter:
    """
    时间滤波器，用于对深度图像进行时间加权平均处理。
    """
    def __init__(self, alpha):
        self.alpha = alpha  # 滤波器系数，控制当前帧与上一帧的加权比例
        self.previous_frame = None  # 用于存储上一帧的图像数据

    def process(self, frame):
        """
        对当前帧应用时间滤波。如果是第一帧，直接返回；否则，将当前帧与上一帧加权平均后返回。
        """
        if self.previous_frame is None:
            result = frame  # 如果没有上一帧（即第一帧），直接返回当前帧
        else:
            # 对当前帧与上一帧进行加权融合
            result = cv2.addWeighted(frame, self.alpha, self.previous_frame, 1 - self.alpha, 0)
        self.previous_frame = result  # 更新上一帧为当前处理后的帧
        return result

def get_depth_image_url():
    """
    获取深度图像，并将其上传到服务器或云存储，返回图像的URL。
    """
    config = Config()  # 创建配置对象
    pipeline = Pipeline()  # 创建管道对象，用于管理数据流的获取
    temporal_filter = TemporalFilter(alpha=0.5)  # 创建时间滤波器，设置alpha为0.5
    
    # 获取深度传感器的流配置
    profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
    if profile_list is None:
        return None  # 如果获取不到配置文件，返回None
    
    # 获取默认的深度流配置
    depth_profile = profile_list.get_default_video_stream_profile()
    if depth_profile is None:
        return None  # 如果没有找到默认的深度流配置，返回None
    
    config.enable_stream(depth_profile)  # 启用深度流配置
    pipeline.start(config)  # 开始深度流数据传输
    image_url = None  # 初始化图像URL

    while True:
        try:
            # 等待深度帧数据，超时时间为100毫秒
            frames = pipeline.wait_for_frames(100)
            if frames is None:
                continue  # 如果没有获取到帧数据，继续等待
            depth_frame = frames.get_depth_frame()  # 获取深度帧
            if depth_frame is None:
                continue  # 如果深度帧为空，继续等待
            
            # 获取深度图像的宽、高和深度缩放比例
            width = depth_frame.get_width()
            height = depth_frame.get_height()
            scale = depth_frame.get_depth_scale()

            # 将深度数据转换为numpy数组
            depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
            depth_data = depth_data.reshape((height, width))  # 将数据转换为图像的形状

            # 将深度值转换为毫米，并过滤掉不在指定范围内的深度值
            depth_data = depth_data.astype(np.float32) * scale
            depth_data = np.where((depth_data > MIN_DEPTH) & (depth_data < MAX_DEPTH), depth_data, 0)
            depth_data = depth_data.astype(np.uint16)  # 再次将深度数据转换为16位整数

            # 应用时间滤波器，平滑深度数据
            depth_data = temporal_filter.process(depth_data)

            # 将深度图像数据归一化到0-255的范围，并应用伪彩色
            depth_image = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            depth_colored_image = cv2.applyColorMap(depth_image, cv2.COLORMAP_JET)  # 伪彩色映射

            # 保存伪彩色深度图像到本地
            depth_image_filename = os.path.join(output_dir, 'depth_image.jpg')
            cv2.imwrite(depth_image_filename, depth_colored_image)

            # 读取保存的图像并上传到云存储
            with open(depth_image_filename, 'rb') as f:
                image_data = f.read()
                object_key = f'depth_image_{int(time.time())}.jpg'  # 生成唯一的图像名称
                image_url = upload_image(image_data, object_key)  # 调用上传函数，上传图像数据并获取URL
            
            if image_url:
                print("图片的访问URL为:", image_url)  # 打印图像URL
            else:
                print("上传失败")  # 如果上传失败，打印提示
            
            break  # 成功处理后，跳出循环
            
        except KeyboardInterrupt:
            break  # 如果用户按下Ctrl+C终止程序，退出循环

    pipeline.stop()  # 停止数据流
    return image_url  # 返回最终图像的URL

if __name__ == "__main__":
    # 主程序入口，调用get_depth_image_url函数
    image_url = get_depth_image_url()
    if image_url:
        print(image_url)  # 打印图像URL
