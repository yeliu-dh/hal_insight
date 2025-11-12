import json
from pathlib import Path
import pandas as pd
import re

# 项目根目录
BASE_DIR = Path(__file__).parent.parent # 当前文件的上上级文件路径
MAPPING_DIR = BASE_DIR / "mappings"


# def map_axe(df, col):
#     if col=="Axe":
#         # 定义映射字典
#         axe_map = {
#             "1": "Performances et responsabilités",
#             "2": "Société de services et services à la société",
#             "3": "Innovations; transformations et résistances organisationnelles et sociétales",
#             "4": "Ouvrages pédagogiques"
#         }

#         # 拆分、映射、再合并
#         df['Axe'] = (
#             df['Axe']
#             .fillna('nan')
#             .astype(str)
#             .str.split(';')                  # 拆分多个值
#             .apply(lambda lst: [axe_map.get(x.strip(), x.strip()) for x in lst])  # 映射
#             .apply(lambda lst: ';'.join(lst))  # 再合并成字符串
#         )
#     return df

