import re
import math

class PromptManager(object):
    # 初始化 OneStagePromptManager 类，配置与内部状态
    def __init__(self, args):
        self.args = args  # 接受参数并存储，通常包括 batch_size 等配置项
        self.history  = ''  # 用于存储历史记录
        self.nodes_list = []  # 用于存储节点列表
        self.candidate_images = [] #用于存储候选节点的图片
        self.node_imgs = []  # 用于存储当前节点对应图像
        self.graph  = {}  # 存储每个batch的图（用字典表示节点和连接）
        self.trajectory = []   # 用于存储每个batch的轨迹
        self.planning = [["Navigation has just started, with no planning yet."]] # 初始化导航规划状态

        # 根据相对方向和高度生成动作概念（动作文本）
    def get_action_concept(self, rel_heading): 
        if rel_heading == 0:
            action_text = 'go forward'  # 向前
        elif rel_heading == 90:
            action_text = 'turn right'  # 向右转
        elif rel_heading == 270:
            action_text = 'turn left'  # 向左转
        elif rel_heading == 180:
            action_text = 'turn around'  # 180度转向（掉头）
        else:
            action_text = 'invalid heading'  # 如果角度不在规定范围内，返回无效值

        return action_text  # 返回动作文本



    def make_action_prompt(self, obs, previous_angle):
        """
        生成动作提示，包含候选视点的动作选项。
        """
        # 初始化存储变量
        nodes_list, graph, trajectory, candidate_images = self.nodes_list, self.graph, self.trajectory, self.candidate_images

        cand_vpids = []  # 候选视点ID
        # cand_index = []  # 候选视点索引
        action_prompts = []  # 存储当前动作提示

        # 如果当前视点不在节点列表中，则将其添加进去
        if obs['viewpointId'] not in nodes_list:
            nodes_list.append(obs['viewpointId'])
            # node_imgs.append(None)  # 还未加载图像，设为None

        # 更新轨迹，记录当前视点
        trajectory.append(obs['viewpointId'])

        # 遍历候选视点并生成对应的动作提示
        for cc in obs['candidate']:
            cand_vpids.append(cc['candidate_viewpointId'])  # 添加候选视点ID
            # cand_index.append(cc['idx'])  # 添加候选视点索引

            # 根据航向和高度生成动作概念
            direction = self.get_action_concept(cc['absolute_heading'] - previous_angle)

            # 如果候选视点不在节点列表中，则添加，并存储图像
            if cc['candidate_viewpointId'] not in nodes_list:
                nodes_list.append(cc['candidate_viewpointId'])
                # 确保imgs 列表的长度足够
                node_index = len(nodes_list) - 1  # 通过添加节点，确定该节点的索引
                candidate_images.append(cc['image'])  # 添加图像
            else:
                node_index = nodes_list.index(cc['candidate_viewpointId'])
                # 确保imgs 列表的长度足够，若不足则扩展
                if node_index >= len(candidate_images):
                    candidate_images.append(cc['image'])
                else:
                    candidate_images[node_index] = cc['image']  # 更新节点图像

            # 生成动作提示文本
            action_text = direction + f" to Place {node_index} which is corresponding to Image {node_index}"
            action_prompts.append(action_text)

            #加入停止操作
        stop_text =f"The goal is right ahead, I stop."
        action_prompts.append(stop_text)

        # 更新候选视点ID、索引和动作提示
        # batch_cand_index = cand_index
        batch_cand_vpids = cand_vpids
        batch_action_prompts = action_prompts

        # 更新图，将当前视点与候选视点ID连接
        if not isinstance(graph, dict):
            graph = {}  # 确保是字典

        if obs['viewpointId'] not in graph:
            graph[obs['viewpointId']] = cand_vpids

        return {
            'cand_vpids': batch_cand_vpids,  # 候选视点ID
            # 'cand_index': batch_cand_index,  # 候选视点索引
            'action_prompts': batch_action_prompts,  # 动作提示
        }


    def make_action_options(self, cand_inputs, t):
        """
        根据候选输入生成带字母标签的动作选项
        """
        # 初始化变量
        action_options = []  # 存储完整的动作选项
        only_options = []  # 存储动作选项的标签（例如A, B, C等）
        
        action_prompts = cand_inputs["action_prompts"]  # 从 cand_inputs 中获取的动作提示集合
        # print(action_prompts)

        # # 如果定义了stop_after，并且t大于或等于该值，则在动作选项中加入"stop"动作
        # if self.args.stop_after and t >= self.args.stop_after:
        #     action_prompts = ['stop'] + action_prompts

        # 生成完整的动作选项（带字母标签）和仅包含选项字母的列表
        full_action_options = [chr(j + 65) + '. ' + action_prompts[j] for j in range(len(action_prompts))]
        only_options = [chr(j + 65) for j in range(len(action_prompts))]
        
        action_options.append(full_action_options)
        only_options.append(only_options)

        return action_options, only_options  # 返回完整选项和标签


    def build_navigation_graph(self, obs):
        """
        构建导航图并记录轨迹，同时返回候选ID和候选索引。
        """
        nodes_list, graph, trajectory = self.nodes_list, self.graph, self.trajectory

        candidate_ids = []  # 候选视点的ID
        candidate_indices = []  # 候选视点的索引

        # 如果当前视点不在节点列表中，则将其添加
        if obs['viewpointId'] not in nodes_list:
            nodes_list.append(obs['viewpointId'])

        # 更新轨迹
        trajectory.append(obs['viewpointId'])

        # 遍历候选节点，构建导航图
        for candidate in obs['candidate']:
            # 记录候选ID和索引
            candidate_ids.append(candidate['viewpointId'])
            candidate_indices.append(candidate['idx'])

            # 如果候选视点不在节点列表中，则添加
            if candidate['viewpointId'] not in nodes_list:
                nodes_list.append(candidate['viewpointId'])

            # 更新导航图
            current_viewpoint = tuple(obs['viewpoint'])
            graph.setdefault(current_viewpoint, []).append(candidate['viewpointId'])

        return {
            'cand_vpids': candidate_ids,
            'cand_indices': candidate_indices
        }

    def make_map_prompt(self):
        """
        基于单视点生成地图提示。
        :return: 轨迹文本、图的连接信息、补充地图信息
        """
        trajectory = self.trajectory
        nodes_list = self.nodes_list
        graph = self.graph

        no_dup_nodes = []  # 去重的节点列表
        trajectory_text = "Place " + " ".join(str(nodes_list.index(node)) for node in trajectory)

        graph_text = ""
        for node in trajectory:
            node_index = nodes_list.index(node)
            if node not in no_dup_nodes:
                no_dup_nodes.append(node)

                adj_nodes = graph.get(tuple(node) if isinstance(node, (list, tuple)) else node, [])
                adj_text = ", ".join(str(nodes_list.index(adj)) for adj in adj_nodes)
                graph_text += f"\nPlace {node_index} is connected with Places {adj_text}"

        # 处理未访问且不直接连接的节点（补充信息）
        graph_supp_text = ""
        current_node = trajectory[-1]  # 当前节点
        connected_nodes = graph.get(current_node, [])  # 当前节点的邻居

        for node_index, node in enumerate(nodes_list):
            node_key = tuple(node) if isinstance(node, (list, tuple)) else node
            if node not in trajectory and node_key not in connected_nodes:
                graph_supp_text += f"\nPlace {node_index}, which is corresponding to Image {node_index}"

        if not graph_supp_text:
            graph_supp_text = "Nothing yet."

        return trajectory_text, graph_text, graph_supp_text
     

    def make_r2r_prompts(self, obs, cand_inputs, t):
        """
        基于当前观测数据和候选点信息生成导航提示。
        :param obs: 当前观测数据
        :param cand_inputs: 候选点的ID和索引信息
        :param t: 当前时间步
        :return: 导航输入字典
        """
        # 背景信息：描述机器人在现实世界中的导航任务
        background = """You are an embodied robot that navigates in the real world."""
        # background_supp = """You need to explore between some places marked with IDs and ultimately find the destination to stop.""" \
        #                 """ At each step, a series of images corresponding to the places you have explored and have observed will be provided to you."""
        background_supp = """You need to explore between locations marked with IDs, eventually finding the target location and stopping there.
                   At each step, you will receive images of the four candidate nodes (front, back, left, right) of your current node, showcasing the explored and observed locations.Provide a detailed description of what is in each image."""

        # 任务描述：
        # 'Instruction'：全球性的、逐步的指令，可能有些命令已经执行过，机器人需要识别哪些未执行的命令。
        instr_des = """'Instruction' is a global, step-by-step detailed guidance, but you might have already executed some of the commands. You need to carefully discern the commands that have not been executed yet."""
        # 'Trajectory'：记录机器人已探索的地点ID，从Place 0开始。
        traj_info = """'Trajectory' represents the ID info of the places you have explored. You start navigating from Place 0."""
        # 'Map'：记录已探索地点与其他观察到的地方的连接关系。
        map_info = """'Map' refers to the connectivity between the places you have explored and other places you have observed."""
        # 'Supplementary Info'：记录曾经观察过的地点及其图像，这些地点尚未访问，只有在出现导航错误时才会考虑。
        map_supp = """'Supplementary Info' records some places and their corresponding images you have ever seen but have not yet visited. These places are only considered when there is a navigation error, and you decide to backtrack for further exploration."""
        # 'History'：表示历史上已探索的地方及其图像，可能包含正确的地标或之前错误的探索。
        history = """'History' represents the places you have explored in previous steps along with their corresponding images. It may include the correct landmarks mentioned in the 'Instruction' as well as some past erroneous explorations."""
        # 'Action options'：当前步骤可采取的动作选项。
        option = """'Action options' are some actions that you can take at this step."""
        # 'Previous Planning'：记录之前的多步计划信息，当前可以参考。
        pre_planning = """'Previous Planning' records previous long-term multi-step planning info that you can refer to now."""

        # 任务要求：
        # 结合图片、指令、历史、地图等信息进行决策
        # requirement = """For each provided image of the places, you should combine the 'Instruction' and carefully examine the relevant information, such as scene descriptions, landmarks, and objects. You need to align 'Instruction' with 'History' (including corresponding images) to estimate your instruction execution progress and refer to 'Map' for path planning. Check the Place IDs in the 'History' and 'Trajectory', avoiding repeated exploration that leads to getting stuck in a loop, unless it is necessary to backtrack to a specific place."""
        requirement = """For the four candidate node images, you should carefully examine the relevant information from the 'instruction',
                such as scene descriptions, landmarks, and objects. You need to align the 'instruction' with the 'history' (including corresponding images),
                to assess the progress of the instruction and use the 'map' for path planning.
                Check the location IDs in the 'history' and 'trajectory' to avoid redundant exploration that may lead to cycles,
                unless it is necessary to backtrack to a specific location."""
        # 如果已经看到目标，估计与目标之间的距离。如果距离较远，继续前进并尝试在1米内停止。
        dist_require = """If you can already see the destination, estimate the distance between you and it. If the distance is far, continue moving and try to stop within 1 meter of the destination."""
        # 'Thought'：生成机器人思考的JSON格式答案，必须包括'Thought'、'New Planning'和'Action'三个字段。
        thought = """Your answer should be JSON format and must include three fields: 'Thought', 'New Planning', and 'Action'. You need to combine 'Instruction', 'Trajectory', 'Map', 'Supplementary Info', your past 'History', 'Previous Planning', 'Action options', and the provided images to think about what to do next and why, and complete your thinking into 'Thought'.Provide a detailed description of what is in each image in the 'Thought' field."""
        # 'New Planning'：基于当前的'History'、'Map'和'Previous Planning'，更新新的多步路径规划。
        new_planning = """Based on your 'Map', 'Previous Planning' and current 'Thought', you also need to update your new multi-step path planning to 'New Planning'."""
        # 'Action'：输出最终选定的动作选项，必须只包含一个字母（如"Action: A"）。
        action = """At the end of your output, you must provide a single capital letter in the 'Action options' that corresponds to the action you have decided to take, and place only the letter into 'Action', such as "Action: A" or "Action: B".Your every action choice must be based on image information, historical data, and other relevant factors, and cannot be made randomly."""
        # action = """At the end of your output, you must choose a single capital letter from the 'Action options': "A. Stop;B. Turn left; C. Turn right; D. Move forward; E. Move backward；", which corresponds to the action you have decided to take in the current environment. Place only the letter in 'Action', such as "Action: A"."""

        # 将所有任务相关的描述信息组合成一个完整的任务描述
        task_description = f"""{background} {background_supp}\n{instr_des}\n{history}\n{traj_info}\n{map_info}\n{map_supp}\n{option}\n{pre_planning}\n{requirement}\n{dist_require}\n{thought}\n{new_planning}\n{action}"""

        # 初始化历史记录，表示导航刚刚开始
        init_history = 'The navigation has just begun, with no history.'

        # 提取候选ID和索引信息
        # cand_ids = cand_inputs.get('cand_vpids', [])
        # cand_indices = cand_inputs.get('cand_indices', [])

        # 根据当前时间步t生成可能的动作选项
        action_options_batch, only_options_batch = self.make_action_options(cand_inputs, t=t)

        # 生成轨迹信息、地图信息和补充地图信息
        trajectory_text, graph_text, graph_supp_text = self.make_map_prompt()  

        # 如果是第一步（t == 0），初始化历史记录为导航刚开始
        if t == 0:
            prompt = f"""Instruction: {obs["instruction"]}\nHistory: {init_history}\nTrajectory: {trajectory_text}\nMap:{graph_text}\nSupplementary Info: {graph_supp_text}\nPrevious Planning:\n{self.planning[-1]}\nAction options (step {str(t)}): {action_options_batch}"""
        else:
            # 如果不是第一步，使用当前的历史记录
            prompt = f"""Instruction: {obs["instruction"]}\nHistory: {self.history}\nTrajectory: {trajectory_text}\nMap:{graph_text}\nSupplementary Info: {graph_supp_text}\nPrevious Planning:\n{self.planning[-1]}\nAction options (step {str(t)}): {action_options_batch}"""

        # 准备最终的导航输入字典，包含任务描述和提示信息
        nav_input = {
            "task_description": task_description,  # 任务描述
            "prompts": prompt,  # 当前的生成提示
            # "cand_ids": cand_ids,  # 候选视点ID
            "only_options": only_options_batch,  # 动作选项
            "action_options": action_options_batch,  # 当前批次的动作选项
            # "cand_indices": cand_indices,  # 候选视点索引
            "only_actions": cand_inputs["action_prompts"]  # 仅动作提示
        }

        # 返回最终的导航输入字典
        return nav_input
    
    def make_r2r_json_prompts(self, obs, cand_inputs, t):
        # 背景信息：描述机器人在现实世界中的导航任务
        background = """You are an embodied robot that navigates in the real world."""
        # background_supp = """You need to explore between some places marked with IDs and ultimately find the destination to stop.""" \
        #                 """ At each step, a series of images corresponding to the places you have explored and have observed will be provided to you."""
        background_supp = """You need to explore between locations marked with IDs, eventually finding the target location and stopping there. 
                   At each step, you will receive images of the four candidate nodes (front, back, left, right) of your current node, showcasing the explored and observed locations. Provide a detailed description of what is in each image."""

        # 任务描述：
        # 'Instruction'：全球性的、逐步的指令，可能有些命令已经执行过，机器人需要识别哪些未执行的命令。
        instr_des = """'Instruction' is a global, step-by-step detailed guidance, but you might have already executed some of the commands. You need to carefully discern the commands that have not been executed yet."""
        # 'Trajectory'：记录机器人已探索的地点ID，从Place 0开始。
        traj_info = """'Trajectory' represents the ID info of the places you have explored. You start navigating from Place 0."""
        # 'Map'：记录已探索地点与其他观察到的地方的连接关系。
        map_info = """'Map' refers to the connectivity between the places you have explored and other places you have observed."""
        # 'Supplementary Info'：记录曾经观察过的地点及其图像，这些地点尚未访问，只有在出现导航错误时才会考虑。
        map_supp = """'Supplementary Info' records some places and their corresponding images you have ever seen but have not yet visited. These places are only considered when there is a navigation error, and you decide to backtrack for further exploration."""
        # 'History'：表示历史上已探索的地方及其图像，可能包含正确的地标或之前错误的探索。
        history = """'History' represents the places you have explored in previous steps along with their corresponding images. It may include the correct landmarks mentioned in the 'Instruction' as well as some past erroneous explorations."""
        # 'Action options'：当前步骤可采取的动作选项。
        option = """'Action options' are some actions that you can take at this step."""
        # 'Previous Planning'：记录之前的多步计划信息，当前可以参考。
        pre_planning = """'Previous Planning' records previous long-term multi-step planning info that you can refer to now."""

        # 任务要求：
        # 结合图片、指令、历史、地图等信息进行决策
        # requirement = """For each provided image of the places, you should combine the 'Instruction' and carefully examine the relevant information, such as scene descriptions, landmarks, and objects. You need to align 'Instruction' with 'History' (including corresponding images) to estimate your instruction execution progress and refer to 'Map' for path planning. Check the Place IDs in the 'History' and 'Trajectory', avoiding repeated exploration that leads to getting stuck in a loop, unless it is necessary to backtrack to a specific place."""
        requirement = """For the four candidate node images, you should carefully examine the relevant information from the 'instruction',
                such as scene descriptions, landmarks, and objects. You need to align the 'instruction' with the 'history' (including corresponding images),
                to assess the progress of the instruction and use the 'map' for path planning.
                Check the location IDs in the 'history' and 'trajectory' to avoid redundant exploration that may lead to cycles,
                unless it is necessary to backtrack to a specific location."""
        # 如果已经看到目标，估计与目标之间的距离。如果距离较远，继续前进并尝试在1米内停止。
        dist_require = """If you can already see the destination, estimate the distance between you and it. If the distance is far, continue moving and try to stop within 1 meter of the destination."""
        # 'Thought'：生成机器人思考的JSON格式答案，必须包括'Thought'、'New Planning'和'Action'三个字段。
        thought = """Your answer should be JSON format and must include three fields: 'Thought', 'New Planning', and 'Action'. You need to combine 'Instruction', 'Trajectory', 'Map', 'Supplementary Info', your past 'History', 'Previous Planning', 'Action options', and the provided images to think about what to do next and why, and complete your thinking into 'Thought'.rovide a detailed description of what is in each image in the 'Thought' field."""
        # 'New Planning'：基于当前的'History'、'Map'和'Previous Planning'，更新新的多步路径规划。
        new_planning = """Based on your 'Map', 'Previous Planning' and current 'Thought', you also need to update your new multi-step path planning to 'New Planning'."""
        # 'Action'：输出最终选定的动作选项，必须只包含一个字母（如"Action: A"）。
        action = """At the end of your output, you must provide a single capital letter in the 'Action options' that corresponds to the action you have decided to take, and place only the letter into 'Action', such as "Action: A" or "Action: B".Your every action choice must be based on image information, historical data, and other relevant factors, and cannot be made randomly."""

        # 将所有的任务描述信息组合成完整的任务描述字符串
        task_description = f"""{background} {background_supp}\n{instr_des}\n{history}\n{traj_info}\n{map_info}\n{map_supp}\n{pre_planning}\n{option}\n{requirement}\n{dist_require}\n{thought}\n{new_planning}\n{action}"""

        # 初始化历史记录：表示刚开始时没有历史记录
        init_history = 'The navigation has just begun, with no history.'

        #  # 提取候选ID和索引信息
        # cand_ids = cand_inputs.get('cand_vpids', [])
        # cand_indices = cand_inputs.get('cand_indices', [])

        # 根据当前时间步t生成可能的动作选项
        action_options_batch, only_options_batch = self.make_action_options(cand_inputs, t=t)

        # 生成轨迹信息、地图信息和补充地图信息
        trajectory_text, graph_text, graph_supp_text = self.make_map_prompt()  

        # 如果是第一步（t == 0），初始化历史记录为导航刚开始
        if t == 0:
            prompt = f"""Instruction: {obs["instruction"]}\nHistory: {init_history}\nTrajectory: {trajectory_text}\nMap:{graph_text}\nSupplementary Info: {graph_supp_text}\nPrevious Planning:\n{self.planning[-1]}\nAction options (step {str(t)}): {action_options_batch}"""
        else:
            # 如果不是第一步，使用当前的历史记录
            prompt = f"""Instruction: {obs["instruction"]}\nHistory: {self.history}\nTrajectory: {trajectory_text}\nMap:{graph_text}\nSupplementary Info: {graph_supp_text}\nPrevious Planning:\n{self.planning[-1]}\nAction options (step {str(t)}): {action_options_batch}"""

        # 准备最终的导航输入字典，包含任务描述和提示信息
        nav_input = {
            "task_description": task_description,  # 任务描述
            "prompts": prompt,  # 当前的生成提示
            # "cand_ids": cand_ids,  # 候选视点ID
            "only_options": only_options_batch,  # 动作选项
            "action_options": action_options_batch,  # 当前批次的动作选项
            # "cand_indices": cand_indices,  # 候选视点索引
            "only_actions": cand_inputs["action_prompts"]  # 仅动作提示
        }

        # 返回最终的导航输入字典
        return nav_input
    

 # 解析导航输出中的动作指令，提取出每个样本的具体动作（在指定的选项范围内），并返回动作的索引
    def parse_action(self, nav_output, only_options, t):
        """
        解析导航输出中的动作部分。
        """
        # 清除首尾空白字符
        output = nav_output.strip()

        # 默认值
        action_letter = None
        action_idx = 0  # 默认选择第一个动作

        # # 调试输出，打印原始输出
        # print("Raw output:", output)

        # 查找 "Action" 关键字后带字母的内容，增强匹配
        pattern = re.compile(r"Action:\s*([A-M])")  # 确保匹配 A-M 范围的字母
        match = pattern.search(output)
        print(match)

        if match:
            action_letter = match.group(1)  # 提取动作字母
            print(f"Matched action: {action_letter}")  # 调试输出已匹配的动作字母
            try:
                action_idx = only_options.index(action_letter)  # 找到字母对应的索引
                print(f"Action index found: {action_idx}")  # 调试输出
            except ValueError:
                print(f"Action letter {action_letter} not in only_options: {only_options}")
                action_idx = 0  # 设置默认值
        else:
            print(f"Action not found in output: {output}")
            action_letter = "A"
            action_idx = 0  # 设置默认值

        # 调试输出
        print(f"Parsed action: {action_letter}, action_idx: {action_idx}")

        # 如果设置了 stop_after 参数，且当前步数 t 小于 stop_after，则加1避免过早停止
        if bool(self.args.stop_after) and t < self.args.stop_after:
            action_idx = min(action_idx + 1, len(only_options) - 1)  # 确保索引不超出范围

        # 返回动作的索引
        return action_idx





    
    # 解析导航输出 (nav_output) 中的新规划信息，并将其存储到内部的 self.planning 列表中。
# 它依赖两个关键词（'New Planning:' 和 'Action:'）来找到新规划的开始和结束位置，提取该规划信息，并进行一些后续的格式处理。
    def parse_planning(self, nav_output):
        """
        解析导航输出中的规划部分。
        支持特定格式的导航输出。如果输出风格不一致，请修改解析器。
        """
        # 获取单个导航输出
        output = nav_output.strip()  # 清除首尾空白字符
        
        # 定义关键词，用于从输出中提取规划信息
        keyword1 = 'New Planning:'  # 新规划的标识
        keyword2 = 'Action:'        # 动作的标识

        start_index = output.find(keyword1)
        end_index = output.find(keyword2)

        # 如果找不到关键词，返回默认值
        if start_index == -1 or end_index == -1 or start_index + len(keyword1) >= end_index:
            planning = "No plans currently."
        else:
            # 提取新规划的部分
            planning = output[start_index + len(keyword1):end_index].strip()

        # 替换 "new" 和 "New" 为 "previous" 和 "Previous"
        planning = planning.replace('new', 'previous').replace('New', 'Previous')

        # 初始化 self.planning 如果尚未存在
        if not hasattr(self, "planning"):
            self.planning = []

        # 确保 self.planning 是一个列表
        self.planning.append(planning)

        # 返回最新解析的规划
        return planning
    
    def make_history(self, a_t, nav_input, t):
        """
        更新历史记录，记录当前时刻执行的动作
        """
        # # 在动作列表中加入 "stop" 动作
        # nav_input["only_actions"] = ['stop'] + nav_input["only_actions"]
        
        # 获取当前的动作
        last_action = nav_input["only_actions"][a_t]  # 根据a_t获取当前动作
        
        # 根据当前时间步t更新历史记录
        if t == 0:
            self.history += f"""step {str(t)}: {last_action}"""
        else:
            self.history += f""", step {str(t)}: {last_action}"""

    def parse_json_planning(self, json_output):
        """
        从 JSON 输出中解析规划信息，假设 JSON 输出包含 "New Planning" 字段。
        """
        print("在进行planning")
        try:
            # 尝试从 JSON 输出中获取新规划
            planning = json_output["New Planning"]
        except:
            # 如果没有 "New Planning" 字段，则返回默认值
            planning = "No plans currently."

        # 将解析出的规划添加到规划记录中
        self.planning[0].append(planning)
        return planning
    
    def parse_json_action(self, json_output, only_options_batch, t):
        """
        从 JSON 输出中解析动作信息，假设 JSON 输出包含 "Action" 字段。
        """
        print("在进行行动分析")

        try:
            # 尝试从 JSON 输出中获取动作
            output = str(json_output["Action"])
            print(output)
            # 如果找到的动作在可选动作中，返回对应的索引
            if output in only_options_batch:
                output_index = only_options_batch.index(output)
                print("找到的动作在可选动作中，返回对应的索引:",output_index)
            else:
                # 如果没有找到，默认选择0
                print("没有找到，默认选择4")
                output_index = 4
        except:
            # 如果没有找到动作字段，默认选择第一个动作
            print("没有找到动作字段，默认选择4")
            output_index = 4

        # # 如果设置了 stop_after 参数，且当前步数 t 小于 stop_after，则加1避免在 3 步内停止
        # if bool(self.args.stop_after):
        #     if t < self.args.stop_after:
        #         output_index += 1  # 增加索引避免提前停止

        # 返回动作选项的索引列表
        output_index_batch = output_index
        return output_index_batch