import sys
import time
from pylimo import limo
from camera import * 

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
    limo.SetMotionCommand(1, -0.1)  # 直线前进
    time.sleep(1) 

move_forward() 

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

def move_to_backtrack(now_absolute_heading, backtrack_path_coordinates):
    """
    根据当前绝对朝向和回溯路径的坐标计算运动方向，并更新朝向。
    :param now_absolute_heading: 当前绝对朝向（0, 90, 180, 270）
    :param backtrack_path_coordinates: 回溯路径坐标列表，形式如 [[3, 1], [2, 1], [2, 0]]
    """
    """
    1. 根据当前朝向 (now_absolute_heading) 和坐标差值计算运动方向。
    2. 运动规则：
       - backtrack_path_coordinates 的形式如 [[3, 1], [2, 1], [2, 0], ...]。
         前一个坐标减去后一个坐标，得到类似 [1,0], [0,1] 的差值数组。
         遍历这个差值数组，根据朝向和差值确定运动方式。
       - 不同朝向和坐标差值的运动规则：
         - 朝向为 0：
           - x轴：
             +1 ([1,0]): 向左前进，调用 def turn_left_and_move()。
             -1 ([-1,0]): 向右前进，调用 def turn_right_and_move()。
           - y轴：
             +1 ([0,1]): 向后前进，调用 def move_backward()。
             -1 ([0,-1]): 向前前进，调用 def move_forward()。
         - 朝向为 90：
           - x轴：
             +1 ([1,0]): 向后前进，调用 move_backward()。
             -1 ([-1,0]): 向前前进，调用 move_forward()。
           - y轴：
             +1 ([0,1]): 向右前进，调用 turn_right_and_move()。
             -1 ([0,-1]): 向左前进，调用 turn_left_and_move()。
         - 朝向为 180：
           - x轴：
             +1 ([1,0]): 向右前进，调用 turn_right_and_move()。
             -1 ([-1,0]): 向左前进，调用 turn_left_and_move()。
           - y轴：
             +1 ([0,1]): 向前前进，调用 move_forward()。
             -1 ([0,-1]): 向后前进，调用 move_backward()。
         - 朝向为 270：
           - x轴：
             +1 ([1,0]): 向前前进，调用 move_forward()。
             -1 ([-1,0]): 向后前进，调用 move_backward()。
           - y轴：
             +1 ([0,1]): 向左前进，调用 turn_left_and_move()。
             -1 ([0,-1]): 向右前进，调用 turn_right_and_move()。
    3. 更新当前的绝对朝向 (now_absolute_heading)，每次坐标差值计算后更新朝向：
       - 更新规则：
         - 向左前进： (now_absolute_heading + 270) % 360
         - 向右前进： (now_absolute_heading + 90) % 360
         - 向前前进： (now_absolute_heading + 0) % 360
         - 向后前进： (now_absolute_heading + 180) % 360
    """
    print(f"开始回溯，当前绝对朝向: {now_absolute_heading}")
    for i in range(len(backtrack_path_coordinates) - 1):
        # 获取当前坐标和下一个坐标
        current_coord = backtrack_path_coordinates[i]
        next_coord = backtrack_path_coordinates[i + 1]
        
        # 计算坐标差值
        diff = [current_coord[0] - next_coord[0], current_coord[1] - next_coord[1]]
        print(f"当前坐标: {current_coord}, 下一个坐标: {next_coord}, 坐标差值: {diff}")

        # 根据当前绝对朝向和坐标差值决定运动
        if now_absolute_heading == 0:
            if diff == [1, 0]:  # x轴+1
                turn_left_and_move()
                now_absolute_heading = (now_absolute_heading + 270) % 360
            elif diff == [-1, 0]:  # x轴-1
                turn_right_and_move()
                now_absolute_heading = (now_absolute_heading + 90) % 360
            elif diff == [0, 1]:  # y轴+1
                move_backward()
                now_absolute_heading = (now_absolute_heading + 180) % 360
            elif diff == [0, -1]:  # y轴-1
                move_forward()
                now_absolute_heading = (now_absolute_heading + 0) % 360

        elif now_absolute_heading == 90:
            if diff == [1, 0]:  # x轴+1
                move_backward()
                now_absolute_heading = (now_absolute_heading + 180) % 360
            elif diff == [-1, 0]:  # x轴-1
                move_forward()
                now_absolute_heading = (now_absolute_heading + 0) % 360
            elif diff == [0, 1]:  # y轴+1
                turn_right_and_move()
                now_absolute_heading = (now_absolute_heading + 90) % 360
            elif diff == [0, -1]:  # y轴-1
                turn_left_and_move()
                now_absolute_heading = (now_absolute_heading + 270) % 360

        elif now_absolute_heading == 180:
            if diff == [1, 0]:  # x轴+1
                turn_right_and_move()
                now_absolute_heading = (now_absolute_heading + 90) % 360
            elif diff == [-1, 0]:  # x轴-1
                turn_left_and_move()
                now_absolute_heading = (now_absolute_heading + 270) % 360
            elif diff == [0, 1]:  # y轴+1
                move_forward()
                now_absolute_heading = (now_absolute_heading + 0) % 360
            elif diff == [0, -1]:  # y轴-1
                move_backward()
                now_absolute_heading = (now_absolute_heading + 180) % 360

        elif now_absolute_heading == 270:
            if diff == [1, 0]:  # x轴+1
                move_forward()
                now_absolute_heading = (now_absolute_heading + 0) % 360
            elif diff == [-1, 0]:  # x轴-1
                move_backward()
                now_absolute_heading = (now_absolute_heading + 180) % 360
            elif diff == [0, 1]:  # y轴+1
                turn_left_and_move()
                now_absolute_heading = (now_absolute_heading + 270) % 360
            elif diff == [0, -1]:  # y轴-1
                turn_right_and_move()
                now_absolute_heading = (now_absolute_heading + 90) % 360

        else:
            print(f"未知的绝对朝向: {now_absolute_heading}")
            break

        print(f"更新后的绝对朝向: {now_absolute_heading}")

    print("回溯路径执行完毕。")


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
    elif a_t == 5: 
        move_to_backtrack(now_absolute_heading,backtrack_path_coordinates)   
    else:
        print("未知的命令")