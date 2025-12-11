# Statistiques de l'entraînement
👉Consulter [Entraînement des modèles (notebook)](httpsgithub.comyeliu-dhhal_insightblobmainnotebookstest_multiaxe_3emb.ipynb)

- Tous les 2734 articles de type art, ouv, cov et comm d'IRG jusqu'au Dec.2025
- Parmi eux, le titre, les mots-clés, le résumé de 2117 articles sont séparément embeddés par le modèle 'BAAIbge-m3' (environ 30 mins)
- Entrainer un MLP avec 5139 embeddings
- Méthodes d'amélioration  pondération et échantillonnage des classes, Adam optimizer, focal loss, early stopping
- Enregistrer le meilleur F1 et le seuil correspondant

## Résultats du modèle MLP

 Metric  Value 
 ---  --- 
 Micro F1  0.7794 
 Macro F1  0.6336 
 Micro Precision  0.8031 
 Micro Recall  0.7570 

### Per-class Classification Report

 Class  Precision  Recall  F1-score  Support 
 ---  ---  ---  ---  --- 
 axe1  0.76  0.78  0.77  299 
 axe2  0.58  0.77  0.66  86 
 axe3  0.89  0.77  0.83  615 
 axe4  0.32  0.24  0.27  29 

PB  l'axe 4 est très sous-présent  
Solution  entraîner d'autres modèles linéaires ('Logistic Regression' et 'LightGBM') pour l'axe 4  
Résultat final 

 Metric  Value 
 ---  --- 
 Micro F1  0.7879 
 Macro F1  0.7001 
 Micro Precision  0.7701 
 Micro Recall  0.8061 

 Class  Precision  Recall  F1-score  Support 
 ---  ---  ---  ---  --- 
 axe1  0.78  0.76  0.77  304 
 axe2  0.77  0.58  0.66  113 
 axe3  0.77  0.89  0.83  531 
 axe4  0.67  0.45  0.54  22 

![Matrice de confusion](external_dataclf_classification_matrix.png)
