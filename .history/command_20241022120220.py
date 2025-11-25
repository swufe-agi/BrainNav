from voice_recognition import *
from utils_llm import *
from utils_tts import *


def command_selection():
    '''
    指令选择函数，负责根据用户输入的选择执行相应的操作
    '''
    suppress_stderr()
    
    text_to_speech = "您好，我是Limo,很高兴为您服务。输入1为文本控制运动，2为语音控制运动，3为语音智能问答。"
    generate_and_play_audio(text_to_speech)

    # 获取用户输入
    choice = input("请输入1选择文本控制运动，2选择语音控制运动，3选择语音智能问答：")

    order = None  # 初始化 order 变量

    if choice == "1":
        # 文本控制运动模式
        text_to_speech = "您已选择文本控制运动，请输入运动指令。"
        generate_and_play_audio(text_to_speech)
        order = input("请输入运动指令：")
        print(f"文本输入的指令：{order}")

    elif choice == "2":
        # 语音控制运动模式
        text_to_speech = "您已选择语音控制运动，请开始说话。"
        generate_and_play_audio(text_to_speech)

        # 调用录音函数并进行语音识别
        record()
        order = recognize_speech(WAVE_OUTPUT_FILENAME)

        if order:
            print(f"语音识别的指令：{order}")
        else:
            generate_and_play_audio("未能识别语音，请重试。")
            order = None  # 确保语音识别失败时返回空值

    elif choice == "3":
        # 调用语音问答模式
        agent_voice_mode()
        order = None  # 语音问答模式不返回运动指令

    else:
        # 无效输入处理
        text_to_speech = "无效的输入，请输入1、2或3。"
        generate_and_play_audio(text_to_speech)
        print("无效的输入，请输入1、2或3。")
        order = None  # 无效输入也不返回指令

    return order
