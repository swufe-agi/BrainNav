# from local_server import *
from camera import *  # 导入camera.py中的所有函数
# from voice_recognition import *  # 导入voice_recognition.py中的所有函数
#from utils_llmPrompts import *  # 导入nlp_processing.py中的所有函数
from  utils_mllm import *  # 导入multimodal_processing.py中的所有函数
from utils_llm import *
from utils_tts import *
#from get_distences import *
#from get_image import *
import time  # 导入time模块用于添加延时
# 导入小车的包
import sys
from utils_llmPrompts import agent_plan
sys.path.append('/home/agilex/.local/lib/python3.8/site-packages')
from pylimo import limo
from voice_recognition import *
from depth_camera import *
from command import*

def agent_play():
    '''
    主函数，控制智能体编排动作
    '''
    order = command_selection()

    while True:

        # 1、普通相机开启与rgb图片放到服务器获取URL
        rgb_image_url = get_image_and_upload_to_cos() 
        print("rgb图片地址：" + rgb_image_url)
        # 2、深度相机开启与图片放到服务器获取URL
        depth_image_url = load_depth_camera()
        print("深度图片地址：" + depth_image_url)
        # 只查看图片信息的调试
        info = call_mllm_for_images(rgb_image_url,depth_image_url,order)
        print(info)
        # break

        # 智能体Agent编排动作。多模态大模型
        agent_plan_output = eval(call_mllm_to_actions(rgb_image_url,depth_image_url,order))

        # 智能体Agent编排动作。普通大模型
        # agent_plan_output = eval(agent_plan(order))

        print('智能体编排动作如下\n', agent_plan_output)
        
        break

        # 执行智能体编排的每个函数
        for each in agent_plan_output['function']:  # 运行智能体规划编排的每个函数
            try:
                print('开始执行动作:', each)
                eval(each)  # 执行每个函数
                # time.sleep(0.5)  # 每个任务之间添加0.5秒的缓冲时间
            except Exception as e:
                print(f'执行动作 {each} 时发生错误: {e}')
        #brake()  # 每次分析完，小车必须停止

        plan_ok = input('动作执行完成，是否继续？按c继续输入新指令，按q退出\n')
        if plan_ok == 'q':
            print('程序退出')
            break
        elif plan_ok == 'c':
            print('继续执行')
            continue
        else:
            print('无效输入，程序结束')
            break

# agent_play()
if __name__ == '__main__':
    # 小车初始化
    limo = limo.LIMO()
    limo.EnableCommand()  # 使能控制
    agent_play()

    
