import sys
import time
from pylimo import limo
from map_camera import * 

def get_user_input():
    # Print welcome message
    print("======================================")
    print("    **Limo Navigation Assistant**     ")
    print("        Welcome to Limo Robot     "   )
    print("======================================")

    # Prompt the user for input
    user_input = input("Hello, I am Limo, glad to assist you! Please enter your navigation command: ")

    # 返回用户输入的指令
    return user_input

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
def move_car(a_t,now_absolute_heading,backtrack_path_coordinates):
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