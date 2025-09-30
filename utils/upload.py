import streamlit as st
import pandas as pd

def csv_uploader(key="uploaded_df"):
    """
    通用 CSV 上传器:
    - 优先显示 session_state 中已有数据 (搜索结果 or 上传)
    - 用户可随时上传新文件覆盖
    - 自动区分数据来源
    """
    st.subheader("📂 Importer vos données")

    uploaded_file = st.file_uploader(
        "Charger / Changer un fichier (.xlsx/.csv)", 
        type=["csv", "xlsx"], 
        key=f"{key}_file"
    )

    # 用户主动上传 -> 覆盖 session_state 并打上来源
    if uploaded_file is not None:# 读成df，都可以同样处理！
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, encoding="utf-8")
        else:
            df = pd.read_excel(uploaded_file)
        st.session_state[key] = df
        st.session_state[f"{key}_source"] = "upload"


    # 如果uploaded df存在,无论是用户刚上传，还是通过搜索保存的
    if key in st.session_state and st.session_state[key] is not None:
        source = st.session_state.get(f"{key}_source", "unknown")# 如果source不存在，则显示unk

        source_label = {
            "search": " 🔎 Résultats de recherche",
            "upload": "📂 Fichier uploadé",
            "unknown": "❓ Source inconnue"
        }.get(source, "❓ Source inconnue")

        st.success(f"✅ data chargé |{source_label} : {len(st.session_state[key])} lignes au total.")
        st.dataframe(st.session_state[key].head())
    else:
        st.info("📭 Aucun fichier importé. Veuillez chercher des articles ou charger un CSV.")




# def csv_uploader(key="uploaded_df"):
#     """
#     通用 CSV 上传器:
#     - 优先使用 session_state 中已有 df（来自搜索页或之前上传）
#     - 用户可以随时上传新 CSV 覆盖
#     """
#     st.subheader("📂 Importer vos données")

#     uploaded_file = st.file_uploader(
#         "Charger / Changer un fichier CSV", 
#         type=["csv"], 
#         key=f"{key}_file"
#     )

#     # 如果用户主动上传 -> 覆盖 session_state
#     if uploaded_file is not None:
#         st.session_state[key] = pd.read_csv(uploaded_file)
#         st.success(f"✅ CSV chargé manu: {len(st.session_state[key])} lignes au total.")

#     # 优先显示已有数据（可能来自搜索页）
#     if key in st.session_state and st.session_state[key] is not None:
#         st.success(f"✅ CSV chargé : {len(st.session_state[key])} lignes au total.")
#         st.dataframe(st.session_state[key].head())
#     else:
#         st.info("⚠ Aucun fichier importé. Veuillez chercher des articles ou charger un CSV.")




# def csv_uploader(key="uploaded_df"):
#     """
#     通用 CSV 上传器:
#     - 如果 session_state 中已有 df，则显示 ✅ 状态和数据头
#     - 否则显示上传器
#     - 用户可以随时重新上传，更新 session_state
#     """
#     st.subheader("📂 Importer vos données")

#     uploaded_file = st.file_uploader(
#         "Charger / Changer un fichier CSV", 
#         type=["csv"], 
#         key=f"{key}_file"
#     )

#     if uploaded_file is not None:#存在df
#         st.session_state[key] = pd.read_csv(uploaded_file)

#     #再次判断,不是直接upload储存的,从session中提取已有数据
#     if key in st.session_state and st.session_state[key] is not None:
#         st.success(f"✅ CSV chargé : {len(st.session_state[key])} lignes au total.")
#         #apercu
#         st.dataframe(st.session_state[key].head())  # 显示前几行
