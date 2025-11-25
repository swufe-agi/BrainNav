import sys
import time
from pylimo import limo
from camera import * 
import cv2

sys.path.append('/home/agilex/.local/lib/python3.8/site-packages')

# 创建 LIMO 对象并启用命令
limo = limo.LIMO()
limo.EnableCommand()

# 前进1米的函数
def move_forward():
    limo.SetMotionCommand(1, 0)  # 直线前进
    time.sleep(1)  

# 后退1米的函数
def move_backward():
    limo.SetMotionCommand(0, 60)  # 左旋转
    time.sleep(1)  # 等待旋转完成
    limo.SetMotionCommand(0, 1) 
    time.sleep(1) 
    limo.SetMotionCommand(0, 60)  # 左旋转
    time.sleep(1)  # 等待旋转完成
    limo.SetMotionCommand(0, 1) 
    time.sleep(1) 
    limo.SetMotionCommand(1, 0)  # 后退1米
    time.sleep(1)  

# 左转并前进1米的函数
def turn_left_and_move():
    limo.SetMotionCommand(0, 60)  # 左旋转
    time.sleep(1)  # 等待旋转完成
    limo.SetMotionCommand(0, 1) 
    time.sleep(1)  
    limo.SetMotionCommand(1, 0)  
    time.sleep(1) 

# 右转并前进1米的函数
def turn_right_and_move():
    limo.SetMotionCommand(0, -60)  # 右旋转
    time.sleep(1)  # 等待旋转完成
    limo.SetMotionCommand(0, -1)  
    time.sleep(1)  
    limo.SetMotionCommand(1, 0)  
    time.sleep(1) 


# 控制小车根据 a_t 参数执行不同的动作
def move_car(a_t):
    if a_t == 0:
        move_forward()
    elif a_t == 1:
        turn_right_and_move()
    elif a_t == 2:
        move_backward()
    elif a_t == 3:
        turn_left_and_move()
    else:
        print("未知的命令")

move_car(2)