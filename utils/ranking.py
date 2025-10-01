import json
import pandas as pd
from typing import Dict, Any #Python 类型注解模块 typing 里的类型提示
from pathlib import Path
import unicodedata
import re
from rapidfuzz import process


MAPPING_DIR = Path(__file__).parent.parent / "mappings"
RANKING_FILE = MAPPING_DIR / "classement.json"

# --------------------------
# 字符串归一化
# --------------------------
def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]", "", text)  # 去掉标点
    return text


# def normalize(text: str) -> str:
     
#     text = text.lower().strip()
#     text = unicodedata.normalize("NFKD", text)
#     text = "".join(c for c in text if not unicodedata.combining(c))
#     text = re.sub(r"[^\w\s]", "", text)
#     return text

def parse_php_txt(input_file: str) -> dict:
    mapping = {}
    with open(input_file, "r", encoding="utf-8") as f:
        i=0
        for line in f:            
            line = line.strip()
            if "=>" in line:
                i+=1
                left, right = line.split("=>", 1)
                journal = left.strip().strip('"')
                rank = right.strip().strip('"').strip(',;"')
                mapping[journal] = rank
        print(f'{i} correspondances du classement!')
        print(f"{len(mapping)} enregistrés dans le dict")
        #有很多重复key
    return mapping

def save_mapping(mapping: dict, output_file: str = RANKING_FILE):

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存到 {output_file}")


# --------------------------
# 模糊匹配期刊名
# --------------------------
def fuzzy_lookup(journal_name: str, mapping: dict, cutoff: int = 85) -> str:
    """
    返回最匹配的期刊排名，如果匹配不到则返回 None
    """
    if not journal_name or not mapping:
        return None

    normalized_mapping_keys = {normalize(k): k for k in mapping.keys()}
    norm_name = normalize(journal_name)

    # 找最接近的 key
    best_match = process.extractOne(norm_name, list(normalized_mapping_keys.keys()))
    if best_match and best_match[1] >= cutoff:
        original_key = normalized_mapping_keys[best_match[0]]
        return mapping[original_key]
    return None



def add_classement_col(
    df: pd.DataFrame,
    journal_col: str = "journalTitle_s",
    map: Dict[str, Any] = None, ## 表示 mapping 是一个字典，key 是字符串，value 可以是任意类型  
    cl_name: str = 'Cl. FNEGE',
    cutoff: int = 85
) -> pd.DataFrame:
    col_cl = df[journal_col].apply(lambda x: fuzzy_lookup(x, mapping, cutoff=cutoff))
    
    # 找到 journalTitle_s 的列索引
    idx = df.columns.get_loc(journal_col)

    # 插入列到 journalTitle_s 后面
    df.insert(loc=idx+1, column=cl_name, value=col_cl)
    return df



# def add_classement(df: pd.DataFrame, journal_col: str = "journalTitle_s", mapping : dict, cl_name:str='Cl. FNEGE', cutoff: int = 85) -> pd.DataFrame:
#     col_cl = df[journal_col].apply(lambda x: fuzzy_lookup(x, mapping, cutoff=cutoff))
    
#     # 找到 journalTitle_s 的列索引
#     idx = df.columns.get_loc(journal_col)

#     # 插入列到 journalTitle_s 后面
#     df.insert(loc=idx+1, column=cl_name, value=col_cl)
#     return df



# -----------------------------
# python hal_insight\utils\ranking.py
# -----------------------------
if __name__ == "__main__":
    input_file = Path(__file__).parent / "ExtractionHAL-revues-IRG.txt"  # 或者你 txt 的路径
    # input_file = Path(__file__).parent / "classement.txt"
    mapping = parse_php_txt(input_file)
    save_mapping(mapping)


