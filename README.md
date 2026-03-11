# Projet HAL INSIGHT pour l'IRG







## Utilisation en local (Windows)

### 1️⃣Premier lancement

**Prérequis :**
- Python 3.10 dans l'oridinateur!
La dernière version de 3.10.x préférable!
https://www.python.org/downloads/release/python-3100/

- VSCODE:
Choisir selon le système de votre ordinateur! 
https://code.visualstudio.com/download


**1) Télécharger le git**

-par clone (recommandé!) 

ouvrir le terminal(de vscode, par exemple), entrer dans un dossier où vous voulez mettre ce git

'git clone https://github.com/yeliu-dh/hal_insight.git'

entrer dans le git :

cd hal_insight


-Télécharger le git par zip

appuyer le bouton vert'Code', choisir 'download ZIP', unzip, obtenir un dossier 'hal_insight-main'

**2) Créer un environement virtuel**
 py -3.10 -m venv venv 

**3) installer les librairies nécessaires**

pip install -r requirements.txt

**4) Lancer streamlit en local:**

streamlit run home.py

**5) Cessez l'application**

Ctrl+c

---

### *️⃣Lancement régulier

**a) activer l'environement :**

ouvrir le termnial et tapper 'venv\Scripts\activate'

(attention à la direction de slash ! 

s'il y a un '(venv)' au début de la ligne, environement est activé!)


**b) activer l'app:**

tapper 'streamlit run home.py' 


### 🔃Mis à jour 
- dans le terminal
cd 'votre_path_à_git_HAL_INSIGHT'
git pull

- re-télécharger
télécharger le zip sur Github et répéter 'premier lancement'

