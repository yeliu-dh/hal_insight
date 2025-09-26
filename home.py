import streamlit as st
from utils.upload import csv_uploader#

st.set_page_config(page_title="HAL Insight",page_icon="🛸", layout="wide")

st.title("🛸Accueil | HAL Insight")
st.markdown("""
Bienvenue sur le tableau de bord HAL Insight !

🔎 Ici vous pouvez explorer :
- Récupérer les articles sur HAL
- Vue d’ensemble des publications
- Tendances temporelles
- Répartitions par pays, langue, domaine, etc.
- Nuage des mots clés
- Réseaux de cooccurrence
- ......
""")

# 调用上传器（会自动处理已有/新上传）
csv_uploader()

if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
    df = st.session_state.uploaded_df.copy()
    st.write("### Aperçu des données", df.head())
    # 👉 这里接着做分析

else:
    st.warning("⚠️ Merci d’importer un fichier CSV pour continuer.")




#update requirements
# pipreqs hal_insight --force --savepath hal_insight/requirements.txt


