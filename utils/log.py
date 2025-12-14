import logging
from pathlib import Path


"""
level	用途
=====   ===================
DEBUG	详细信息，用于开发调试
INFO	程序正常运行状态信息
WARNING	可能的问题
ERROR	必须处理的错误
CRITICAL	程序无法继续

.log文件本身是纯文本文件（UTF-8）
默认的是mode="w" 覆盖


"""

def setup_logging(save_log=True, log_file="run.log"):
    handlers = [logging.StreamHandler()]
    if save_log:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=logging.INFO,#只写入INFO类
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=handlers
    )