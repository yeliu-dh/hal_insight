import streamlit as st
import pandas as pd
import sys
import os
import json
from pathlib import Path

#my utils :

# from utils.preprocess import explode_by_col# preprocess用到了这里的load_exetrnal_json, 无法互相循环导入包



def save_as_json(data, path):
    with open (path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)   
    print(f"data saved in {path}!")
    return 

# BASE_DIR = Path(__file__).parent.parent # 当前文件的上上级文件路径==HAL_INSIGHT

def load_external_json(file_path):
    BASE_DIR = Path(__file__).parent.parent # 当前文件的上上级文件路径
    file_path = BASE_DIR / file_path
    # st.write(file_path)
    if not file_path.exists():
        raise FileNotFoundError("NO FILE FOUND!")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)



def explode_by_col(df, col="Axe"):
    """"
    空值填nan，
    多值按照，/；分割成list
    =>在某一col上explode；
    检查notna
    """
    df = df.copy()
    df[col] = df[col].fillna('nan').astype(str).str.split("[,;]") # axe中有nan所以type:objet，先变成str
    df = df.explode(col)
    df[col] = df[col].str.strip()
    return df[df[col].notna() & (df[col] != "")]

def missing_data_warning(df, col=None, map:dict=None, show_distribution=False):
    if col not in df.columns:
        st.warning (f"⚠ {col} n'est pas trouvé dans la base de données !")
    else:        
        if map:
            col_readable= map.get(col,col)
        else :
            col_readable=col
        
        # 是否有缺失：
        nb_manquant=df[col].isna().sum()
        if nb_manquant==0:
            str_manquant=f"**{col_readable}** sont disponibles dans toutes les lignes.\n\n"
        else :
            str_manquant=f"Les **{col_readable}** sont manquants dans {df[col].isna().sum()} ({df[col].isna().sum()*100/len(df):.2f}%) articles! \n\n"
        st.markdown(f"[INFO] {str_manquant}")

        # 是否显示分布
        if show_distribution:
            df=explode_by_col(df, col=col)
            dist = df[col].value_counts(normalize=True)* 100
            dist_str = "; ".join([f"{k}: {v:.1f}%" for k, v in dist.items()])
            st.write(f"{dist_str}")

        # else :
        #     dist_str=" "
   
        # st.info (f"**Values**: {str_manquant} \n\n"
        #          f"Distribution : {dist_str}")
        # st.markdown(f"**Values :** {str_manquant}\n\n**Distribution :**\n{dist_str}")#mkd更好控制分行和格式

    return



def data_uploader(key="uploaded_df"):
    """
    通用 CSV 上传器:
    - 优先显示 session_state 中已有数据 (搜索结果 or 上传)
    - 用户可随时上传新文件覆盖
    - 自动区分数据来源
    """
    st.subheader("📂 Importer vos données")

    uploaded_file = st.file_uploader(
        "Charger / Changer un fichier", 
        type=["csv", "xlsx"], 
        key=f"{key}_file"
    )

    # 用户主动上传 -> 覆盖 session_state 并打上来源
    if uploaded_file is not None:# 读成df，都可以同样处理！
        try :
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            else:
                df = pd.read_excel(uploaded_file)
            st.session_state[key] = df
            st.session_state[f"{key}_source"] = "upload"
        except Exception as e:
            st.error(f"⚠ {e}")

    
    # 如果uploaded df存在,无论是用户刚上传，还是通过搜索保存的
    if key in st.session_state and st.session_state[key] is not None:
        source = st.session_state.get(f"{key}_source", "unknown")# 如果source不存在，则显示unk

        source_label = {
            "search": " résultats de recherche",
            "upload": " fichier uploadé",
            "unknown": "source"
        }.get(source, "source")

        st.success(f" Data importé | Source :{source_label} | {len(st.session_state[key])} lignes au total.")
        st.dataframe(st.session_state[key].head())
    else:
        st.info("Aucun fichier importé. Veuillez chercher des articles ou charger un CSV.")

