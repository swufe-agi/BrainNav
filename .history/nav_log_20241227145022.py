import logging
import os
import sys
import time
import math
from collections import OrderedDict

# 设置日志配置
log_file = 'navigation_log.txt'

# 创建日志记录器
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 创建文件处理器，确保日志追加而非覆盖
file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setLevel(logging.INFO)

# 设置日志输出格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 添加文件处理器到日志记录器
logger.addHandler(file_handler)

# Log writing function (保持原有功能)
def write_to_record_file(data, file_path, verbose=True):
    if verbose:
        print(data)
    with open(file_path, 'a') as record_file:
        record_file.write(data + '\n')


# Timer class for tracking time
class Timer:
    def __init__(self):
        self.cul = OrderedDict()
        self.start = {}
        self.iter = 0

    def reset(self):
        self.cul = OrderedDict()
        self.start = {}
        self.iter = 0

    def tic(self, key):
        self.start[key] = time.time()

    def toc(self, key):
        delta = time.time() - self.start[key]
        if key not in self.cul:
            self.cul[key] = delta
        else:
            self.cul[key] += delta

    def step(self):
        self.iter += 1

    def show(self):
        total = sum(self.cul.values())
        for key in self.cul:
            print(f"{key}, total time {self.cul[key]:.2f}, avg time {self.cul[key]*1./self.iter:.2f}, part of {self.cul[key]*1./total:.2f}")
        print(f"Average time per step: {total / self.iter:.2f}")

# Progress bar function
def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


# import logging
# import os
# import sys
# import time
# from collections import OrderedDict

# # 设置日志配置
# log_file = 'navigation_log.txt'

# # 创建日志记录器
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

# # 创建文件处理器，确保日志追加而非覆盖
# file_handler = logging.FileHandler(log_file, mode='a')
# file_handler.setLevel(logging.INFO)

# # 设置日志输出格式
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(formatter)

# # 添加文件处理器到日志记录器
# logger.addHandler(file_handler)

# # 重新定义 print 函数，将控制台输出也保存到日志文件
# class LoggerWriter:
#     """
#     A class that captures the output of print() and writes it to both console and log file.
#     """
#     def __init__(self, logger, level=logging.INFO):
#         self.logger = logger
#         self.level = level

#     def write(self, message):
#         """捕获 print 的输出并通过 logger 记录"""
#         if message != '\n':  # 忽略空行
#             self.logger.log(self.level, message.strip())  # 去掉多余的换行

#     def flush(self):
#         """确保任何缓存的输出都被写入"""
#         pass

# # 将 sys.stdout 重定向到 LoggerWriter 类实例
# sys.stdout = LoggerWriter(logger)

# # Log writing function (保持原有功能)
# def write_to_record_file(data, file_path, verbose=True):
#     """
#     将数据写入文件，并根据 verbose 参数决定是否在控制台打印日志。

#     :param data: 要写入的数据
#     :param file_path: 文件路径
#     :param verbose: 是否在控制台输出日志
#     """
#     if verbose:
#         print(data)  # 现在这会通过 logger 输出到控制台和日志文件
#     with open(file_path, 'a') as record_file:
#         record_file.write(data + '\n')
