import json
from pathlib import Path
import pandas as pd
import re

# 项目根目录
BASE_DIR = Path(__file__).parent.parent # 当前文件所在的文件夹路径
MAPPING_DIR = BASE_DIR / "mappings"

def load_mapping_json(file_name: str):
    """加载 mappings 文件夹中的 JSON 字典"""
    file_path = MAPPING_DIR / file_name
    if not file_path.exists():
        raise FileNotFoundError(f"{file_name} not found in {MAPPING_DIR}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def map_domains(codes_str:str=None, map:dict=DOMAIN_MAP):
                """
                搜索结果是代码，对代码进行映射和清洗
                """
                if not codes_str: return ""
                codes = codes_str.split(";")
                mapped = []
                for code in codes:
                    code_clean = re.sub(r"^\d+\.", "", code.strip())
                    mapped.append(DOMAIN_MAP.get(code_clean, code_clean))
                return "; ".join(mapped)


# # 如果需要专门函数，可以写多个，方便调用
# def get_journal_rankings():
#     return load_json("ranking.json")

# def get_domain_map():
#     return load_json("domain_map.json")

# def get_lang_map():
#     return load_json("lang_map.json")
