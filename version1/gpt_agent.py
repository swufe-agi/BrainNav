import sys
import numpy as np
from collections import defaultdict
import json
import os
import glob
from one_stage_prompt_manager1 import OneStagePromptManager
from api import *
from camera_directions import *

class NavigationAgent:
    # 定义环境动作字典：包括左、右、上、下、前进等动作
    env_actions = {
        'left': (0, -1, 0),  # 向左
        'right': (0, 1, 0),  # 向右
        'up': (0, 0, 1),  # 向上
        'down': (0, 0, -1),  # 向下
        'forward': (1, 0, 0),  # 向前
        '<end>': (0, 0, 0),  # 结束动作
        '<start>': (0, 0, 0),  # 开始动作
        '<ignore>': (0, 0, 0)  # 忽略动作
    }

    # 将所有动作都转化为对应的坐标表示
    for k, v in env_actions.items():
        env_actions[k] = [[vx] for vx in v]

    def __init__(self, args, rank=0, prompt_manager=None):
        self.args = args
        self.rank = rank
        self.results = {}
        self.viewpoint_map = self.create_viewpoint_map()  # 添加视点映射

        self.prompt_manager = prompt_manager
        sys.stdout.flush()
        self.logs = defaultdict(list)

    def create_viewpoint_map(self):
        """
        创建一个简单的视点映射。这里使用固定的示例坐标。
        你可以根据实际情况修改此方法。
        """
        viewpoint_map = {
            0: [0, 0, 0],  # 示例：视点 0 对应坐标 (0, 0, 0)
            1: [1, 0, 0],  # 示例：视点 1 对应坐标 (1, 0, 0)
            2: [1, 1, 0],  # 示例：视点 2 对应坐标 (1, 1, 0)
            3: [0, 1, 0],  # 示例：视点 3 对应坐标 (0, 1, 0)
            4: [2, 0, 0],  # 示例：视点 4 对应坐标 (2, 0, 0)
            # 更多视点坐标...
        }
        return viewpoint_map

    def _get_image_files(self, folder_path):
        image_files = glob.glob(os.path.join(folder_path, "*.jpg")) + glob.glob(os.path.join(folder_path, "*.png"))
        return image_files

    def make_equiv_action(self, a_t, obs, traj=None):
        """
        更新每次行动后的视点和目标点。
        """
        for i in range(len(obs)):
            # 当前观察的视点
            current_viewpoint = obs[i]['viewpoint']
            current_viewIndex = obs[i]['viewIndex']

            # 更新视点位置以及目标点
            if a_t[i] != -1:  # 如果不是停止
                next_viewIndex = self.get_next_viewpoint(current_viewpoint, a_t[i])  # 获取下一个视点
                obs[i]['viewIndex'] = next_viewIndex  # 更新视点
                obs[i]['viewpoint'] = self.get_viewpoint_coordinates(next_viewIndex)  # 更新视点坐标
                print(f"Updated viewIndex: {obs[i]['viewIndex']}")  # 输出调试信息

            # 更新轨迹
            if traj is not None:
                traj[i]['path'].append(obs[i]['viewpoint'])  # 添加新的视点到轨迹

        return obs

    def get_next_viewpoint(self, current_viewpoint, action):
        """
        根据动作更新视点编号。
        例如：简单地根据动作值增加或减少视点编号。
        """
        action_map = {
            'left': (0, -1),
            'right': (0, 1),
            'up': (0, 1),
            'down': (0, -1),
            'forward': (1, 0),
            '<end>': (0, 0),
            '<start>': (0, 0),
            '<ignore>': (0, 0)
        }

        action_tuple = action_map.get(action, (0, 0))
        # 更新视点（这里假设更新视点编号的简单规则）
        new_viewpoint = [current_viewpoint[0] + action_tuple[0], current_viewpoint[1] + action_tuple[1]]
        return new_viewpoint

    def get_viewpoint_coordinates(self, viewIndex):
        """
        获取视点坐标，确保 viewIndex 是可哈希的。
        """
        # 确保 viewIndex 是一个整数类型，如果它是一个列表或其他类型，处理它
        if isinstance(viewIndex, list):
            # 如果 viewIndex 是一个列表，使用某种规则将其转换为单一的标识符（例如，使用列表长度作为索引）
            viewIndex = len(viewIndex)  # 或者其他转换规则
        elif not isinstance(viewIndex, int):
            raise ValueError(f"viewIndex must be an integer or a list, got {type(viewIndex)}")

        # 获取 viewIndex 对应的坐标
        coordinates = self.viewpoint_map.get(viewIndex, [0, 0, 0])  # 默认坐标
        return coordinates


    def rollout(self, reset=False):
        # 初始化观察环境的状态，包括位置、方向、指令和历史信息等
        obs = [{
            'viewpoint': [0, 0],  # 初始视点坐标
            'heading': 0,  # 初始朝向
            'elevation': 0,  # 初始高度
            'instr_id': 0,  # 指令的唯一标识符
            'instruction': "Go forward toward the windows.",  # 导航指令
            'candidate': [{  # 候选点信息
                'viewpointId': 1,  # 候选点的 ID
                'pointId': 1,  # 点的编号
                'absolute_heading': 90,  # 绝对朝向
                'absolute_elevation': 0,  # 绝对高度
                'image': None,  # 图像数据
                'idx': 0  # 索引
            }],
            'history': [],  # 历史记录
            'trajectory': [0],  # 当前轨迹
            'viewIndex': 0  # 当前视图索引
        }]

        # 获取批量大小
        batch_size = len(obs)

        # 初始化轨迹信息，包括路径、细节和动作信息
        traj = [{
            'instr_id': ob['instr_id'],  # 当前轨迹对应的指令 ID
            'path': [[ob['viewpoint']]],  # 路径初始化为起点
            'details': {},  # 路径的详细信息
            'a_t': {},  # 记录每个时间步的动作
        } for ob in obs]

        # 检查任务是否已完成
        if traj[0]['instr_id'] in self.results:
            print(f"Task {traj[0]['instr_id']} already completed. Skipping.")
            return [None]

        # 初始化导航的结束状态和动作状态
        ended = np.array([False] * batch_size)  # 标记导航是否已结束
        just_ended = np.array([False] * batch_size)  # 标记是否刚结束

        # 记录初始的角度信息（朝向和高度）
        previous_angle = [{'heading': ob['heading'], 'elevation': ob['elevation']} for ob in obs]

        # 初始化提示管理器的相关状态
        self.prompt_manager.history = ['' for _ in range(self.args.batch_size)]  # 历史记录
        self.prompt_manager.nodes_list = [[] for _ in range(self.args.batch_size)]  # 节点列表
        self.prompt_manager.node_imgs = [[] for _ in range(self.args.batch_size)]  # 节点对应的图像
        self.prompt_manager.graph = [{} for _ in range(self.args.batch_size)]  # 地图的图表示
        self.prompt_manager.trajectory = [[] for _ in range(self.args.batch_size)]  # 导航轨迹
        self.prompt_manager.planning = [["Navigation has just started, with no planning yet."] for _ in range(self.args.batch_size)]

        # 获取当前节点对应的图像列表
        image_folder = r"E:\VScode\Map_Limo_Car\Map_Limo_Car\images"
        image_list = self._get_image_files(image_folder)
        self.prompt_manager.node_imgs[0] = image_list #只更新第一个任务的数据，保留其他任务或批次的独立性。0是批次，因为批处理了

        # 导航循环，执行一系列时间步动作
        for t in range(self.args.max_action_len):
            if t == self.args.max_action_len:
                break

            # 获取候选行动的提示
            cand_inputs = self.prompt_manager.make_action_prompt(obs, previous_angle)#返回的是： 'cand_vpids' # 候选视点ID。'cand_index': # 候选视点索引'action_prompts':# 动作提示：action_text = direction + f" to Place {node_index} which is corresponding to Image {node_index}"
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
            image_list = self.prompt_manager.node_imgs[0]
            environment_prompts = nav_input["prompts"][0]
            print('-------------------- Environment Prompts --------------------')
            print(environment_prompts)

            # 调用 GPT 模型进行推理
            if self.args.llm == 'gpt-4-vision-preview' and self.args.response_format == 'str':
                # GPT-4 Vision 推理，返回字符串输出
                nav_output, tokens = gpt_infer(nav_input["task_description"], environment_prompts, image_list,
                                            self.args.llm, self.args.max_tokens)
                print('-------------------- Output --------------------')
                print(nav_output)
                nav_output = [nav_output]
                a_t = self.prompt_manager.parse_action(nav_output=nav_output,
                                                    only_options_batch=nav_input["only_options"],
                                                    t=t)
                self.prompt_manager.parse_planning(nav_output=nav_output)

            elif self.args.llm == 'gpt-4o-2024-05-13' and self.args.response_format == 'json':
                # GPT-4o 推理，返回 JSON 输出
                if len(image_list) > 20:
                    a_t = [0]
                    print('Exceed image limit and stop!')
                else:
                    nav_output, tokens = gpt_infer(nav_input["task_description"], environment_prompts, image_list,
                                                self.args.llm, self.args.max_tokens, response_format={"type": "json_object"})
                    json_output = json.loads(nav_output)
                    a_t = self.prompt_manager.parse_json_action(json_output, nav_input["only_options"], t)
                    self.prompt_manager.parse_json_planning(json_output)
                    print('-------------------- Output --------------------')
                    print(nav_output)

            else:
                raise NotImplemented

            # 更新轨迹中的动作信息
            for i in range(batch_size):
                traj[i]['a_t'][t] = a_t[i]

            # 检查是否停止动作
            a_t_stop = [a_t_i == 0 for a_t_i in a_t]

            # 初始化 CPU 级别的动作
            cpu_a_t = []
            for i in range(batch_size):
                if a_t_stop[i] or ended[i]:
                    cpu_a_t.append(-1)  # 停止的标记
                    just_ended[i] = True
                else:
                    cpu_a_t.append(a_t[i] - 1)  # 将动作索引从 1 基数调整为 0 基数

            # 根据动作更新视点和观察状态
            self.make_equiv_action(cpu_a_t, obs, traj)

            # 更新 previous_angle
            previous_angle = [{'heading': ob['heading'], 'elevation': ob['elevation']} for ob in obs]

            # 检查是否停止导航
            if a_t[0] == 0:
                break

            # 更新历史记录
            self.prompt_manager.make_history(a_t, nav_input, t)

        # 保存结果到 self.results
        self.results[traj[0]['instr_id']] = traj
        return traj

class Args:
    def __init__(self):
        self.llm = 'gpt-4-vision-preview'
        # self.llm = 'gpt-4o-2024-05-13'
        self.batch_size = 1
        self.max_action_len = 10
        self.response_format = 'str'
        # self.response_format = 'json'
        self.max_tokens = 600
        self.rank = 0
        self.stop_after = 4

# 主函数
if __name__ == "__main__":

    args = Args()

    prompt_manager = OneStagePromptManager(args)

    nav_agent = NavigationAgent(args, rank=args.rank, prompt_manager=prompt_manager)

    traj = nav_agent.rollout()

    print("Navigation result:")
    print(traj)