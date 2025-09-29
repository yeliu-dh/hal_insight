import streamlit as st
import pandas as pd


def csv_uploader(key="uploaded_df"):
    """
    通用 CSV 上传器:
    - 如果 session_state 中已有 df，则显示 ✅ 状态和数据头
    - 否则显示上传器
    - 用户可以随时重新上传，更新 session_state
    """
    st.subheader("📂 Importer vos données")

    uploaded_file = st.file_uploader(
        "Charger / Changer un fichier CSV", 
        type=["csv"], 
        key=f"{key}_file"
    )

    if uploaded_file is not None:#存在df
        st.session_state[key] = pd.read_csv(uploaded_file)

    #再次判断,不是直接upload储存的,从session中提取已有数据
    if key in st.session_state and st.session_state[key] is not None:
        st.success("✅ CSV chargé : {len(st.session_state[key])} lignes au total.")
        #apercu
        st.dataframe(st.session_state[key].head())  # 显示前几行
