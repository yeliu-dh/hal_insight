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
    
def map_domains(codes_str:str=None, map:dict=None):
    """
    搜索结果是代码，对代码进行映射和清洗
    """
    if not isinstance(codes_str,str): 
        return None

    codes = codes_str.split(";")
    mapped = []

    for code in codes:
        code_clean = re.sub(r"^\d+\.", "", code.strip())
        mapped.append(map.get(code_clean, code_clean))
    
    return "; ".join(mapped)



# Axes thématiques (classification) d'IRG
# Code	    Nom de l'axe
# IRG_AXE1	Performances et responsabilités
# IRG_AXE2	Société de services et services à la société
# IRG_AXE3	Innovations, transformations et résistances organisationnelles et sociétales
# IRG_AXE4	Ouvrages pédagogiques

def transforme_axe(axe_str:str):
    if not isinstance(axe_str,str): #确保是str
        return None
    
    axe_str=axe_str.strip().lower()
    if axe_str and axe_str.startswith("irg_axe"):#以irg开头
        axe_label=axe_str[-1:]
    else :
        axe_label=axe_str
    return axe_label
    
def add_axe(df,axe_name='Axe'):
    """   
    把 classification_s 字段中的值"IRG_AXE1/2/3"，整理成字符串数字，列名改为Axe

    """
    df["classification_s"] = df["classification_s"].apply(transforme_axe)
    df=df.rename(columns={"classification_s":axe_name})
    return df




# # 如果需要专门函数，可以写多个，方便调用
# def get_journal_rankings():
#     return load_json("ranking.json")

# def get_domain_map():
#     return load_json("domain_map.json")

# def get_lang_map():
#     return load_json("lang_map.json")
