# projet HAL INSIGHT pour IRG

## Pages :








## Utilisation en local (Windows)

Ce guide explique comment exécuter l'application **HAL Insight** en local sur un ordinateur Windows.


**Prérequis : 2 INDISPENSABLES !**
- Python 3.10 dans l'oridinateur!
La dernière version de 3.10.x préférable!(Télécharger ici)[https://www.python.org/downloads/release/python-3100/] 

- VSCODE:
Choisir selon le système de votre ordinateur! (Télécharger ici)[https://code.visualstudio.com/download]


**1) Télécharger le git**
- appuyer le bouton vert'Code',choisir download ZIP, unzip => obtenir un dossier 'hal_insight-main'

- par git: bash clone https://github.com/yeliu-dh/hal_insight.git


**2) Ouvrir vscode, choisir ce folder**

**3) Ouvrir un noueauv terminal**
en cliquant au haut-gauche 'Terminal> New terminal'
voir au bas de la page: '(base) D:\Work\hal_insight-main'

**4) Créer un environement virtuel**
taper 'py -3.10 -m venv venv '

**5) installer les librairies nécessaires**
pip install -r requirements.txt
et vous patientez...

**6) Lancer streamlit en local:**
taper 'streamlit run home.py'

**7) Cessez l'application**
dans le termnial, taper 'Ctrl+c'.

---

**NB. Assurez vous chaque fois vous êtez dans le bon environement virtuel!**

Comment entrer dans ce environement ?

a) ouvrir le termnial

b) taper 'venv\Scripts\activate'

c) voir s'il y a un '(venv)' au début de la ligne.
