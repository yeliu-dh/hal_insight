import json
from pathlib import Path
import pandas as pd
import re

# # 项目根目录
# BASE_DIR = Path(__file__).parent.parent # 当前文件的上上级文件路径
# MAPPING_DIR = BASE_DIR / "mappings"

# def load_mapping_json(file_name: str):
#     """
#     加载 mappings 文件夹中的 JSON 字典
#     """
#     file_path = MAPPING_DIR / file_name
#     if not file_path.exists():
#         raise FileNotFoundError(f"{file_name} not found in {MAPPING_DIR}")
#     with open(file_path, "r", encoding="utf-8") as f:
#         return json.load(f)


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

def extract_irg_axes(text):
    """
    把 classification_s 字段中的值:
        IRG_AXE1
        IRG_axe1
        IRG_AXE 3
        IRG_AXE1IRG_AXE3
        IRG_AXE2 – Sociétés de services et services à la société (A society of services and services to society)
        Axe_1            

    re.findall(pattern, text)
    \s* 允许space, *表示0或多个！

    (\d+):
        \d是数字，+表示模式重复多次，()为捕获组单位，只取出()内的内容

    """
    if pd.isna(text):
        return None
    text=text.strip().lower()
        
    # 找出所有 irg_axe后面的数字
    matches = re.findall(r"axe\s*(\d+)", text)
    if matches:
        # 用分号拼接
        return "; ".join(matches)
    return None


    
def add_axe(df,axe_name='Axe'):
    """   
    整理成字符串数字，列名改为Axe
    """
    df["classification_s"] = df["classification_s"].apply(extract_irg_axes)
    df=df.rename(columns={"classification_s":axe_name})
    return df


def map_axe(df, col):
    if col=="Axe":
        # 定义映射字典
        axe_map = {
            "1": "Performances et responsabilités",
            "2": "Société de services et services à la société",
            "3": "Innovations, transformations et résistances organisationnelles et sociétales",
            "4": "Ouvrages pédagogiques"
        }

        # 拆分、映射、再合并
        df['Axe'] = (
            df['Axe']
            .fillna('nan')
            .astype(str)
            .str.split(';')                  # 拆分多个值
            .apply(lambda lst: [axe_map.get(x.strip(), x.strip()) for x in lst])  # 映射
            .apply(lambda lst: ';'.join(lst))  # 再合并成字符串
        )
    return df

