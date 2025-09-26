import streamlit as st

st.set_page_config(page_title="HAL Insight",page_icon="🛸", layout="wide")

st.title("🛸Accueil | HAL Insight")
st.markdown("""
Bienvenu-e sur le tableau de bord HAL Insight !

🔎 Ici vous pouvez explorer :
- Récupérer les articles sur HAL
- Générer des plots :
    * Aperçu global des publications scientifiques
    * Répartitions par pays, langue, domaine,etc.
    * Tendances temporelles
    * Nuage des mots clés
    * Réseaux de cooccurrence
            
en consultant la barre latéral! 
""")

st.markdown("""
Pour tout problème ou question concernant l'utilisation de l'application,  
veuillez me contacter : ye.liu@chartes.psl.eu
""")


#-------------update requirements-----------
# pipreqs hal_insight --force --savepath hal_insight/requirements.txt


