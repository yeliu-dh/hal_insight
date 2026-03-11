# hal_insight/init_imports.py
import os, sys

# 项目根目录
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)  # 保证优先查找

# 清理旧的 utils 模块缓存（防止 Streamlit 热重载失败）
for k in list(sys.modules.keys()):
    if k.startswith("utils."):
        del sys.modules[k]

# 导入 utils 模块
from utils.HAL_search_api import fetch_hal_articles
from utils.mapping import load_mapping_json
from utils.mapping import map_domains
from utils.mapping import add_axe
from utils.ranking import add_classement_fnege


# 对外提供引用
__all__ = [
    "fetch_hal_articles",
    "load_mapping_json",
    "map_domains",
    "add_axe",
    "add_classement_fnege"
]