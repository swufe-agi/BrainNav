import sys
import os
import glob
from agent_prompt_manager import PromptManager
from agent_api import *
from actions import *
import json
import copy
from nav_log import *
import logging

class NavigationAgent:

    def __init__(self, args, prompt_manager=None, log_file='navigation_log.txt'):
        self.args = args
        self.results = []
        self.prompt_manager = prompt_manager
        self.global_viewpoint_id = 5  # 初始化全局 viewpointId 计数器
        self.item_list_all = []
        self.image_index = 1
        self.log_file = log_file
        self.timer = Timer()


    def start_road(self, next_viewpointId, road_map_dict, history_data):
        """
        从头到尾遍历路径，直到找到目标视点的父节点，且将目标视点作为子节点添加到路径中，
        然后获取路径中各视点的坐标。
        :param next_viewpointId: 目标视点 ID
        :param road_map_dict: 路径图字典，表示视点之间的连通性
        :param obs: 包含历史记录的观测状态
        :return: 包含路径中各视点坐标的列表
        """
        # 初始化路径列表
        forward_path = []
        # 确保目标视点 ID 是整数类型
        next_viewpointId = int(next_viewpointId)
        
        # 1. 找到目标视点的父节点
        print(f"开始从当前视点开始遍历，直到找到目标视点 {next_viewpointId} 的父节点")
        
        parent_node = None  # 用来存储目标视点的父节点
        for key, values in road_map_dict.items():
            if next_viewpointId in values:
                parent_node = key
                print(f"找到目标视点 {next_viewpointId} 的父节点: {parent_node}")
                break

        if parent_node is None:
            print(f"错误: 在 road_map_dict 中找不到目标视点 {next_viewpointId} 的父节点")
            raise ValueError(f"无法找到目标视点 {next_viewpointId} 的父节点。")

        # 2. 从头遍历父节点列表，直到找到目标视点的父节点
        parent_list = []
        for key, values in road_map_dict.items():
            parent_list.append(key)  # 存储父节点
        print("父节点列表：", parent_list)

        # 正序遍历父节点列表，直到找到目标视点的父节点
        for current_node in parent_list:
             # 将路径中的视点 ID 转换为整数类型，以确保与 history_data 中的类型一致
            forward_path.append(int(current_node))
            print(f"路径: {forward_path}")
            if current_node == parent_node:
                break

        # 3. 将目标视点的子节点添加到路径
        forward_path.append(int(next_viewpointId))
        print(f"最终路径: {forward_path}")

        # 4. 获取路径中各视点的坐标
        coordinates_list = []
        for viewpoint in forward_path:
            try:
                # 查找对应视点的字典
                viewpoint_data = next(item for item in history_data if item['candidate_viewpointId'] == viewpoint)
                coord = viewpoint_data['candidate_viewpoint']
                coordinates_list.append(coord)
                print(f"视点 {viewpoint} 的坐标为 {coord}")
            except (KeyError, IndexError, TypeError, StopIteration) as e:
                print(f"错误: 无法在 history_data 中找到视点 {viewpoint} 的坐标。错误信息: {e}")
                raise

        print(f"最终坐标路线为: {coordinates_list}")
        return coordinates_list


    def _get_image_files(self, folder_path):
        """
        获取指定文件夹中的图像文件
        """
        image_files = glob.glob(os.path.join(folder_path, "*.jpg")) + glob.glob(os.path.join(folder_path, "*.png"))
        return image_files
    
    def write_log(self, message):
        logger.info(message)  # 直接使用 logger 来记录日志
    
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


# 1、获取next_viewpointId从road_map_dict字典这个value值对应的key值
            # 2、获取从road_map_dict字典从当前now_viewpointId这个key值到上面next_viewpointId这个value值对应的key值之间的元素，弄成列表
            # 3、把这个列表最后再加上一个next_viewpointId
            # 4、从obs["history"],里获取这个列表所有元素对应的坐标,obs['history'][x]['candidate_viewpoint']，把这个坐标拼接成一个列表返回
#         具体思路：
# 从目标视点找到其父节点：首先找到目标视点的父节点，直到找到目标视点对应的父节点为止。
# 回溯到父节点：然后从当前视点开始，回溯到目标视点的父节点，遍历父节点。
# 路径构建：最后将目标视点（作为子节点）添加到路径列表中，完成回溯路径。        
    def backtrack_road(self, now_viewpointId, next_viewpointId, road_map_dict, obs):
        """
        从当前视点回溯到目标视点的父节点，然后将目标视点作为子节点添加到路径列表。
        :param now_viewpointId: 当前视点 ID
        :param next_viewpointId: 目标视点 ID
        :param road_map_dict: 路径图字典，表示视点之间的连通性
        :param obs: 包含历史记录的观测状态
        :return: 包含路径中各视点坐标的列表
        """
        # 初始化路径列表
        backtrack_path = []
        
        # 1. 找到目标视点的父节点
        print(f"开始从当前视点 {now_viewpointId} 回溯到目标视点 {next_viewpointId}")
        
        parent_node = None  # 用来存储目标视点的父节点
        # 确保 road_map_dict 包含了每个视点的父节点关系
        for key, values in road_map_dict.items():
            if next_viewpointId in values:
                parent_node = key
                print(f"找到目标视点 {next_viewpointId} 的父节点: {parent_node}")
                break
        
        if parent_node is None:
            print(f"错误: 在 road_map_dict 中找不到目标视点 {next_viewpointId} 的父节点")
            raise ValueError(f"无法找到目标视点 {next_viewpointId} 的父节点。")

        # # 2. 从当前视点开始回溯到目标视点的父节点
        # backtrack_path.append(now_viewpointId)  # 先添加当前视点
        # print(f"已将当前视点 {now_viewpointId} 添加到路径。当前路径: {backtrack_path}")

        parent_list = []
        for key,values in road_map_dict.items():
                parent_list.append(key)  # 仅存储父节点
        # 倒序父节点列表
        parent_list.reverse()
        print("parent_list:",parent_list)
        
        current_node = now_viewpointId
        # 向上回溯，直到找到当前视点的父节点
        for current_node in parent_list:
            # print("current_node:",current_node)
            backtrack_path.append(current_node)
            # print(f"路径: {backtrack_path}")
            if current_node == parent_node: 
                break

        # 3. 将目标视点的子节点添加到路径
        backtrack_path.append(next_viewpointId)
        print(f"最终路径: {backtrack_path}")

        # 4. 获取路径中各视点的坐标
        coordinates_list = []
        for viewpoint in backtrack_path:
            try:
                coord = obs['history'][viewpoint]['candidate_viewpoint']
                coordinates_list.append(coord)
                print(f"视点 {viewpoint} 的坐标为 {coord}")
            except KeyError as e:
                print(f"错误: 无法在 obs['history'] 中找到视点 {viewpoint} 的坐标。错误信息: {e}")
                raise

        print(f"最终坐标路线为: {coordinates_list}")
        return coordinates_list




    def make_equiv_action(self, a_t, obs,remaining_nodes, road_map_dict,traj=None, t=0):
        """
        根据当前动作更新视点和候选点。
        :param a_t: 当前时间步的动作（整数），而不是列表
        :param obs: 当前的观测状态（字典），会在函数内被直接修改
        :param traj: 当前的轨迹信息（可选）
        :param t: 当前时间步（整数）

        """
         # 确保 obs 是字典
        if isinstance(obs, list):  # 如果 obs 是列表，需要访问其中的字典
            obs = obs[0]  # 取列表中的第一个字典元素

        # 当前坐标
        now_viewpoint = obs["viewpoint"]
        now_viewpointId = obs['viewpointId']
        now_absolute_heading = obs['absolute_heading']

        
        if a_t==5:
            if remaining_nodes:
            # 选择 remaining_nodes 列表的最后一个节点
                backtrack_node = remaining_nodes[-1]
                selected_candidate =  obs['history'][backtrack_node]
                print("selected_candidate选择的候选节点：",selected_candidate)
                print(f"选择回溯到未执行节点: {backtrack_node}")
            else:
                # 这个情况就是，最开始的时候就没有可通行的路，那就让小车固定去0这个点
                selected_candidate = obs['candidate'][0]
        else:
        # 获取当前动作对应的候选点
            action_idx = a_t  # 直接使用 a_t（应该是整数）
            selected_candidate = obs['candidate'][action_idx]  # 获取所选候选点的信息
        
    
        # 更新视点到所选候选点
        obs['viewpoint'] = selected_candidate['candidate_viewpoint']
        obs['viewpointId'] = selected_candidate['candidate_viewpointId']
        obs['absolute_heading'] = selected_candidate['candidate_absolute_heading']
        
        if a_t==5:
            if remaining_nodes:
            # 更新视点后的坐标
                next_viewpoint = obs['viewpoint']
                next_viewpointId = obs['viewpointId'] 
                # 找到回溯路径
                backtrack_path_coordinates = self.backtrack_road(now_viewpointId, next_viewpointId, road_map_dict, obs)
                move_car(a_t, now_absolute_heading, backtrack_path_coordinates)
        else:      
        # 执行动作：move_car
            move_car(a_t, now_absolute_heading, backtrack_path_coordinates=None)

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
            candidate['candidate_absolute_heading'] = (obs['absolute_heading'] + i*90)%360
            self.global_viewpoint_id += 1  # 更新全局 viewpointId

        # 更新指令 ID
        obs['instr_id'] += 1

        # 打印小车的动作
        print(f"小车执行了动作 {a_t}，移动到 {obs['viewpoint']}, 是 place: {obs['viewpointId']}, 对应 image {obs['viewpointId']}")



# # 回溯测试用例
#     def test_backtrack_functionality(self):
#             # 准备测试数据
#         obs = {
#                 'viewpoint': [-1, -2],
#                 'viewpointId': 12,
#                 'heading': 0,
#                 'absolute_heading': 270,
#                 'instr_id': 3,
#                 'instruction': 'Find the stairwell and stop in front of it.',
#                 'candidate': [
#                     {
#                         'candidate_viewpointId': 13,
#                         'candidate_viewpoint': [-1, -1],
#                         'candidate_heading': 0,
#                         'candidate_absolute_heading': 270,
#                         'image': None
#                     },
#                     {
#                         'candidate_viewpointId': 14,
#                         'candidate_viewpoint': [0, -2],
#                         'candidate_heading': 90,
#                         'candidate_absolute_heading': 0,
#                         'image': None
#                     },
#                     {
#                         'candidate_viewpointId': 15,
#                         'candidate_viewpoint': [-1, -3],
#                         'candidate_heading': 180,
#                         'candidate_absolute_heading': 90,
#                         'image': None
#                     },
#                     {
#                         'candidate_viewpointId': 16,
#                         'candidate_viewpoint': [-2, -2],
#                         'candidate_heading': 270,
#                         'candidate_absolute_heading': 180,
#                         'image': None
#                     }
#                 ],
#                 'history': [
#                     {'candidate_viewpointId': 0, 'candidate_viewpoint': [0, 0], 'candidate_heading': 0, 'candidate_absolute_heading': 0, 'image': None},
#                     {'candidate_viewpointId': 1, 'candidate_viewpoint': [0, 1], 'candidate_heading': 0, 'candidate_absolute_heading': 0, 'image': None},
#                     {'candidate_viewpointId': 2, 'candidate_viewpoint': [1, 0], 'candidate_heading': 90, 'candidate_absolute_heading': 90, 'image': None},
#                     {'candidate_viewpointId': 3, 'candidate_viewpoint': [0, -1], 'candidate_heading': 180, 'candidate_absolute_heading': 180, 'image': None},
#                     {'candidate_viewpointId': 4, 'candidate_viewpoint': [-1, 0], 'candidate_heading': 270, 'candidate_absolute_heading': 270, 'image': None},
#                     {'candidate_viewpointId': 5, 'candidate_viewpoint': [0, 0], 'candidate_heading': 0, 'candidate_absolute_heading': 180, 'image': None},
#                     {'candidate_viewpointId': 6, 'candidate_viewpoint': [1, -1], 'candidate_heading': 90, 'candidate_absolute_heading': 270, 'image': None},
#                     {'candidate_viewpointId': 7, 'candidate_viewpoint': [0, -2], 'candidate_heading': 180, 'candidate_absolute_heading': 0, 'image': None},
#                     {'candidate_viewpointId': 8, 'candidate_viewpoint': [-1, -1], 'candidate_heading': 270, 'candidate_absolute_heading': 90, 'image': None},
#                     {'candidate_viewpointId': 9, 'candidate_viewpoint': [0, -1], 'candidate_heading': 0, 'candidate_absolute_heading': 0, 'image': None},
#                     {'candidate_viewpointId': 10, 'candidate_viewpoint': [1, -2], 'candidate_heading': 90, 'candidate_absolute_heading': 90, 'image': None},
#                     {'candidate_viewpointId': 11, 'candidate_viewpoint': [0, -3], 'candidate_heading': 180, 'candidate_absolute_heading': 180, 'image': None},
#                     {'candidate_viewpointId': 12, 'candidate_viewpoint': [-1, -2], 'candidate_heading': 270, 'candidate_absolute_heading': 270, 'image': None}
#                 ],
#                 'trajectory': [[0, 0]]
#             }


#             # 准备路径图
#         road_map_dict = {0: [1, 2, 3], 3: [7, 8], 7: [9,12],12:[]}

#         remaining_nodes = [1,2,8,9]  # 假设剩余的回溯节点

#             # 进行测试：执行回溯动作
#         self.make_equiv_action(5, obs, remaining_nodes, road_map_dict)

#             # 检查回溯路径是否正确
#         # expected_path = [[2, 1], [2, 0], [1, 1]]
#         print(obs)
#         print(f"回溯路径测试完成")



# # 主函数
# if __name__ == "__main__":

#     nav_agent = NavigationAgent(args=None, prompt_manager=None)  # 初始化导航代理 
#     # 运行回溯功能测试
#     nav_agent.test_backtrack_functionality()

    

    def update_candidate_images(self, obs, t):
        """
        更新候选点的图像信息。
        :param obs: 当前观测状态
        :param t: 当前时间步，决定使用哪个图像字典
        """
        
        candidate_image_urls = capture_four_directions()  # 调用外部函数拍摄四个方向的图片

        # 为每个候选点分配图像
        for candidate in obs['candidate']:
            # 获取候选点的绝对朝向
            heading = candidate['candidate_heading']

            # 根据朝向选择对应的图像URL
            image_url = candidate_image_urls.get(heading)

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
            'absolute_heading': 0,  # 初始绝对朝向
            'instr_id': 0,  # 指令的唯一标识符
            'instruction': instruction,#导航指令
            'candidate': [  # 候选点信息
                {
                    'candidate_viewpointId': 1,
                    'candidate_viewpoint': [0, 1],
                    'candidate_heading': 0,
                    'candidate_absolute_heading': 0,
                    'image': None,
                    # 'idx': 1
                },
                {
                    'candidate_viewpointId': 2,
                    'candidate_viewpoint': [1, 0],
                    'candidate_heading': 90,
                    'candidate_absolute_heading': 90,
                    'image': None,
                    # 'idx': 2
                },
                {
                    'candidate_viewpointId': 3,
                    'candidate_viewpoint': [0, -1],
                    'candidate_heading': 180,
                    'candidate_absolute_heading': 180,
                    'image': None,
                    # 'idx': 3
                },
                {
                    'candidate_viewpointId': 4,
                    'candidate_viewpoint': [-1, 0],
                    'candidate_heading': 270,
                    'candidate_absolute_heading': 270,
                    'image': None,
                    # 'idx': 4
                }
            ],
            'history': [{
                    'candidate_viewpointId': 0,
                    'candidate_viewpoint': [0, 0],
                    'candidate_heading': 0,
                    'candidate_absolute_heading': 0,
                    'image': None,
                }],  # 历史记录
            'trajectory': [[0, 0]]  # 当前轨迹初始化为起点
        }

        # 初始化轨迹信息
        traj = {
            'instr_id': obs['instr_id'],  # 当前轨迹对应的指令 ID
            'path': [obs['viewpoint']],  # 路径初始化为起点
            'a_t': {}  # 记录每个时间步的动作
        }

        # 检查任务是否已完成
        if traj['instr_id'] in self.results:
            print(f"Task {traj['instr_id']} already completed. Skipping.")
            return None

        # 记录初始的角度信息（朝向）
        previous_angle = obs['heading']


        self.timer.reset()
        # 记录指令到日志
        self.write_log(f"开始执行指令: {instruction}")





        print("============地图手册推理专家=================")

        # 检查文件是否存在且不为空
        files = ['item_list_storage.json', 'history_data.json', 'road_map_data.json']
        all_files_valid = True  # 用于标记是否所有文件都有效

        # 检查每个文件
        for file in files:
            if not os.path.exists(file) or os.stat(file).st_size == 0:
                # print(f"{file} 不存在或为空，跳过推理操作")
                all_files_valid = False  # 如果文件不合法，设置标志为False

        # 如果所有文件都有效，进行推理
        if all_files_valid:
            try:
                # 如果文件不为空，则进行推理
                place_sign_id, _ = gpt_infer_with_item_list_and_check(file_path='item_list_storage.json', instruction=obs['instruction'])

                if place_sign_id is not None:
                    print(f"大模型返回的对应place键值：{place_sign_id}")
                    # 要在开始导航到的目标点，因为不能走未知的路，所以只能根据前人的路走，假设在地图手册上有和指令相关的东西的话
                    next_viewpointId = place_sign_id

                    # 读取 history_data.json 文件
                    with open('history_data.json', 'r') as f:
                        history_data = json.load(f)  # 解析 JSON 内容

                    # 读取 road_map_data.json 文件
                    with open('road_map_data.json', 'r') as f:
                        road_map_data = json.load(f)  # 解析 JSON 内容
                        print("地图数据：", road_map_data)

                    road_map_dict = road_map_data
                    a_t = 5
                    now_absolute_heading = obs['absolute_heading']
                    backtrack_path_coordinates = self.start_road(next_viewpointId, road_map_dict, history_data)
                    move_car(a_t, now_absolute_heading, backtrack_path_coordinates)
                    # 根据返回的物品ID进行进一步的操作，如选择相应的图像或物品
                else:
                    print("未能从地图手册获得有效的placeID")

            except Exception as e:
                print(f"处理过程中发生了错误: {e}")

        else:
            print("地图手册为空或不存在，跳过地图手册推理专家")

        print("============地图手册推理专家完成=================")

        
        # 主导航循环
        for t in range(self.args.max_action_len):
            print("----------------------------------------------")
            print("第",t,"次行动开始")

            # 更新候选点图像
            self.update_candidate_images(obs,t)
            candidate_images = [candidate['image'] for candidate in obs['candidate']]
            image_list = candidate_images
            # print("image_list:",image_list)

            # 添加历史信息
            for candidate in obs['candidate']:
                obs['history'].append(copy.deepcopy(candidate))  # 使用深拷贝确保历史记录不会被修改

            # 获取候选行动提示。
            cand_inputs = self.prompt_manager.make_action_prompt(obs,previous_angle)
             
            print("--开始进行图片分析模块/专家--")
            # 视觉处理模块
            instruction = obs['instruction']
            image_prompt = self.prompt_manager.make_image_prompt_json()
            image_index =self.image_index
            image_info_output = gpt_infer_image(instruction, image_prompt,image_list,image_index, response_format={"type": "json_object"})
            
            self.image_index += len(image_list)
            print("--图片分析完成--")
            image_info = json.loads(image_info_output)
            road = image_info.get('road', [])
            item_list = image_info.get('item_list', [])

            # 将 item_list 拼接到 self.item_list_all 列表
            self.item_list_all.append(item_list) 


            
            print("--开始进行地图与提示构建模块/专家--")
            #开始构建导航图并记录轨迹
            # cand_inputs = self.prompt_manager.build_navigation_graph(obs)
            if self.args.response_format == 'str':
                # 根据提示生成导航输入（字符串格式）
                nav_input = self.prompt_manager.make_r2r_prompts(cand_inputs=cand_inputs,image_info=image_info, obs=obs, t=t)
            elif self.args.response_format == 'json':
                # 根据提示生成导航输入（JSON格式）
                nav_input = self.prompt_manager.make_json_prompts(cand_inputs=cand_inputs,image_info=image_info, obs=obs, t=t)
            else:
                # 如果响应格式不支持，抛出异常
                raise NotImplementedError("Unsupported response format. Please specify either 'str' or 'json'.")

        
           
            environment_prompts = nav_input["prompts"]
            print('-------------------- Environment Prompts --------------------')
            print(environment_prompts)
            print("--地图与提示构建完成--")

            
            print("--开始进行指令决策处理模块/专家--")
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
                nav_output, tokens = gpt_infer(nav_input["task_description"], environment_prompts,
                                                self.args.llm, self.args.max_tokens, response_format={"type": "json_object"})
                json_output = json.loads(nav_output)
                print('-------------------- Output --------------------')
                print(nav_output)
                a_t = self.prompt_manager.parse_json_action(json_output, nav_input["only_options"], t)
                self.prompt_manager.parse_json_planning(json_output)
            else:
                raise NotImplemented
            print("--指令决策处理完成--")

            print("--开始进行行动处理模块/专家--")
            # 更新轨迹中的动作信息
            traj['a_t'][t] = a_t
            print(a_t)
            
            # 检查是否停止动作
            if a_t == 4:
                return traj
            
            #car run function,未访问且可到达的节点remaining_nodes,可通行道路road_map_dict
            self.make_equiv_action(a_t, obs,nav_input["remaining_nodes"],nav_input["road_map_dict"], traj,t)
            traj['path'].append(obs['viewpoint'])
            traj['instr_id'] = obs['instr_id']


            # 更新历史记录
            self.prompt_manager.make_history(a_t, nav_input, t)

            # 保存结果到 self.results
            self.results.append(obs['viewpointId'])
            print("--小车行动处理完成--")
            # print(obs)
            print("----------------------------------------------")
            
            # print("一轮结束===========================obs['history']:================================",obs['history'])

        # 保存 obs['history'] 和 nav_input["road_map_dict"] 到文件
        history_file = 'history_data.json'
        road_map_file = 'road_map_data.json'
        # 保存 item_list 数据到文件
        item_list_file = 'item_list_storage.json'
        
        with open(item_list_file, 'w') as f:
            json.dump(self.item_list_all, f, indent=4)  # 将字典内容保存到文件
        print(f"物品列表已保存到 {item_list_file}")

            # 保存 history 数据
        with open(history_file, 'w') as f:
            json.dump(obs['history'], f, indent=4)
        print(f"历史记录已保存到 {history_file}")

            # 保存 road_map_dict 数据
        with open(road_map_file, 'w') as f:
            json.dump(nav_input["road_map_dict"], f, indent=4)
        print(f"地图数据已保存到 {road_map_file}")

        return traj


class Args:
    def __init__(self):
        # self.llm = 'gpt-4-vision-preview'
        self.llm = 'gpt-4o-2024-05-13'
        self.max_action_len = 10
        # self.response_format = 'str'
        self.response_format = 'json'
        self.max_tokens = 1000
        # self.stop_after = 8


# 主函数
if __name__ == "__main__":

    args = Args()
    instruction = get_user_input()
    prompt_manager = PromptManager(args)  # 初始化提示管理器
    nav_agent = NavigationAgent(args, prompt_manager=prompt_manager)  # 初始化导航代理
    traj = nav_agent.rollout(instruction)  # 调用主导航逻辑
    print("Navigation result:")
    print(traj)