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