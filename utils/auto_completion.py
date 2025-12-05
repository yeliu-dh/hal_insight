import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import time

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import precision_score, recall_score, f1_score, multilabel_confusion_matrix
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from kneed import KneeLocator

import umap
import hdbscan
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt



import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import random
import os, sys


# my utils
from utils.upload import missing_data_warning
from utils.preprocess import load_external_json
from utils.preprocess import preprocess_text
from utils.preprocess import explode_by_col
from utils.plot import make_pie_chart


def split_axe(df):
    #dropna
    df_clean = df[(df["Axe"].notna())&(df['Axe']!='nan')].copy()#去掉nan
    print(f"len df notna : {len(df)} => {len(df_clean)}")
    # print(df_clean['Axe'].value_counts())

    axe_map = {
        "1": 0,
        "2": 1,
        "3": 2,
        "4": 3
    }

    def parse_axes(axe_str):
        # 确保是字符串
        if pd.isna(axe_str):
            return [0,0,0,0]
        # 拆分并 strip
        labels = str(axe_str).split(";")
        labels = [s.strip() for s in labels]
        
        # 创建 one-hot
        vec = [0,0,0,0]
        for lbl in labels:
            if lbl in axe_map:
                vec[axe_map[lbl]] = 1
        return vec

    df_clean["axes_vec"] = df_clean["Axe"].apply(parse_axes)
    df_clean[['axe1','axe2','axe3','axe4']] = pd.DataFrame(df_clean['axes_vec'].tolist(), index=df_clean.index)
    # df_clean.head()

    # df_clean['original_axe']=df_clean['Axe']
    # df_clean=df_clean.explode("Axe")
    # print(f"df exploded : {len(df_clean)}\n"
    #       f"{df_clean['Axe'].value_counts()}")

    return df_clean


def group_text(df, cols, new_col='col_text'):
    """
    将指定的列拼接成一个新的文本列。

    参数:
    df: pd.DataFrame
    cols: list, 需要拼接的列名
    new_col: str, 新生成列的名称

    返回:
    df: 添加了新列的 DataFrame
    """
    def safe_get(val):
        return "" if pd.isna(val) else str(val)

    df[new_col] = df[cols].apply(lambda row: " ".join(safe_get(row[col]) for col in cols), axis=1)
    
    print(f"ALL text NA counts: {df[new_col].isna().value_counts(dropna=False)}\n")
    return df



def emb_text(df, model, col_text, col_emb, pq_path):

    start_time=time.time()
    texts = df[col_text].astype(str).tolist()

    emb = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    df[col_emb] = list(emb)

    df.to_parquet(pq_path, index=False)
    end_time=time.time()
    print(f"[SAVE] emd saved to {pq_path} : {end_time-start_time:.2f} sec!")
    return df




def get_best_n_clusters(df, col_emb='embedding', max_k=5):
    
    X = df[col_emb].tolist()  # 转为列表形式，确保可fit
    wcss = []
    K = range(1, max_k + 1)

    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        wcss.append(kmeans.inertia_)

    # 自动寻找肘部点
    kneedle = KneeLocator(K, wcss, curve="convex", direction="decreasing")
    best_n_clusters = kneedle.knee

    # 绘图
    plt.plot(K, wcss, 'bo-')
    if best_n_clusters:
        plt.axvline(x=best_n_clusters, color='r', linestyle='--', label=f'Elbow at k={best_n_clusters}')
    plt.xlabel('Number of clusters k')
    plt.ylabel('WCSS')
    plt.title('Elbow Method for Optimal k')
    plt.legend()
    plt.show()

    # centroids = kmeans.cluster_centers_
    if len(df)<=50:
        best_n_clusters=1

    print(f"{len(df)} texts => best_n_clusters :{best_n_clusters}")
    
    return best_n_clusters









def kmeans_2Dpca(df,best_n_clusters, col_emb="embedding"):
    #------------------KMeans---------------------------
    X = np.vstack(df[col_emb].values)

    kmeans = KMeans(n_clusters=best_n_clusters)
    labels = kmeans.fit_predict(X)

    df['cluster']=labels
    print(f"DISTRI clusters :{df.cluster.value_counts()}")
        
    sil_score = silhouette_score(X, labels, metric='euclidean')
    print("Silhouette:", sil_score)
    
   
    # -------------按照cluster着色：PCA plot--------------------
    pca = PCA(n_components=2)
    X_2d = pca.fit_transform(X)

    df['x'] = X_2d[:, 0]
    df['y'] = X_2d[:, 1]

    # ---------------------------
    # 画 scatterplot
    # ---------------------------
    plt.figure(figsize=(8, 6))
    plt.scatter(
        df['x'], df['y'],
        c=df['cluster'],    # 用簇编号上色
        cmap='tab10',
        s=30
    )
    plt.title(f"KMeans clustering visualization (PCA 2D)")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.colorbar(label='Cluster')
    plt.show()

    return 










def mlp_multilabels(X_train,X_val,y_train, y_val, batch_size=32,dropout=0.5,n_epochs = 30, model_path="../model/best_mlp.pt"):
    import pandas as pd
    import numpy as np
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import f1_score
    import random
    import os, sys

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    #固定种子
    seed = 42
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # #优化1：weight for BCE loss
    # # y_train 是二值矩阵 [N,4]
    # label_counts = y_train.sum(axis=0)
    # total = len(y_train)
    # # pos_weight = (total - pos) / pos
    # pos_weight = torch.tensor((total - label_counts) / label_counts, dtype=torch.float32).to(device)
    # print("pos_weight:", pos_weight)

    # -------------------------------
    # 2️⃣ Dataset & DataLoader
    # -------------------------------
    class MultiLabelDataset(Dataset):
        def __init__(self, X, y):
            #保证类型为 float32
            self.X = torch.from_numpy(X).float()
            self.y = torch.from_numpy(y).float()
            print("Dataset X shape:", self.X.shape, "y shape:", self.y.shape)  # 加这个检查

        def __len__(self):
            return len(self.X)
        def __getitem__(self, idx):
            return self.X[idx], self.y[idx]

    val_dataset   = MultiLabelDataset(X_val, y_val)
    val_loader   = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    train_dataset = MultiLabelDataset(X_train, y_train)  # X_train [N, 1024], y_train [N, 4]
    # train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)


    ## 给少类别重采样：oversampling
    from torch.utils.data import DataLoader, WeightedRandomSampler
    class_counts = y_train.sum(axis=0)
    # # OPT0: 每个样本的 weight = 1 / class count
    # class_weights = 1.0 / class_counts
    # sample_weights = (y_train * class_weights).sum(axis=1)
    
    #小类别很少，但不想限制最大值 → 用 epsilon 平滑。
    # 不想让类别权重超过某个上限 → 用 np.clip
    ## OPT1 
    # class_weights = 1.0 / class_counts
    # # 限制 class_weights 范围，避免过大
    # class_weights = np.clip(class_weights, a_min=None, a_max=5.0)  
    # sample_weights = (y_train * class_weights).sum(axis=1)
    # sample_weights = np.clip(sample_weights, a_min=0.1, a_max=5.0)
    
    # OPT2 :epsilon+clip
    epsilon = 1e-2
    class_weights = 1.0 / (class_counts + epsilon)
    sample_weights = (y_train * class_weights).sum(axis=1) 
    sample_weights = np.clip(sample_weights, 0.001, 5.0)

    #将w加入sampler
    sampler = WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.float),
        num_samples=len(sample_weights),
        replacement=True
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, sampler=sampler)

    # for batch_X, batch_y in train_loader:
    #     print(batch_X.shape, batch_y.shape)  # 应该是 [32, 1024], [32, 4]

    # -------------------------------
    # 3️⃣ 定义 MLP 模型
    # -------------------------------

    # 优化二：更强 MLP + dropout（避免过拟合）
    class MultiLabelMLP(torch.nn.Module):
        def __init__(self, input_dim, hidden=512, dropout=dropout):
            super().__init__()
            self.net = torch.nn.Sequential(
                torch.nn.Linear(input_dim, hidden),
                torch.nn.ReLU(),
                torch.nn.Dropout(dropout),

                torch.nn.Linear(hidden, hidden//2),
                torch.nn.ReLU(),
                torch.nn.Dropout(dropout),

                torch.nn.Linear(hidden//2, 4)
            )

        def forward(self, x):
            return self.net(x)# logits


    # -------------------------------
    # 4️⃣ 初始化模型、优化器、loss
    # -------------------------------
    # device = "cuda" if torch.cuda.is_available() else "cpu"
    model = MultiLabelMLP(input_dim=X_train.shape[1]).to(device)

    #优化三：weight decay
    # optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)

    # criterion = nn.BCEWithLogitsLoss()  # 多标签分类
    # criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    #优化七 ：让模型不要极端预测 0/1：
    # criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight, reduction="mean", label_smoothing=0.1)

    # #优化五:
    class FocalLoss(nn.Module):
        def __init__(self, alpha=0.25, gamma=2):
            super().__init__()
            self.alpha = alpha
            self.gamma = gamma
            self.bce = nn.BCEWithLogitsLoss(reduction='none')

        def forward(self, logits, targets):
            bce_loss = self.bce(logits, targets)
            probs = torch.sigmoid(logits)
            pt = probs * targets + (1 - probs) * (1 - targets)
            focal = self.alpha * (1 - pt) ** self.gamma * bce_loss
            return focal.mean()
    criterion = FocalLoss(alpha=0.5, gamma=2)


    #优化四:
    # -------- early stopping ----------
    best_f1 = 0
    patience = 3
    stops = 0

    for epoch in range(n_epochs):
        # ---------------- train ----------------
        model.train()
        train_loss = 0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            batch_y = batch_y.float()  # 冗余，但保险

            optimizer.zero_grad()
            logits = model(batch_X)
            loss = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch_X.size(0)

        train_loss /= len(train_loader.dataset)

        # ---------------- validation ----------------
        model.eval()
        val_loss = 0
        all_probs, all_labels = [], []
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                logits = model(batch_X)
                loss = criterion(logits, batch_y)
                val_loss += loss.item() * batch_X.size(0)

                probs = torch.sigmoid(logits).cpu().numpy()
                all_probs.append(probs)
                all_labels.append(batch_y.cpu().numpy())

        val_loss /= len(val_loader.dataset)
        all_probs = np.vstack(all_probs)        # ← 这里是验证集所有概率
        all_labels = np.vstack(all_labels)      # ← 这里是验证集所有真实标签
        
        # ----- Per-class threshold tuning -----
        best_t_per_class = []
        for c in range(all_labels.shape[1]):
            best_f1, best_t = 0, 0.5
            for t in np.arange(0.05, 0.80, 0.01):
                preds_t = (all_probs[:, c] >= t).astype(int)
                # f1 = f1_score(all_labels[:, c], preds_t)
                # f1_score 对只有 0 或 1 的类可能报 warning，可加 zero_division=0
                f1 = f1_score(all_labels[:, c], preds_t, zero_division=0)

                if f1 > best_f1:
                    best_f1, best_t = f1, t
            best_t_per_class.append(best_t)
        #在每一轮打印的 best_t_per_class 只是用来观察当前 epoch 模型在不同阈值下的表现趋势，它 并没有被实际用于训练或梯度计算。
        #在prediction才会用到！
        # print("Best thresholds per class:", best_t_per_class)


        # 默认阈值 0.4；后续会改成 best_t_per_class
        # preds_bin = (all_probs >= 0.4).astype(int)
        # f1_macro = f1_score(all_labels, preds_bin, average='macro')
        preds_bin = np.zeros_like(all_probs)
        for c, t in enumerate(best_t_per_class):
            preds_bin[:, c] = (all_probs[:, c] >= t).astype(int)
        f1_macro = f1_score(all_labels, preds_bin, average='macro')

        print(f"Epoch {epoch+1}/{n_epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | F1_macro: {f1_macro:.4f}\n")


        # 默认阈值 0.4；后续再进行 per-class tuning
        # preds_bin = (all_probs >= 0.4).astype(int)
        # f1_micro = f1_score(all_labels, preds_bin, average='macro')
        # print(f"Epoch {epoch+1}/{n_epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | F1_micro: {f1_micro:.4f}")

        # -------- early stopping ----------
        if f1_macro > best_f1:
            best_f1 = f1_macro
            stops = 0
            torch.save(model.state_dict(), model_path)
        else:
            stops += 1
            if stops >= patience:
                print("Early stopping triggered.")
                break
    return model, best_t_per_class










def predict_by_model(text_embeddings, model, threshold=0.4):
    """
    text_embeddings: numpy array [N, dim]
    threshold: float or list/np.array of length num_classes
    returns: binary multi-label predictions [N, num_classes]
    """
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    X = torch.from_numpy(text_embeddings.astype(np.float32)).to(device)
    with torch.no_grad():
        logits = model(X)
        probs = torch.sigmoid(logits).cpu().numpy()
    
    # 支持 per-class 阈值
    threshold = np.array(threshold)
    if threshold.ndim == 0:
        # 单个阈值，应用于所有类别
        preds = (probs >= threshold).astype(int)
    else:
        # 每列使用不同阈值
        preds = (probs >= threshold[None, :]).astype(int)
    
    return preds, probs

def evaluate_model(preds_val, y_val):
    import numpy as np
    from sklearn.metrics import (
        f1_score, precision_score, recall_score,
        classification_report, hamming_loss,
        accuracy_score, confusion_matrix,
        ConfusionMatrixDisplay
        )
    import matplotlib.pyplot as plt
    
    # overall metrics
    f1_micro = f1_score(y_val, preds_val, average='micro')
    f1_macro = f1_score(y_val, preds_val, average='macro')
    precision_micro = precision_score(y_val, preds_val, average='micro')
    recall_micro = recall_score(y_val, preds_val, average='micro')

    hamming = hamming_loss(y_val, preds_val)
    subset_acc = accuracy_score(y_val, preds_val)  # exact match

    print("Micro  F1: ", f1_micro)
    print("Macro  F1: ", f1_macro)
    print("Micro Precision:", precision_micro)
    print("Micro Recall:", recall_micro)
    print("Hamming loss:", hamming)
    print("Subset exact match:", subset_acc)

    # per-class report
    print("\nPer-class classification report:")
    print(classification_report(y_val, preds_val, target_names=['axe1','axe2','axe3','axe4']))




    # ConfusionMatrixDisplay
    n_classes = y_val.shape[1]
    class_names = ['axe1','axe2','axe3','axe4']

    fig, axes = plt.subplots(1, n_classes, figsize=(4*n_classes, 4))  # 1 行 4 列

    for c in range(n_classes):
        cm = confusion_matrix(y_val[:, c], preds_val[:, c])
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0,1])
        disp.plot(ax=axes[c], cmap='Blues', colorbar=False)  # 指定当前轴
        axes[c].set_title(class_names[c])

    plt.tight_layout()
    plt.show()
    return 










def auto_completion_by_sim(df, model_name, threshold=0.4):
    
    #=============================step1：clean text=================================
    def safe_get(val):
        return "" if pd.isna(val) else str(val)

    df["clean_text"] = df.apply(
        lambda r: preprocess_text(
            safe_get(r["title_s"]) + " " +
            safe_get(r["keyword_s"]) + " " +
            safe_get(r["abstract_s"]),
            user_stopwords=None,
            lang=r['language_s']
        ),
        axis=1
    )
     
    #=============================step2:embedding==================================
    # with st.spinner("Embedding..."):
    model = SentenceTransformer(model_name)
    df["embedding"] = df["clean_text"].apply(lambda x: model.encode(x))


    # =====================step3 :prediction by similarity between embeddings=====================

    df["original_axe"] = df["Axe"]#保留原值
    # missing_data_warning(df, col='Axe', show_distribution=False)

    df=explode_by_col(df, col="Axe")#fillna('nan')#原axe已经被exploded
    df["Axe"] = df["Axe"].replace("nan", np.nan)
    

    #计算每一个主题的平均向量：
    axe_means = df[df["Axe"].notna()].groupby("Axe")["embedding"].apply(
        lambda emb: np.mean(list(emb), axis=0)
    )

    def predict_axes_for_row(row, threshold):
        if pd.isna(row["Axe"]):#若无axe
            sims = {axe: cosine_similarity([row["embedding"]], [axe_means[axe]])[0][0] for axe in axe_means.index}
            # 返回匹配的 Axe
            return [axe for axe, score in sims.items() if score >= threshold]
        else:
            return [row["Axe"]]

    df["predicted_axe"] = df.apply(lambda row: predict_axes_for_row(row, threshold), axis=1)

    # print(df.Axe.value_counts(dropna=False),'\n')
    # print(df.predicted_axe.value_counts(dropna=False),'\n')
    # missing_data_warning(df, col='original_axe', show_distribution=False)
    #一篇可能有多个axes超过了 threshold
    df_exploded = df.explode("predicted_axe")
    
    display(df_exploded[["halId_s","docType_s","authFullName_s","title_s","keyword_s","abstract_s","clean_text","original_axe","predicted_axe"]])


    # #==========================快速画图=======================
    # def quick_pie(df,col):
    #     counts=df[col].fillna('NaN').value_counts()
    #     cmap = cm.get_cmap('viridis')
    #     colors = [cmap(i / len(counts)) for i in range(len(counts))]

    #     fig, ax = plt.subplots(figsize=(6,6))
    #     ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90, colors=colors)
    #     ax.set_title(col)
    #     return fig
    
    # def show_pies(fig1, fig2):
    #     st.header("***Comparasion entrte les vrais axes et axes prédits***")
    #     cols=st.columns(2)
    #     with cols[0]:
    #         st.pyplot(fig1)     
    #     with cols[1]:
    #         st.pyplot(fig2)
    #     return 
        
    # if "fig1" not in st.session_state and "fig1" not in st.session_state: 
    #     fig1=quick_pie(df,col='Axe')
    #     fig2=quick_pie(df_exploded, col='predicted_axe')
    #     st.session_state.fig1=fig1
    #     st.session_state.fig2=fig2
    #     show_pies(fig1, fig2)      

    # else :
    #     show_pies(st.session_state.fig1, st.session_state.fig2)    
    
    ###点击总结摘要按钮之后也可以保留

    #=======================step 4: evaluate by metrics================================ 
    
    df_valid = df[df["Axe"].notna()].drop_duplicates(subset='halId_s')

    # 所有可能的Axe标签
    unique_labels = sorted(df_valid["Axe"].dropna().unique().tolist())
    #['1', '2', '3']

    # 转为多标签二进制格式
    def to_multilabel(row):# 把axe数字变成binary 2==[010]
        y_true = [int(x in row["original_axe"]) for x in unique_labels]
        y_pred = [int(x in row["predicted_axe"]) for x in unique_labels]
        return y_true, y_pred

    y_true, y_pred = zip(*df_valid.apply(to_multilabel, axis=1))
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    

    st.markdown("***L'accuracy de la prediction :***\n")
    # 微平均和宏平均的precision/recall/f1
    st.write("Precision (micro):", precision_score(y_true, y_pred, average="micro"))
    st.write("Recall (micro):", recall_score(y_true, y_pred, average="micro"))
    st.write("F1 (micro):", f1_score(y_true, y_pred, average="micro"))

    st.write("\nPrecision (macro):", precision_score(y_true, y_pred, average="macro"))
    st.write("Recall (macro):", recall_score(y_true, y_pred, average="macro"))
    st.write("F1 (macro):", f1_score(y_true, y_pred, average="macro"))

    ## precision==1,说明pred中的结果都在original中（pred都是正确的），但是还有一部分没有预测出来（还有部分标签没被包含!）
    return df_exploded



    
