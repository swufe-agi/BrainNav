import sys
import os
import glob
from camera_directions import *
from agent_prompt_manager import PromptManager
from agent_api import *
import json
from car_actions import *
from command import get_user_input
from nav_log import *

class NavigationAgent:

    def __init__(self, args, prompt_manager=None, log_file='navigation_log.txt'):
        self.args = args
        self.results = []
        self.prompt_manager = prompt_manager
        self.global_viewpoint_id = 5  # 初始化全局 viewpointId 计数器
        self.image_index = 1
        self.log_file = log_file
        self.timer = Timer()

    def write_log(self, message):
        write_to_record_file(message, self.log_file)
    
    
    def _get_image_files(self, folder_path):
        """
        获取指定文件夹中的图像文件
        """
        image_files = glob.glob(os.path.join(folder_path, "*.jpg")) + glob.glob(os.path.join(folder_path, "*.png"))
        return image_files

    def _assign_images_to_candidates(self, obs, image_list):
        """
        为每个候选节点分配对应图片
        """
        for i, candidate in enumerate(obs['candidate']):
            # 假设图片与候选点顺序对应
            if i < len(image_list):
                candidate['image'] = image_list[i]  # 分配图片
            else:
                candidate['image'] = None  # 如果图片不足，留空


    def make_equiv_action(self, a_t, obs, traj=None, t=0):
        """
        根据当前动作更新视点和候选点。
        :param a_t: 当前时间步的动作（整数），而不是列表
        :param obs: 当前的观测状态（字典），会在函数内被直接修改
        :param traj: 当前的轨迹信息（可选）
        :param t: 当前时间步（整数）
        """
        # 执行动作
        move_car(a_t)

        # 确保 obs 是字典
        if isinstance(obs, list):  # 如果 obs 是列表，需要访问其中的字典
            obs = obs[0]  # 取列表中的第一个字典元素

        # 获取当前动作对应的候选点
        action_idx = a_t  # 直接使用 a_t（应该是整数）
        selected_candidate = obs['candidate'][action_idx]  # 获取所选候选点的信息

        # 更新视点到所选候选点
        obs['viewpoint'] = selected_candidate['candidate_viewpoint']
        obs['viewpointId'] = selected_candidate['candidate_viewpointId']

        # 更新候选点信息
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 四个方向
        for i, candidate in enumerate(obs['candidate']):
            dx, dy = directions[i]
            # print("===1===",candidate['candidate_viewpoint'])
            # 更新每个候选点的信息
            candidate['candidate_viewpoint'] = [
                obs['viewpoint'][0] + dx,
                obs['viewpoint'][1] + dy
            ]
            # print("===2===",candidate['candidate_viewpoint'])
            # candidate['absolute_heading'] = (selected_candidate['absolute_heading'] + (i - 1) * 90) % 360
            candidate['candidate_viewpointId'] = self.global_viewpoint_id
            self.global_viewpoint_id += 1  # 更新全局 viewpointId

        # 更新指令 ID
        obs['instr_id'] += 1

        # 打印小车的动作
        print(f"小车执行了动作 {a_t}，移动到 {obs['viewpoint']}, 是 place: {obs['viewpointId']}, 对应 image {obs['viewpointId']}")


    def update_candidate_images(self, obs, t):
        """
        更新候选点的图像信息。
        :param obs: 当前观测状态
        :param t: 当前时间步
        """
        candidate_image_urls = capture_four_directions()  # 调用外部函数拍摄四个方向的图片

        # 为每个候选点分配图像
        for candidate in obs['candidate']:
            # 获取候选点的绝对朝向
            heading = candidate['absolute_heading']
            # heading = str(candidate['absolute_heading'])  # 确保 heading 是字符串类型
            # print(f"Looking for heading {heading}")
    
            # 根据朝向选择对应的图像URL
            image_url = candidate_image_urls.get(heading)
            # print(f"Found image URL: {image_url}")  # 打印出每次获取的结果

            if image_url:
                # 更新候选点的图像信息为URL
                candidate['image'] = image_url
            else:
                # 如果没有找到匹配的图像URL，设置为默认值或None
                candidate['image'] = None
                print(f"Warning: No image found for heading {heading}.")


    
    def rollout(self,instruction):
        """
        主导航逻辑
        """
        # 初始化单视点导航的状态
        obs = {
            'viewpoint': [0, 0],  # 初始视点坐标
            'viewpointId': 0,
            'heading': 0,  # 初始朝向
            'instr_id': 0,  # 指令的唯一标识符
            'instruction': instruction,  #导航指令
            'candidate': [  # 候选点信息
                {
                    'candidate_viewpointId': 1,
                    'candidate_viewpoint': [0, 1],
                    'absolute_heading': 0,
                    'image': None,
                    # 'idx': 1
                },
                {
                    'candidate_viewpointId': 2,
                    'candidate_viewpoint': [1, 0],
                    'absolute_heading': 90,
                    'image': None,
                    # 'idx': 2
                },
                {
                    'candidate_viewpointId': 3,
                    'candidate_viewpoint': [0, -1],
                    'absolute_heading': 180,
                    'image': None,
                    # 'idx': 3
                },
                {
                    'candidate_viewpointId': 4,
                    'candidate_viewpoint': [-1, 0],
                    'absolute_heading': 270,
                    'image': None,
                    # 'idx': 4
                }
            ],
            'history': [],  # 历史记录
            'trajectory': [[0, 0]]  # 当前轨迹初始化为起点
        }

        # 初始化轨迹信息
        traj = {
            'instr_id': obs['instr_id'],  # 当前轨迹对应的指令 ID
            'path': [obs['viewpoint']],  # 路径初始化为起点
            # 'details': {},  # 路径的详细信息
            'a_t': {}  # 记录每个时间步的动作
        }

        self.timer.reset()

        # 检查任务是否已完成
        if traj['instr_id'] in self.results:
            print(f"Task {traj['instr_id']} already completed. Skipping.")
            return None

        # 记录初始的角度信息（朝向）
        previous_angle = obs['heading']

        #传入图片
        # # 加载当前节点图像文件
        # image_folder = r"E:\\VScode\\Map_Limo_Car\\Map_Limo_Car\\images"
        # image_list = self._get_image_files(image_folder)
        # #加载候选节点的图像文件
        # candidate_image_folder = r"E:\\VScode\\Map_Limo_Car\\Map_Limo_Car\\images1"
        # candidate_image_folder_list = self._get_image_files(candidate_image_folder)
        #  # 假设前几张图片对应候选点
        # self._assign_images_to_candidates(obs, candidate_image_folder_list)

        # # 传递当前视点图片
        # self.prompt_manager.node_imgs = [image_list]  # 当前视点图片

        # # 传递候选点图片
        # candidate_images = [candidate['image'] for candidate in obs['candidate']]
        # self.prompt_manager.candidate_imgs = candidate_images  # 候选点图片


        # 主导航循环
        for t in range(self.args.max_action_len):

            # 记录时间
            self.timer.tic('step')

            # 更新候选点图像
            self.update_candidate_images(obs,t)
            # self.update_candidate_images(obs)
            candidate_images = [candidate['image'] for candidate in obs['candidate']]

            # 获取候选行动提示。
            cand_inputs = self.prompt_manager.make_action_prompt(obs,previous_angle)

            #开始构建导航图并记录轨迹
            # cand_inputs = self.prompt_manager.build_navigation_graph(obs)
            if self.args.response_format == 'str':
                # 根据提示生成导航输入（字符串格式）
                nav_input = self.prompt_manager.make_r2r_prompts(cand_inputs=cand_inputs, obs=obs, t=t)
            elif self.args.response_format == 'json':
                # 根据提示生成导航输入（JSON格式）
                nav_input = self.prompt_manager.make_r2r_json_prompts(cand_inputs=cand_inputs, obs=obs, t=t)
            else:
                # 如果响应格式不支持，抛出异常
                raise NotImplementedError("Unsupported response format. Please specify either 'str' or 'json'.")

            # 输出环境提示信息
            # image_list = self.prompt_manager.node_imgs[0]
            image_list = candidate_images

            environment_prompts = nav_input["prompts"]
            print('-------------------- Environment Prompts --------------------')
            print(environment_prompts)

            # 调用 GPT 模型进行推理
            if self.args.llm == 'gpt-4-vision-preview' and self.args.response_format == 'str':
                # GPT-4 Vision 推理，返回字符串输出
                nav_output, tokens = gpt_infer(nav_input["task_description"], environment_prompts, image_list,
                                            self.args.llm, self.args.max_tokens)
                print('-------------------- Output --------------------')
                print(nav_output)
                # print(f"消耗tokens：{tokens}")

                # nav_output = [nav_output]
                a_t = self.prompt_manager.parse_action(nav_output=nav_output,only_options=nav_input["only_options"], t=t)
                self.prompt_manager.parse_planning(nav_output=nav_output)

            elif self.args.llm == 'gpt-4o-2024-05-13' and self.args.response_format == 'json':
                # GPT-4o 推理，返回 JSON 输出
                # if len(image_list) > 20:
                if len(image_list) > 40:
                    a_t = [0]
                    print('Exceed image limit and stop!')
                else:
                    image_index = self.image_index
                    nav_output, tokens = gpt_infer(nav_input["task_description"], environment_prompts, image_list,
                                                self.args.llm,image_index, self.args.max_tokens, response_format={"type": "json_object"})
                    json_output = json.loads(nav_output)
                    image_index +=4
                    print('-------------------- Output --------------------')
                    print(nav_output)
                    a_t = self.prompt_manager.parse_json_action(json_output, nav_input["only_options"], t)
                    self.prompt_manager.parse_json_planning(json_output)
                    # print(f"消耗tokens：{tokens}")

            else:
                raise NotImplemented

            # 更新轨迹中的动作信息
            traj['a_t'][t] = a_t
            print(a_t)

            # 写入日志
            self.write_log(f"时间步 {t}: 动作 {a_t}，视点 {obs['viewpoint']}")
             # 显示进度条
            print_progress(t + 1, self.args.max_action_len, prefix='导航中', suffix='完成', decimals=1)


            # traj['details'].append()

            # print("==================")
            # print(a_t)


            # # 根据动作更新视点和观察状态
            # cpu_a_t = -1 if a_t == 0 else a_t - 1  # 将动作索引从 1 基数调整为 0 基数
            # 检查是否停止动作
            if a_t == 4:
                break
            
            #car run function
            self.make_equiv_action(a_t, obs, traj,t)
            print(obs)
            traj['path'].append(obs['viewpoint'])
            traj['instr_id'] = obs['instr_id']


            # 更新历史记录
            self.prompt_manager.make_history(a_t, nav_input, t)

            # 保存结果到 self.results
            self.results.append(obs['viewpointId'])

            # 记录每步时间
            self.timer.toc('step')
            self.timer.step()

        # 打印总时间统计
        self.timer.show()
        
        return traj



class Args:
    def __init__(self):
        # self.llm = 'gpt-4-vision-preview'
        self.llm = 'gpt-4o-2024-05-13'
        self.max_action_len = 20
        # self.response_format = 'str'
        self.response_format = 'json'
        self.max_tokens = 1000
        # self.stop_after = 8


# 主函数
if __name__ == "__main__":

    args = Args()  # 初始化Args类
    instruction = get_user_input()  

    if not instruction:  # 检查指令是否有效
        print("未获得有效的指令，无法执行导航。")
    else:
        prompt_manager = PromptManager(args)  # 初始化提示管理器
        nav_agent = NavigationAgent(args, prompt_manager=prompt_manager)  # 初始化导航代理

        # 调用导航逻辑并传递指令
        traj = nav_agent.rollout(instruction)  # 传递指令到导航逻辑中

        print("Navigation result:")
        print(traj)  # 输出导航结果
