import re
import math

class PromptManager(object):
    # 初始化 OneStagePromptManager 类，配置与内部状态
    def __init__(self, args):
        self.args = args  # 接受参数并存储
        self.history  = ''  # 用于存储历史记录
        self.nodes_list = []  # 用于存储节点列表
        self.candidate_images = [] #用于存储候选节点的图片
        self.node_imgs = []  # 用于存储当前节点对应图像
        self.road_graph = {}   # 存储每个坐标可通行道路的图（用字典表示节点和连接）
        self.graph = {} #存储每个坐标点的全部连接情况图
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

    def make_image_prompt_json(self): 
        # Part 1: Background Information 
        background = """You are an embodied robot navigating through different environments in the real world. 
                        Your task is to explore your surroundings step by step and identify key information about the observed locations. 
                        At each step, you will receive a series of descriptions for observed areas. Use these descriptions to understand the environment, detect objects, and make navigation decisions."""

        # Part 2: Scene and Environment Description
        scene_description = """scene_description: Based on the provided descriptions of the observed areas, analyze the specific details of each scene, 
                            such as objects, structures, colors, and notable features. Identify the environment type (e.g., office, corridor, exhibition hall, living room, or undefined) 
                            and describe the observed locations in detail. Indicate if any part of the description is directly related to the task instructions. 
                            Example:
                            image1: "This scene shows a wooden door with a metal handle, white walls on the left, and a smooth light-colored concrete floor.";
                            image7: "This scene reveals an open door leading to a hallway with white walls and tiled floors.";
                            environment: The robot appears to be in a modern office or similar building environment."""

        # Part 3: Item List Description 
        object_recognition = """Identify and list all objects observed in each scene. Objects may include tables, chairs, doors, walls, windows, stairs, walkable pathways, or any other items visible. Walkable pathways refer to unobstructed(cardboard box) and open ground that allows the robot to navigate forward. 
                    Provide the output as a list in the following format:
                    image4: [table, chair, door, walkable pathway]; 
                    image9: [wall, window, stairs]."""

        # Part 4: navigable Area Identification 
        navigable_area = """Identify if there are any clear walkable pathways in each scene. 
                        A walkable pathway refers to an unobstructed, open ground that allows the robot to move forward. If the scene contains a cardboard box, the path will be impassable and should be explicitly noted. 
                        If a scene contains walkable pathways, explicitly indicate it and return a list of all such images. 
                        Example:
                        road: [6, 8, 9] (images 6 and 9 have walkable pathways).
                        The format `road: [6, 8, 9]` is not allowed; it must not appear as `road: ['image6', 'image8', 'image9']`."""

        # Part 5: Distance to Obstacles 
        distance_to_obstacles = """Estimate the distance to the nearest obstacle (e.g., wall, cardboard box) in each observed scene.Please note that the cardboard box is considered an obstacle and should be included.
                                The distance estimation should be inferred based on the actual size of the objects in the image, their relative position, and the type of the object.
                                You must estimate the distance by referencing the visual proportion of the object or known object dimensions. Please keep one decimal place.Example:
                                image1: "approximately 2.3 meters";
                                image5: "approximately 1.5 meter".；
                                image7: "less than 0.5 meter"."""        
        

        # Part 6: Thought Process 
        thought = """Your response must include the following four sections: 
                    1. 'imageInfo': Detailed descriptions of the observed scenes. 
                    2. 'item_list': A list of all objects identified in each scene.
                    3. 'distance_to_obstacles': An estimate of the distance to the nearest obstacle for each scene.
                    4. 'road': A list of images that contain clear walkable pathways.The format `road: [7, 8]` is not allowed; it must not appear as `road: ['image7', 'image8']`.

                    Format your response strictly in JSON format."""

        # Combine all parts to form the final prompt
        image_prompt = f"""{background}\n{scene_description}\n{object_recognition}\n{navigable_area}\n{distance_to_obstacles}\n{thought}"""

        # Explicitly require a JSON-formatted response
        return f"Please respond in the following JSON format:\n{{'imageInfo': '<image_info>', 'item_list': <item_list>, 'distance_to_obstacles': <distance_to_obstacles>, 'road': <road_list>}}\n{image_prompt}"



    def parse_json_image_info(self, image_info):
        # 从 image_info 提取各个字段
        image_info_data = image_info.get('imageInfo', {})
        item_list_data = image_info.get('item_list', {})
        distance_to_obstacles_data = image_info.get('distance_to_obstacles', {})
        road_data = image_info.get('road', [])

        # 将提取的数据组织成字典并返回
        image_result = {
            "imageInfo": image_info_data,
            "item_list": item_list_data,
            "distance_to_obstacles": distance_to_obstacles_data,
            "road": road_data
        }

        return image_result


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

        # 更新轨迹，记录当前视点
        trajectory.append(obs['viewpointId'])

        # 遍历候选视点并生成对应的动作提示
        for cc in obs['candidate']:
            cand_vpids.append(cc['candidate_viewpointId'])  # 添加候选视点ID
            # cand_index.append(cc['idx'])  # 添加候选视点索引

            # 根据航向和高度生成动作概念
            direction = self.get_action_concept(cc['candidate_heading'] - previous_angle)

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

        #加入停止操作选项
        stop_text =f"The goal is right ahead, I stop."
        action_prompts.append(stop_text)

        #加入回溯选项
        # backtrack_text = "No valid paths are available. Choose to backtrack to a historical path."
        backtrack_text = "Choose to backtrack to a historical path."
        action_prompts.append(backtrack_text)

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
        # 生成完整的动作选项（带字母标签）和仅包含选项字母的列表
        full_action_options = [chr(j + 65) + '. ' + action_prompts[j] for j in range(len(action_prompts))]
        only_options = [chr(j + 65) for j in range(len(action_prompts))]
        
        action_options.append(full_action_options)
        only_options.append(only_options)

        return action_options, only_options  # 返回完整选项和标签


    def make_map_prompt(self, road): 
        """
        基于单视点生成地图提示，同时生成原始图和 road_map。
        :param road: 包含可通行节点索引的列表，例如 ['7', '8']
        :return: 轨迹文本、原始图的连接信息、road_map 的连接信息、补充地图信息
        """
        trajectory = self.trajectory
        nodes_list = self.nodes_list
        graph = self.graph  # 筛选后的原始图

        # 初始化输出文本
        trajectory_text = "Place " + " ".join(str(nodes_list.index(node)) for node in trajectory)

        # 构建原始图 full_graph
        full_graph_text = ""
        for node in trajectory:
            node_index = nodes_list.index(node)
            adj_nodes = graph.get(node, [])
            adj_text = ", ".join(str(nodes_list.index(adj)) for adj in adj_nodes)
            full_graph_text += f"\nPlace {node_index} is connected with Places {adj_text}"

        # 获取最新的节点
        latest_node = trajectory[-1]  # 最新的节点是轨迹的最后一个节点
        road_list = road  # 传入的 road 列表（可通行的节点列表）

        # 更新 self.road_graph，将最新的节点和 road 列表拼接
        if latest_node in self.road_graph:
            # 如果该节点已存在，则拼接新的 road 列表
            self.road_graph[latest_node] += road_list
        else:
            # 如果该节点不在，则直接添加该节点和 road 列表
            self.road_graph[latest_node] = road_list

        # 使用更新后的 self.road_graph 来拼接 road_map_text,并保存成一个字典
        road_map_text = ""
        road_map_dict = {}  # 初始化字典
        for node in self.road_graph:
            node_index = nodes_list.index(node)
            updated_adj_nodes = self.road_graph[node]  # 使用更新后的邻接节点
            adj_text = ", ".join(str(nodes_list.index(adj)) for adj in updated_adj_nodes)
            road_map_text += f"\nPlace {node_index} is connected with Places {adj_text}"
            # 添加到字典中
            road_map_dict[node_index] = [nodes_list.index(adj) for adj in updated_adj_nodes]
        print("road_map_dict：",road_map_dict)
       
       
        # 补充未访问节点的信息，基于 road_map
        graph_supp_text = ""
        # 将 road_map 的 key 和 value 转换为列表
        road_map_keys = list(self.road_graph.keys())
        # 是当前节点前面一位节点的所有未访问节点，当前节点的候选节点是不计算入内的，因为这个remaining_nodes是用来回溯的，未来的候选节点不算入回溯的情况
        road_map_values = [item for sublist in list(self.road_graph.values())[:-1] for item in sublist]
        # 过滤出所有未访问且可到达的节点
        remaining_nodes = [node for node in road_map_values if node not in road_map_keys]

        # 生成补充的文本
        for node in remaining_nodes:
            if node in nodes_list:  # 确保节点在 nodes_list 中
                node_index = nodes_list.index(node)
                graph_supp_text += f"\nPlace {node_index}, which is corresponding to Image {node_index}"

        if not graph_supp_text:
            graph_supp_text = "Nothing yet."

        # 返回轨迹文本、原始图的连接信息、road_map 的连接信息、补充地图信息
        return trajectory_text, full_graph_text, road_map_text, graph_supp_text,remaining_nodes,road_map_dict


    def task_description(self, t):
        """
        生成任务描述部分，包括背景信息、任务说明、历史信息等。
        """
        background = """You are an embodied robot that navigates in the real world. Your task is to explore between locations marked with IDs and ultimately find the target location. Once you are within 0.4 meters of the target, you should stop and report your final position.
                            At each step, you will receive images of the four candidate nodes (front, back, left, right) of your current node, showcasing the explored and observed locations. Provide a detailed description of what is in each image."""

        Instruction = """'Instruction' provides global, step-by-step guidance for the robot. Some commands might already have been executed, and you need to identify which ones remain to be completed."""

        Trajectory = """'Trajectory' represents the ID information of the places you have explored, with navigation starting from Place 0."""

        Map = """'Map' refers to the connectivity between the places you have explored and other places you have observed."""

        Map_supp = """'Supplementary Info' records some places and their corresponding images you have ever seen but have not yet visited. These places are only considered when there is a navigation error, and you decide to backtrack for further exploration."""

        history = """'History' represents the places you have explored in previous steps along with their corresponding images. It may include the correct landmarks mentioned in the 'Instruction' as well as some past erroneous explorations."""

        pre_planning = """'Previous Planning' records previous long-term multi-step planning info that you can refer to now."""

        return f"""{background} \n{Instruction}\n{history}\n{Trajectory}\n{Map}\n{Map_supp}\n{pre_planning}"""


    def requirements_and_thought(self):
        """
        生成任务要求和思考部分的描述。
        """
        requirement = """You should carefully examine the descriptions of the candidate nodes, align them with the 'instruction' and 'history' to evaluate your progress, and use the 'map' for path planning.Choose the direction (left or right) to avoid the obstacle, if possible.
                            Avoid redundant exploration unless it is necessary to backtrack to a specific location. You must carefully examine the 'road' field, which indicates the candidate nodes containing walkable pathways. If a node does not have a walkable pathway, it **cannot** be selected for movement. Cross-reference this information with the 'item_list' and 'instruction' to ensure the decision aligns with the goal. Only choose an action corresponding to a walkable pathway listed in the 'road' field."""

        dist_require = """If you can already see the destination in the descriptions, estimate the distance between you and it. 
                                You can estimate the distance based on the relative size of the object in the image and its pixel size. 
                                If the distance is far, continue moving and try to stop within 0.1 meter of the destination."""

        thought = """Your answer must be in JSON format with 'Thought', 'New Planning', and 'Action' fields.
    "Thought": Reason about the task by referring to the 'instruction', 'history', 'map', and candidate node descriptions. Prioritize turning left or right to avoid obstacles(such as box), and avoid backtracking unless absolutely necessary. Only consider actions for nodes listed in the 'road' field (walkable pathways).
    "New Planning": Update your multi-step navigation plan based on the current step and available pathways.
    "Action": Select the letter of the next action from the 'Action options', ensuring it corresponds to a node in the 'road' field. Output only the action letter, such as Action: 'A'.The preferred option is to choose backtracking rather than turning around."""

        return f"""{requirement}\n{dist_require}\n{thought}"""


    def image_info_text(self, image_info):
        """
        将 image_info 字典中的描述拼接成文字，生成候选节点的描述。
        """
        image_descriptions = "\n".join([f"{key}: {desc}" for key, desc in image_info.items()])
        return f"The descriptions of the candidate nodes are as follows:\n{image_descriptions}"


    def make_json_prompts(self, cand_inputs, image_info, obs, t):
        # 获取任务描述、要求和思考部分的文本
        task_background = self.task_description(t)
        task_requirements_and_thought = self.requirements_and_thought()

        # 生成候选节点的描述文本
        image_info_text = self.image_info_text(image_info)

        # 生成当前的导航提示
        road = image_info.get('road', [])
        trajectory_text, full_graph_text, road_map_text, graph_supp_text, remaining_nodes, road_map_dict = self.make_map_prompt(
            road)
        action_options_batch, only_options_batch = self.make_action_options(cand_inputs, t=t)

        # 生成完整的任务描述
        task_description = f"""{task_background}\n{task_requirements_and_thought}"""

        # 初始化历史记录：表示刚开始时没有历史记录
        init_history = 'The navigation has just started with no previous history.'
        
        # 拼接生成导航输入
        if t == 0:
            prompt = f"""Instruction: {obs["instruction"]}\nHistory: {init_history}\nTrajectory: {trajectory_text}\nMap: {road_map_text}\nSupplementary Info: {graph_supp_text}
    Candidate Node Descriptions:\n{image_info_text}\nPrevious Planning:\n{self.planning[-1]}\nAction options (step {t}): {action_options_batch}"""
        else:
            prompt = f"""Instruction: {obs["instruction"]}\nHistory: {self.history}\nTrajectory: {trajectory_text}\nMap: {road_map_text}\nSupplementary Info: {graph_supp_text}
    Candidate Node Descriptions:\n{image_info_text}\nPrevious Planning:\n{self.planning[-1]}\nAction options (step {t}): {action_options_batch}"""

        # 返回导航输入
        nav_input = {
            "task_description": task_description,
            "prompts": prompt,
            "only_options": only_options_batch,
            "action_options": action_options_batch,
            "only_actions": cand_inputs["action_prompts"],
            "remaining_nodes": remaining_nodes,
            "road_map_dict": road_map_dict
        }

        return nav_input
    
    
    def make_history(self, a_t, nav_input, t):
        """
        更新历史记录，记录当前时刻执行的动作
        """
        # 获取当前的动作
        last_action = nav_input["only_actions"][a_t]  # 根据a_t获取当前动作
        
        # 根据当前时间步t更新历史记录
        if t == 0:
            self.history += f"""step {str(t)}: {last_action}"""
        else:
            self.history += f""", step {str(t)}: {last_action}"""
        self.history

    def parse_json_planning(self, json_output):
        """
        从 JSON 输出中解析规划信息，假设 JSON 输出包含 "New Planning" 字段。
        """
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

        try:
            # 尝试从 JSON 输出中获取动作
            output = str(json_output["Action"])
            print("Action analysis:", output)
            # 如果找到的动作在可选动作中，返回对应的索引
            if output in only_options_batch:
                output_index = only_options_batch.index(output)
                print("action index:",output_index)
            else:
                # 如果没有找到，默认选择4
                output_index = 4
        except:
            # 如果没有找到动作字段，默认选择第一个动作
            output_index = 4

        # 返回动作选项的索引列表
        output_index_batch = output_index
        return output_index_batch