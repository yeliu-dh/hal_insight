# basic:
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import time, os, sys, importlib


# model 
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import precision_score, recall_score, f1_score, multilabel_confusion_matrix
from sklearn.metrics import classification_report, precision_recall_curve, confusion_matrix


# model:
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import random
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from lightgbm import LGBMClassifier
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
import lightgbm as lgb
import joblib
from sklearn.calibration import calibration_curve



# my utils
from utils.upload import missing_data_warning
from utils.preprocess import load_external_json
from utils.preprocess import preprocess_text
from utils.preprocess import explode_by_col
from utils.plot import make_pie_chart


# # clustering :
# from sklearn.cluster import KMeans
# from kneed import KneeLocator

# import umap
# import hdbscan
# from sklearn.cluster import KMeans
# from sklearn.metrics import silhouette_score
# from sklearn.decomposition import PCA
# import matplotlib.pyplot as plt

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








def parse_axes(axe_str):
    # map axe 字符到索引
    axe_map = {"1": 0, "2": 1, "3": 2, "4": 3}

    # 如果是 nan 或 "nan"，返回全 0
    if pd.isna(axe_str):
        return [0, 0, 0, 0]

    # 如果是 float/int → 转成整数再字符串化!!!
    if isinstance(axe_str, (float, int)):
        axe_str = str(int(axe_str))

    # 拆分并 strip
    labels = [s.strip() for s in str(axe_str).split(";")]
    vec = [0, 0, 0, 0]
    for lbl in labels:
        if lbl in axe_map:
            vec[axe_map[lbl]] = 1
    return vec


def split_axe(df):
    # 复制原始 df
    df_clean = df.copy()

    # 生成 axes_vec
    df_clean['axes_vec'] = df_clean["axe"].apply(parse_axes)

    # 拆成 4 列
    df_clean[["axe1",'axe2', 'axe3', 'axe4']] = pd.DataFrame(
        df_clean[f'axes_vec'].tolist(), index=df_clean.index
    )
    return df_clean



# def group_text(df, cols, new_col='col_text'):
#     """
#     将指定的列拼接成一个新的文本列。

#     参数:
#     df: pd.DataFrame
#     cols: list, 需要拼接的列名
#     new_col: str, 新生成列的名称

#     返回:
#     df: 添加了新列的 DataFrame
#     """
#     def safe_get(val):
#         return "" if pd.isna(val) else str(val)

#     df[new_col] = df[cols].apply(lambda row: " ".join(safe_get(row[col]) for col in cols), axis=1)
    
#     print(f"ALL text NA counts: {df[new_col].isna().value_counts(dropna=False)}\n")
#     return df




def emb_text(df, model=None, batch_size=32, col_text=None, col_emb=None, pq_path=None):
    import numpy as np
    import time    

    # 初始化模型（如果没有传入）
    if model is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-m3")

    # 获取 embedding 维度（BGE-m3 = 1024）
    emb_dim = model.get_sentence_embedding_dimension()

    # Fill NaN
    df[col_text] = df[col_text].fillna("")

    # 分离空文本和非空文本
    mask_empty = df[col_text].str.strip() == ""
    mask_nonempty = ~mask_empty # mask_nonempty.values 是一个长度等于 len(df) 的布尔数组
    # print(f"len(df) = {len(df)}")
    # print(f"mask_nonempty.sum() = {mask_nonempty.sum()}")
    # print(f"emb_nonempty.shape = {emb_nonempty.shape}")

    texts_nonempty = df.loc[mask_nonempty, col_text].astype(str).tolist()


    # V1:Encode 只有非空文本
    # print(f"- Encoding {len(texts_nonempty)} non-empty texts in column '{col_text}'...")
    # emb_nonempty = model.encode(
    #     texts_nonempty,
    #     batch_size=batch_size,
    #     normalize_embeddings=True,
    #     show_progress_bar=True
    # )

    # # print(f"[ENCODE] done. Shape = {emb_nonempty.shape}. Time: {end_time-start_time:.2f} sec")

    # # 创建最终 embedding 列
    # emb_all = np.zeros((len(df), emb_dim), dtype=np.float32)

    # # 对非空文本填入真实 embedding
    # emb_all[mask_nonempty.values] = emb_nonempty

    # V2
    # Encode 只有非空文本
    emb_nonempty = model.encode(
        texts_nonempty,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    # 转成 numpy
    emb_nonempty = np.array(emb_nonempty)

    # 强制 reshape 成二维 (n_texts, emb_dim)
    if emb_nonempty.ndim == 1:
        emb_nonempty = emb_nonempty.reshape(1, -1)

    # 检查列数
    emb_dim = model.get_sentence_embedding_dimension()
    if emb_nonempty.shape[1] != emb_dim:
        # 如果返回了 shape (1,0)，补齐为 zeros
        emb_nonempty = np.zeros((emb_nonempty.shape[0], emb_dim), dtype=np.float32)


    # 创建最终 embedding 列
    emb_all = np.zeros((len(df), emb_dim), dtype=np.float32)
    emb_all[mask_nonempty.values] = emb_nonempty



    # 对空文本保持 zero vector（默认）
    #[0,0,0,...,0]（更好的指示 "无信息"）
    # add col
    df[col_emb] = list(emb_all)

    # 保存 parquet
    if pq_path is not None:
        df.to_parquet(pq_path, index=False)
        print(f"[SAVE] Embeddings of texts saved to {pq_path}!")

    return df


def filtrate_df_to_emb(df, 
                       df_all_emb_path="../external_data/df_all_3emb.parquet",
                    ):
    import pandas as pd
    df_all=pd.read_parquet(df_all_emb_path)
    df_to_emb=df[~df['halId_s'].isin(df_all['halId_s'].tolist())]
    df_embedded=df_all[df_all['halId_s'].isin(df['halId_s'].tolist())]
    print(f"[INFO]{len(df_embedded)} articles already embedded! \n" 
          f"{len(df_to_emb)} articles go to embeddings. \n")

    return df_to_emb, df_embedded
 


# filtrate+emb: main
def check_before_emb_text(df,embedding_model,  batch_size=32,
                          df_all_emb_path="external_data/df_all_3emb.parquet",
                          ):
    
    #按照halid筛选是否被embedded，没有则再三列上都emb一遍

    # 1) filtrate df_to_emb, df_embedded:
    df_to_emb, df_embedded=filtrate_df_to_emb(df, df_all_emb_path)
    
    # 2)emb df_to_emb:
    for col_text in ['title_s','keyword_s','abstract_s']:
        df_to_emb= emb_text(df=df_to_emb, model=embedding_model, batch_size=batch_size, col_text=col_text, col_emb=f"emb_{col_text}", 
                        pq_path=None)
        ## [IMPO] 处理完一列要把新的df_to_emb输入，接着处理下一列，所以要io的变量名一致

    # 3) concat 
    df_embedded=pd.concat([df_to_emb, df_embedded], axis=0)
    
    return df_embedded


def to_df_long (df,cols=['emb_title_s','emb_keyword_s','emb_abstract_s'], 
                pq_long_path=None
                # "../external_data/df_noaxe_3emb_long.parquet"
                ):
    # 拆成三行后，每行的数据比完整文本弱（因为只看标题、或关键词、或摘要），
    # 模型可能会更偏向预测常见类别。
    rows = []
    for idx, row in df.iterrows():
        labels = row[['axe1','axe2','axe3','axe4']].values.astype(np.float32)
        for col in cols:
            rows.append({
                "text_emb": row[col],
                'halId_s':row['halId_s'],
                "source": col.split('_')[1],
                "axe1": labels[0],
                "axe2": labels[1],
                "axe3": labels[2],
                "axe4": labels[3]
            })

        # rows.append({
        #     "text_emb": row["emb_keyword_s"],
        #     "source": "keyword",
        #     "axe1": labels[0],
        #     "axe2": labels[1],
        #     "axe3": labels[2],
        #     "axe4": labels[3]
        # })

        # rows.append({
        #     "text_emb": row["emb_abstract_s"],
        #     "source": "abstract",
        #     "axe1": labels[0],
        #     "axe2": labels[1],
        #     "axe3": labels[2],
        #     "axe4": labels[3]
        # })

    df_long = pd.DataFrame(rows)
    
    #去掉无文本的行
    def is_zero_vector(vec):
        return np.allclose(vec, 0.0)
    df_long = df_long[~df_long["text_emb"].apply(is_zero_vector)].reset_index(drop=True)
        

    ## source作为额外信号
    source_map = {"title":0, "keyword":1, "abstract":2}
    df_long["source_id"] = df_long["source"].map(source_map)
    # one-hot
    df_long["source_vec"] = df_long["source_id"].apply(lambda x: np.eye(3)[x])

    if pq_long_path!= None :
        df_long.to_parquet(pq_long_path)
        print(f"[SAVE] df_long saved to {pq_long_path}!")

    return df_long


def oversampling(X_train, y_train):
    from collections import Counter

    # 计算每个类的样本数量
    class_counts = y_train.sum(axis=0)
    print(f"[INFO] y_train before oversampling:{class_counts}")
    max_count = class_counts.max()# → 取最多样本的类别作为目标数量。
    # 动态确定每类需要增加多少:每个类别需要复制多少次才能接近最大数量。
    # multipliers = np.ceil(max_count / (class_counts + 1e-5)).astype(int)

    # 避免复制太多：
    target_count = int(max_count * 0.6)
    multipliers = np.ceil(target_count / (class_counts + 1e-5)).astype(int)
    
    max_mult = 5  # 每个少数类最多增加 5 倍
    multipliers = np.minimum(multipliers, max_mult)


    oversampled_rows = []
    for c, mult in enumerate(multipliers):
        if mult <= 1:
            continue
        mask = y_train[:, c] == 1
        rows_to_duplicate = X_train[mask]
        labels_to_duplicate = y_train[mask]
        
        # 复制 N 次
        for _ in range(mult-1):
            oversampled_rows.append((rows_to_duplicate, labels_to_duplicate))

    # 拼接到训练集
    for X_dup, y_dup in oversampled_rows:
        X_train = np.vstack([X_train, X_dup])
        y_train = np.vstack([y_train, y_dup])
    
    new_counts = y_train.sum(axis=0)
    print("After oversampling:", new_counts)

    return X_train, y_train





def mlp_multilabels(X_train,X_val,y_train, y_val, 
                    batch_size=32,dropout=0.5,n_epochs = 40, patience=5, 
                    to_oversampling=True, model_path="../model/test_mlp.pt"):
    import pandas as pd
    import numpy as np
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import f1_score
    import random
    import os, sys

    
    # fixed seed 固定种子
    seed = 42
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # 
    if to_oversampling==True:
        X_train, y_train=oversampling(X_train, y_train)

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
            # make sure float32
            self.X = torch.from_numpy(X).float()
            self.y = torch.from_numpy(y).float()
            print("X shape:", self.X.shape, "y shape:", self.y.shape)  # 加这个检查

        def __len__(self):
            return len(self.X)
        def __getitem__(self, idx):
            return self.X[idx], self.y[idx]

    val_dataset   = MultiLabelDataset(X_val, y_val)
    val_loader   = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    train_dataset = MultiLabelDataset(X_train, y_train)  # X_train [N, 1024], y_train [N, 4]
    # train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)


    # ----------------dynamic sample_weights-----------------------    
    # 小类别很少，但不想限制最大值 → 用 epsilon 平滑。
    # 不想让类别权重超过某个上限 → 用 np.clip
    class_counts = y_train.sum(axis=0)
    epsilon = 1e-2
    class_weights = 1.0 / (class_counts + epsilon)
    # sample_weights = (y_train * class_weights).sum(axis=1) 
    sample_weights = (y_train * class_weights).max(axis=1) # 每条样本只取 最高的少数类权重，不会被多数类稀释
    sample_weights = np.clip(sample_weights, 0.001, 10.0)
    
    ## clip : 5=> 10
    #sample_weights是每一条的权重，但大多被压缩到了0.001!    
    # print("min:", sample_weights.min(), "max:", sample_weights.max(), "mean:", sample_weights.mean())

    #将w加入sampler
    sampler = WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.float),
        num_samples=len(sample_weights),
        replacement=True
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, sampler=sampler)


    # -------------------------------
    # 3️⃣ Define MLP model:MultiLabelMLP
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

    # model for input (n, 3072)
    # class MultiLabelMLP(torch.nn.Module):
    #     def __init__(self, input_dim, dropout=0.5):
    #         super().__init__()
    #         self.net = torch.nn.Sequential(
    #             torch.nn.Linear(input_dim, 1024),
    #             torch.nn.ReLU(),
    #             torch.nn.Dropout(dropout),

    #             torch.nn.Linear(1024, 512),
    #             torch.nn.ReLU(),
    #             torch.nn.Dropout(dropout),

    #             torch.nn.Linear(512, 4)
    #         )
    #     def forward(self, x):
    #         return self.net(x)


    # -------------------------------
    # 4️⃣ initialize model, optimiser and loss
    # -------------------------------
    # device = "cuda" if torch.cuda.is_available() else "cpu"
    model = MultiLabelMLP(input_dim=X_train.shape[1]).to(device)

    # 优化三：weight decay
    # optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)

    # criterion = nn.BCEWithLogitsLoss()  # 多标签分类
    # criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    # 优化七 ：让模型不要极端预测 0/1：
    # criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight, reduction="mean", label_smoothing=0.1)

    # 优化五:
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


    # --------add early stopping ----------
    # best_f1 = 0
    best_f1_overall = 0.0  # 初始 F1 设为 0，保证任何有效的 F1 都会更新
    best_t_overall = None  # 初始化为空列表或 None
    stops = 0              # 用于 early stopping

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
        #得到最好的阈值
        best_t_per_class = []
        for c in range(all_labels.shape[1]):  # 遍历每个类别
            best_f1, best_t = 0, 0.5          # 初始化当前类别在这个 epoch 下的最佳 F1 和阈值
            for t in np.arange(0.05, 0.80, 0.01):  # 遍历可能的阈值
                preds_t = (all_probs[:, c] >= t).astype(int)  # 用 t 对概率进行二值化
                f1 = f1_score(all_labels[:, c], preds_t, zero_division=0)  # 计算 F1
                if f1 > best_f1:  # 如果当前阈值 F1 更好
                    best_f1, best_t = f1, t  # 更新当前类别最佳阈值
            best_t_per_class.append(best_t)  # 保存这个 epoch 下当前类别的最佳阈值

        # => best_t_per_class 是 当前 epoch 中每个类别的最佳阈值集合。


        # 在每一轮打印的 best_t_per_class 只是用来观察当前 epoch 模型在不同阈值下的表现趋势，它 并没有被实际用于训练或梯度计算。
        # 在prediction才会用到！
        # print("Best thresholds per class:", best_t_per_class)
        # 默认阈值 0.4；后续会改成 best_t_per_class
        # preds_bin = (all_probs >= 0.4).astype(int)
        # f1_macro = f1_score(all_labels, preds_bin, average='macro')
        
        #计算这一轮的F1
        preds_bin = np.zeros_like(all_probs)
        for c, t in enumerate(best_t_per_class):
            preds_bin[:, c] = (all_probs[:, c] >= t).astype(int)
        f1_macro = f1_score(all_labels, preds_bin, average='macro')
        print(f"Epoch {epoch+1}/{n_epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | F1_macro: {f1_macro:.4f}\n")
    
        
        # --------smooth early stopping ----------
        # 对f1进行平滑，避免多类别F1的波动导致过于早停。方法：对近几轮的F1取平均值与best_f1比较
        f1_history = []  # 存储每轮 F1
        k = 3            # 平滑窗口大小
        # 每个 epoch 计算 F1
        f1_history.append(f1_macro)

        # 计算滑动平均
        if len(f1_history) >= k:
            f1_smooth = np.mean(f1_history[-k:])
        else:
            f1_smooth = f1_macro

        # 用平滑后的 F1 判断 early stopping
        if f1_smooth > best_f1_overall:
            best_f1_overall = f1_smooth
            stops = 0
            best_t_overall = best_t_per_class.copy()

            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            torch.save({
                'model_state_dict': model.state_dict(),
                'best_t_overall': best_t_overall
            }, model_path)
        else:
            stops += 1
            if stops >= patience:
                print("Early stopping triggered.")
                break
    print(f"[SAVE] Model et best_t_overall saved to {model_path}!!")

    return model, best_t_overall



def predict_by_mlp(text_embeddings, model, threshold=0.4):
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


def evaluate_model(y_true, y_pred):
    import numpy as np
    from sklearn.metrics import (
        f1_score, precision_score, recall_score,
        classification_report, hamming_loss,
        accuracy_score, confusion_matrix,
        ConfusionMatrixDisplay
        )
    import matplotlib.pyplot as plt
    import matplotlib
    # matplotlib.use("module://matplotlib_inline.backend_inline")

    # overall metrics:
    # average =micro / macro / weighted / samples
    f1_micro = f1_score(y_true, y_pred, average='micro', zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)
    precision_micro = precision_score(y_true, y_pred, average='micro', zero_division=0)
    recall_micro = recall_score(y_true, y_pred, average='micro', zero_division=0)
    # hamming = hamming_loss(y_true, y_pred)
    # subset_acc = accuracy_score(y_true, y_pred)  # exact match

    print("Micro  F1: ", f1_micro)
    print("Macro  F1: ", f1_macro)
    print("Micro Precision:", precision_micro)
    print("Micro Recall:", recall_micro)
    # print("Hamming loss:", hamming)
    # print("Subset exact match:", subset_acc)

    # per-class report
    print("\nPer-class classification report:")
    print(classification_report(y_true, y_pred, target_names=['axe1','axe2','axe3','axe4']))

    # ConfusionMatrixDisplay
    n_classes = y_true.shape[1]
    class_names = ['axe1','axe2','axe3','axe4']
    fig, axes = plt.subplots(1, n_classes, figsize=(4*n_classes, 4))  # 1 行 4 列

    for c in range(n_classes):
        cm = confusion_matrix(y_true[:, c], y_pred[:, c], labels=[0,1])
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0,1])
        disp.plot(ax=axes[c], cmap='Blues', colorbar=False)  # 指定当前轴
        axes[c].set_title(class_names[c])

    plt.tight_layout()
    plt.show()

    return 




def load_predict(df,mlp_model_path,lr_model_path,lgb_model_path,
                t_lr=0.25,t_lgb=0.95, f1_lr=0.44, f1_lgb=0.35, t_ens=0.52):
    
    #=========================load==================================
    ## data
    X = np.concatenate([df["text_emb"].tolist(), df["source_vec"].tolist()], axis=1)
    print(f"input X shape:{X.shape}")
    ## mlp
    class MultiLabelMLP(torch.nn.Module):
            def __init__(self, input_dim, hidden=512, dropout=0.5):
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

    device = "cuda" if torch.cuda.is_available() else "cpu"
    mlp_model = MultiLabelMLP(input_dim=1027, hidden=512, dropout=0.5)
    checkpoint = torch.load(mlp_model_path, map_location=device, weights_only=False)  # 默认 weights_only=True
    mlp_model.load_state_dict(checkpoint['model_state_dict'])
    best_t_overall = checkpoint['best_t_overall']
    mlp_model.eval()

    ## lr
    lr_model = joblib.load(lr_model_path)

    ## lgb
    lgb_model = lgb.Booster(model_file=lgb_model_path)
    
    # PARAMETRES 
    # t_lr, t_lgb=0.25,0.9
    # f1_lr, f1_lgb=0.44, 0.35 

    print(f"Les prédictions sont faites en utilisant le seuil qui a donné le meilleur F1"
          f"lors de l’évaluation sur l’ensemble de validation pour chaque modèle.\n"
          f"threshold lr: {t_lr}; f1 lr :{f1_lr}\n"
          f"threshold lgb: {t_lgb}; f1 lgb :{f1_lgb}\n")
      

    #===========================pred==============================
    # mlp
    pred_mlp, probs_mlp = predict_by_mlp(X, mlp_model, threshold=best_t_overall)
    
    # LR+lgb
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)

    probs_lr = lr_model.predict_proba(X_s)[:,1]
    probs_lgb = lgb_model.predict(X)
    # probs_lgb = lgb_model.predict_proba(X)[:,1]


    # above t
    lr_pred = (probs_lr >= t_lr).astype(int)#单独一个模型的预测结果
    lgb_pred = (probs_lgb >= t_lgb).astype(int)


    # ------------------------合并LR+LGB -----------------------------
    #按照F1权重合并零个models的probs，通过该prob_ens得出t_ens再得出标签
    w_lr = f1_lr / (f1_lr + f1_lgb + 1e-12)# w=weight
    w_lgb = f1_lgb / (f1_lr + f1_lgb + 1e-12)

    proba_ens = w_lr * probs_lr + w_lgb * probs_lgb
    # t_ens = best_thresh_by_pr(y_val_axe4, proba_ensemble)# t_ens=threshold of ensemble
    pred_ens = (proba_ens >= t_ens).astype(int)
  
    #------------------------修正MLP axe4--------------------------------
    # 最终组合（主 MLP 预测前3类 + LR 预测 axe4）
    pred_final = np.zeros_like(pred_mlp)   # shape (N, 4)
    pred_final[:, :3] =pred_mlp[:, :3] 
    pred_final[:, 3] = pred_ens  # LR 预测 axe4

    # ----------------------返回df_long---------------------------------
    df["pred_axe1"] = pred_final[:,0]
    df["pred_axe2"] = pred_final[:,1]
    df["pred_axe3"] = pred_final[:,2]
    df["pred_axe4"] = pred_final[:,3]

    
    return df



def gather_predicted_axes(df_long_predicted, 
                       df_all,
                       groupby_col='halId_s'):
    
    axe_cols = ["pred_axe1", "pred_axe2", "pred_axe3", "pred_axe4"]
    # 按照id聚合：
    df_hal = df_long_predicted.groupby(groupby_col)[axe_cols].max().reset_index()

    def axes_to_str(row):
        axes = []
        for i, col in enumerate(axe_cols, start=1):
            if row[col] == 1:# pred_axeK 的值是0/1
                axes.append(str(i))

        return "; ".join(set(axes))     # 例如 "1; 2; 4"
    df_hal["pred_axes_str"] = df_hal.apply(axes_to_str, axis=1)
    
    # mapping_DICT {id:"axe;axe"}
    hal_axes_dict = dict(zip(df_hal["halId_s"], df_hal["pred_axes_str"]))
    
    # str merged back to df_all (insert):  predicted_Axe : '1; 2; 3' 
    if "predicted_axe" in df_all.columns:
        df_all.drop(columns='predicted_axe', inplace=True)
    idx = df_all.columns.get_loc("axe")
    df_all.insert(idx + 1, "predicted_axe", df_all["halId_s"].map(hal_axes_dict))

    
    # [CHECK] 检查df_long_predicted中在prediction之后是否还有没有axe的行:
    df_no_predaxe=df_hal[df_hal[axe_cols].sum(axis=1)==0]
    if len(df_no_predaxe)>0:
        print(f"[INFO] {len(df_no_predaxe)} lignes qui n'ont pas de prédictions: \n")
        display(df_all[df_all['halId_s'].isin(df_no_predaxe['halId_s'].tolist())][['halId_s','title_s','keyword_s','abstract_s','axe',"predicted_axe"]].head())
    else :
        print(f"[INFO] Au moins une prédiction pour chaque ligne non-axée!")

    
    return df_all


def merge_axes(row):
    # axe+predicted_axe=final_axe
    axes = set()
    if pd.notna(row['axe']):
        axes.update(s.strip() for s in str(row['axe']).split(';') if s.strip())
    if pd.notna(row['predicted_axe']):
        axes.update(s.strip() for s in str(row['predicted_axe']).split(';') if s.strip())
    if not axes:
        return np.nan
    #float变成int，再排序
    axes_sorted = sorted([str(int(float(a))) for a in axes])
    return "; ".join(axes_sorted)



def apply_auto_completion_axes(df_all_path="data/20251201-ProductionScientifiqueIRG-__-202512_2734art.csv",
                            df_all_outpath="data_axe/20251201-ProductionScientifiqueIRG-__-202512_2734art_predaxe.csv",
                            df_all_emb_path="../external_data/df_all_3emb.parquet",
                            noaxe_pq_path='../external_data/df_noaxe_3emb.parquet',
                            mlp_model_path="../model/best_mlp_3emb_2.pt",
                            lr_model_path="../model/best_lr_3emb.pt",
                            lgb_model_path="../model/best_lgb_3emb.txt",
                            t_lr=0.25,t_lgb=0.95, f1_lr=0.44, f1_lgb=0.35, t_ens=0.52
                            ):

    #------------------------------------------read&filtrate-----------------------------------------------
    print(f"\n[ETAPE1] Lire le csv, sélectionner les lignes qui n'ont pas d'axes => df_noaxe\n")
    df_all=pd.read_csv(df_all_path)
    print(df_all.columns)
    df_all['axe'].value_counts(dropna=False)
    df_noaxe=df_all[(df_all['axe'].isna())|(df_all['axe']=="nan")]
    df_hasaxe=df_all[~df_all['halId_s'].isin(df_noaxe['halId_s'])]
    print(f"[INFO] Répartition des axes: \n{df_all['axe'].value_counts(dropna=False)}\n\n"
    f"- len df_all: {len(df_all)}\n"
    f"- len df_noaxe: {len(df_noaxe)}\n"
    f"- len df_hasaxe:{len(df_hasaxe)}"
    )
    #------------------------------------------splitaxe-----------------------------------------------
    print(f"\n[ETAPE2] split axe en 4 colonnes'axe1, axe2, axe3, axe4' et en une colonnes 'axes_vec'sous forme de [1,0,0,0]")
    df_noaxe=split_axe(df_noaxe)


    #------------------------------------------embeddings-----------------------------------------------
    embedding_model_name="BAAI/bge-m3"
    print(f"\n[ETAPE3] Embedder les titres, les mots, les résumés des {len(df_noaxe)} lignes non-axées par le modèle '{embedding_model_name}'...\n")

    if os.path.exists(noaxe_pq_path):
        # df_noaxe_embedded=pd.read_parquet(noaxe_pq_path)
        # all_embbded=[0 for halid in df_noaxe['halId_s'].tolist() if halid in df_noaxe_embedded['halId_s'].tolist() else 1]
        # if all_embbded.sum()!=0:
            # to emb
        # else :

        print(f"[INFO] embeddings existe déjà! Passez à l'étape suivante!")
    else :
        print(f"Veuillez vous patienter pendant l'embeddings.")
        print(f"[INFO] Loading the embeddings model {embedding_model_name}...")

        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer(embedding_model_name)
        
        
        # filtrate df_to_emb, df_embedded:
        df_to_emb, df_embedded=filtrate_df_to_emb(df_noaxe, df_all_emb_path)
        
        # emb df_to_emb:
        for col_text in ['title_s','keyword_s','abstract_s']:
            df_to_emb= emb_text(df=df_to_emb, model=None, batch_size=32, col_text=col_text, col_emb=f"emb_{col_text}", 
                            pq_path=None)
        # concat & save :
        df_noaxe_embedded=pd.concat([df_to_emb, df_embedded], axis=0)
        os.makedirs(os.path.dirname(noaxe_pq_path), exist_ok=True)
        df_noaxe_embedded.to_parquet(noaxe_pq_path, index=False)

        # for col_text in ['title_s','keyword_s','abstract_s']:
        #     df_noaxe_embedded= emb_text(df=df_noaxe, model=embedding_model, batch_size=32, col_text=col_text, col_emb=f"emb_{col_text}", 
        #                 pq_path=noaxe_pq_path)

    #-----------------------------------df_long----------------------------------------------------
    print(f"\n[ETAPE4] Transformer df_noaxe en df_noaxe_long...")
    df_noaxe_embedded=pd.read_parquet(noaxe_pq_path)
    noaxe_pq_long_path=noaxe_pq_path.replace('.parquet','_long.parquet')
    df_noaxe_long=to_df_long(df_noaxe_embedded,cols=['emb_title_s','emb_keyword_s','emb_abstract_s'],
                             pq_long_path=noaxe_pq_long_path)
    
    # print(f"len df_noaxe_long : {len(df_noaxe_long)}\n")
    # display(f"df_noaxe_long : \n {df_noaxe_long.head()}")

    #-----------------------------------------------pred----------------------------------------------
    print(f"\n[ETAPE5] Predire les axes:\n"
          f"Pour les quatre axes, les prédictions sont faites avec le modèle MLP,\n"
          f"tandis que pour l’axe 4, les résultats du LR et du LGB sont combinés en pondérant selon le F1 et le seuil optimal pour ajuster la prédiction.\n"
          f"Pour chaque ligne, les titres, mots-clés et résumés non vides sont prédits séparément, puis les axes sont fusionnés et dédupliqués pour améliorer la stabilité.\n")

    df_long_predicted=load_predict(df=df_noaxe_long,
                    mlp_model_path=mlp_model_path,
                    lr_model_path=lr_model_path,
                    lgb_model_path=lgb_model_path,
                    t_lr=t_lr,t_lgb=t_lgb, f1_lr=f1_lr, f1_lgb=f1_lgb, t_ens=t_ens)
    # print(f"df_noaxe with predicted_axe:\n")
    # display(df_long_predicted.head(),"\n")

    # -----------------------------------renvoie et save la pred---------------------------------------------
    print(f"\n[ETAPE6] Organiser les predictions et renvoie au df original...\n")
    df_all=gather_predicted_axes(df_long_predicted, df_all, groupby_col='halId_s')


  
    # [SHOW] in df_noaxe
    # 重新筛选出df_noaxe with predicted_axe，因为之前的df_noaxe已经被split > long > long pred> groupby > dict
    df_noaxe_pred=df_all[(df_all['axe'].isna())|(df_all['axe']=="nan")]
    print(f"[INFO] Répartiton des axes prédits sur {len(df_noaxe_pred)} lignes:\n"
          f"{df_noaxe_pred.predicted_axe.value_counts(dropna=False)}\n")    
    display(df_noaxe_pred[['halId_s','title_s','keyword_s','abstract_s','axe',"predicted_axe"]].head())



    # create final axe
    df_all['final_axe'] = df_all.apply(merge_axes, axis=1)
    # show
    print(f"Répartiton des axes prédits sur toutes les {len(df_all)} lignes:\n"
          f"{df_all.final_axe.value_counts(dropna=False)}\n")
    
    display(df_all[['halId_s','title_s','keyword_s','abstract_s',"axe",'predicted_axe',"final_axe"]].head())

    # save to outpath!!!
    os.makedirs(os.path.dirname(df_all_outpath), exist_ok=True)
    df_all.to_csv(df_all_outpath, index=False)
    print(f"[SAVE] df with predicted axis saved to {df_all_outpath}!!\n")

    return df_all




















# def auto_completion_by_sim(df, model_name, threshold=0.4):
    
#     #=============================step1：clean text=================================
#     def safe_get(val):
#         return "" if pd.isna(val) else str(val)

#     df["clean_text"] = df.apply(
#         lambda r: preprocess_text(
#             safe_get(r["title_s"]) + " " +
#             safe_get(r["keyword_s"]) + " " +
#             safe_get(r["abstract_s"]),
#             user_stopwords=None,
#             lang=r['language_s']
#         ),
#         axis=1
#     )
     
#     #=============================step2:embedding==================================
#     # with st.spinner("Embedding..."):
#     model = SentenceTransformer(model_name)
#     df["embedding"] = df["clean_text"].apply(lambda x: model.encode(x))


#     # =====================step3 :prediction by similarity between embeddings=====================

#     df["original_axe"] = df["axe"]#保留原值
#     # missing_data_warning(df, col='Axe', show_distribution=False)

#     df=explode_by_col(df, col="axe")#fillna('nan')#原axe已经被exploded
#     df["axe"] = df["axe"].replace("nan", np.nan)
    

#     #计算每一个主题的平均向量：
#     axe_means = df[df["axe"].notna()].groupby("axe")["embedding"].apply(
#         lambda emb: np.mean(list(emb), axis=0)
#     )

#     def predict_axes_for_row(row, threshold):
#         if pd.isna(row["axe"]):#若无axe
#             sims = {axe: cosine_similarity([row["embedding"]], [axe_means[axe]])[0][0] for axe in axe_means.index}
#             # 返回匹配的axe
#             return [axe for axe, score in sims.items() if score >= threshold]
#         else:
#             return [row["axe"]]

#     df["predicted_axe"] = df.apply(lambda row: predict_axes_for_row(row, threshold), axis=1)

#     # print(df.axe.value_counts(dropna=False),'\n')
#     # print(df.predicted_axe.value_counts(dropna=False),'\n')
#     # missing_data_warning(df, col='original_axe', show_distribution=False)
#     #一篇可能有多个axes超过了 threshold
#     df_exploded = df.explode("predicted_axe")
    
#     display(df_exploded[["halId_s","docType_s","authFullName_s","title_s","keyword_s","abstract_s","clean_text","original_axe","predicted_axe"]])


#     # #==========================快速画图=======================
#     # def quick_pie(df,col):
#     #     counts=df[col].fillna('NaN').value_counts()
#     #     cmap = cm.get_cmap('viridis')
#     #     colors = [cmap(i / len(counts)) for i in range(len(counts))]

#     #     fig, ax = plt.subplots(figsize=(6,6))
#     #     ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90, colors=colors)
#     #     ax.set_title(col)
#     #     return fig
    
#     # def show_pies(fig1, fig2):
#     #     st.header("***Comparasion entrte les vrais axes et axes prédits***")
#     #     cols=st.columns(2)
#     #     with cols[0]:
#     #         st.pyplot(fig1)     
#     #     with cols[1]:
#     #         st.pyplot(fig2)
#     #     return 
        
#     # if "fig1" not in st.session_state and "fig1" not in st.session_state: 
#     #     fig1=quick_pie(df,col='Axe')
#     #     fig2=quick_pie(df_exploded, col='predicted_axe')
#     #     st.session_state.fig1=fig1
#     #     st.session_state.fig2=fig2
#     #     show_pies(fig1, fig2)      

#     # else :
#     #     show_pies(st.session_state.fig1, st.session_state.fig2)    
    
#     ###点击总结摘要按钮之后也可以保留

#     #=======================step 4: evaluate by metrics================================ 
    
#     df_valid = df[df["axe"].notna()].drop_duplicates(subset='halId_s')

#     # 所有可能的Axe标签
#     unique_labels = sorted(df_valid["axe"].dropna().unique().tolist())
#     #['1', '2', '3']

#     # 转为多标签二进制格式
#     def to_multilabel(row):# 把axe数字变成binary 2==[010]
#         y_true = [int(x in row["original_axe"]) for x in unique_labels]
#         y_pred = [int(x in row["predicted_axe"]) for x in unique_labels]
#         return y_true, y_pred

#     y_true, y_pred = zip(*df_valid.apply(to_multilabel, axis=1))
#     y_true = np.array(y_true)
#     y_pred = np.array(y_pred)
    

#     st.markdown("***L'accuracy de la prediction :***\n")
#     # 微平均和宏平均的precision/recall/f1
#     st.write("Precision (micro):", precision_score(y_true, y_pred, average="micro"))
#     st.write("Recall (micro):", recall_score(y_true, y_pred, average="micro"))
#     st.write("F1 (micro):", f1_score(y_true, y_pred, average="micro"))

#     st.write("\nPrecision (macro):", precision_score(y_true, y_pred, average="macro"))
#     st.write("Recall (macro):", recall_score(y_true, y_pred, average="macro"))
#     st.write("F1 (macro):", f1_score(y_true, y_pred, average="macro"))

#     ## precision==1,说明pred中的结果都在original中（pred都是正确的），但是还有一部分没有预测出来（还有部分标签没被包含!）
#     return df_exploded



    
