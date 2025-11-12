import json
import pandas as pd
from typing import Dict, Any #Python 类型注解模块 typing 里的类型提示
from pathlib import Path
import unicodedata
import re
from rapidfuzz import process

#output
MAPPING_DIR = Path(__file__).parent.parent / "mappings"
RANKING_FILE = MAPPING_DIR / "classement_fnege.json"
   

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
                rank = right.strip().strip('"').strip(',;"*')
                mapping[journal] = rank
        print(f'{i} correspondances du classement!')
        print(f"{len(mapping)} enregistrés dans le dict")
        #有很多重复key
    return mapping

def save_mapping(mapping: dict, output_file: str = RANKING_FILE):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存到 {output_file}")



# -----------------------------
# python hal_insight\utils\ranking.py
# -----------------------------

if __name__ == "__main__":
    #input
    # input_file = Path(__file__).parent / "ExtractionHAL-revues-IRG.txt"  # 或者你 txt 的路径
    input_file = Path(__file__).parent / "classement_fnege.txt"
    
    mapping = parse_php_txt(input_file)
    save_mapping(mapping,)


