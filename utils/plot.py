import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
import plotly.express as px
from utils.mapping import map_axe
import streamlit as st

#my utils:
from utils.preprocess import preprocess_text, assign_time_unit, explode_by_col, wrap_text

def keywords_trendline(df, options, keywords):
    fig_title = "Évolution des mots clés"

    if "submittedDate_s" in df.columns:    
        min_date = df["submittedDate_s"].min()
        max_date = df["submittedDate_s"].max()
        if pd.notnull(min_date) and pd.notnull(max_date):
            min_label = min_date.strftime("%b %Y")
            max_label = max_date.strftime("%b %Y")
            fig_title = f"Évolution des mots clés ({min_label} – {max_label})"


    # 清洗，合并文本
    for opt in options:
        df[f'{opt}_clean']=df.apply(lambda row: preprocess_text(row[opt], stopwords=None, lang=row["language_s"]) ,axis=1)
                                    
    df["text_clean"] = df[options].apply(
        lambda row: " ".join([row[col] for col in options if isinstance(row[col], str)]),
        axis=1
    )        

    #打时间标签
    df = assign_time_unit(df)

    # 初始化 trend_data
    trend_data = {
            kw: df.groupby('time_unit')['text_clean'].apply(lambda texts: sum(kw in t for t in texts))
            for kw in keywords
            if any(df["text_clean"].str.contains(kw, na=False))
        }
       

    # 画图
    colors = cm.viridis(np.linspace(0,1,len(keywords)))

    fig, ax = plt.subplots(figsize=(10,5))
    for i, kw in enumerate(trend_data.keys()):
        series = trend_data[kw]
        # 转换 PeriodIndex 为 datetime 方便绘图
        ax.plot(series.index.to_timestamp(), series.values, label=kw, color=colors[i])

    ax.set_xlabel("Temps")
    ax.set_ylabel("Nombre d'occurrences")
    ax.set_title(fig_title)
    ax.grid(True)
    ax.legend()
    # plt.title(fig_title)
    plt.xticks(rotation=45)
    return fig



        

def make_pie_chart(df, col, title, top_n=5):
    #----------------map axe---------------------------
    # if col=="Axe":
    #     df=map_axe(df, col)

    #--------------处理multivalues str-----------------
    df=explode_by_col(df, col)
    counts=df[col].value_counts()
    # ---------------- map Axe --------------------------
    if col == "Axe":
        axe_map = {
            "1": "Performances et responsabilités",
            "2": "Société de services et services à la société",
            "3": "Innovations, transformations et résistances organisationnelles et sociétales",
            "4": "Ouvrages pédagogiques"
        }
        # 只对非空值进行映射
        df[col] = df[col].astype(str).str.strip().map(lambda x: axe_map.get(x, x))



    # ---------------TOP N---------------------------
    # 如果类别大于top_n, 只保留 top_n，其余归为 "其他"
    if len(counts) > top_n:
        counts = pd.concat([
            counts.head(top_n),
            pd.Series({"Autres": counts[top_n:].sum()})
        ])

    counts_df = counts.reset_index()
    counts_df.columns = [col, "count"]

    #------------ 标签文本分行，见上函数----------------
    counts_df[col] = counts_df[col].apply(lambda x: wrap_text(str(x)))

    fig = px.pie(
        counts_df,
        values="count",
        names=col,
        color_discrete_sequence=px.colors.sequential.Viridis,
        hover_data=["count"],
        title=title
    )
    #显示标签和比例，文字在扇形的外部，扇形之间轻微分开
    fig.update_traces(textinfo="label+percent", textposition="outside", pull=[0.05]*len(counts_df),domain=dict(x=[0, 0.8], y=[0, 1]))
    #x=[0, 0.8] → 饼图占画布左 0%~80%，右边 20% 留给图例
    # y=[0,1] → 垂直方向占满画布

    # 图例放下方，水平排列，网页显示好看?
    fig.update_layout(
        width=800,   # 固定导出尺寸
        height=600,  
        legend=dict(
            title=col.split('_')[0].strip(),
            orientation='v',
            x=0.8,
            y=1,
            xanchor='left',
            yanchor='top'
        ),           
        # legend=dict( #pie图图例放在下方
        #     title=col.split('_')[0].strip(),
        #     orientation='h',
        #     y=-0.2, # 负值表示放在画布底部外侧

        #     x=0.5,
        #     xanchor='center'
        # ),
        # showlegend=False, #不显示图例
        title=dict(
            text=title,
            x=0.5,          # 水平居中
            xanchor='center',
            yanchor='top'
        ),
        margin=dict(t=80, b=80, l=150, r=150),  # 上下左右留白
        # yaxis=dict(tickfont=dict(size=10))       # 缩小字体
    )

    fig.update_yaxes(tickangle=0, automargin=True)#或者让 y 轴自动换行

    return fig





def make_bar_chart(df, col, title, top_n=10):
    #----------------map axe---------------------------
    # if col=="Axe":
    #     df=map_axe(df, col)

    #--------------处理multivalues str-----------------
    df=explode_by_col(df, col)
    counts=df[col].value_counts()


    if len(counts) > top_n:
        counts = pd.concat([
            counts.head(top_n),
            pd.Series({"Autres": counts[top_n:].sum()})
        ])

    counts_df = counts.reset_index()
    counts_df.columns = [col, "count"]
    # 标签分行
    counts_df[col] = counts_df[col].apply(lambda x: wrap_text(str(x)))

    fig = px.bar(
        counts_df,
        x="count",
        y=col,
        orientation="h",#horizontal
        title=title,
        color="count",
        color_continuous_scale="viridis",
        text="count"
    )
    
    fig.update_layout(
        yaxis=dict(autorange="reversed"),              # 让最大值在最上方
        title=dict(
            text=title,
            x=0.5,          # 水平居中
            xanchor='center',
            yanchor='top'
        ),
        legend=dict(
            title=col.split('_')[0].strip(),
            orientation='v',
            x=0.9,
            y=0.9,
            xanchor='left',
            yanchor='middle'
        ),
        margin=dict(t=80, b=80, l=150, r=150)  # 上下左右留白
    )
    fig.update_yaxes(tickangle=0, automargin=True)#或者让 y 轴自动换行

    return fig


  #------------------------------------------------#
            # #optional：
            # fig.update_layout(
            #     legend=dict(
            #         # title="文献类型",
            #         x=0.9,  # 横向位置，0=左, 1=右
            #         y=0.9,  # 纵向位置，0=下, 1=上
            #         xanchor='left',
            #         yanchor='middle',
            #         orientation="v"  # 'v' 垂直, 'h' 水平
            #     )
            # )
            ## tips:
            # xanchor（水平对齐）：
            # 'left' → x 坐标对应图例的左边缘
            # 'center' → x 坐标对应图例的水平中心
            # 'right' → x 坐标对应图例的右边缘

            # yanchor（垂直对齐）：
            # 'bottom' → y 坐标对应图例底部
            # 'middle' → y 坐标对应图例中间
            # 'top' → y 坐标对应图例顶部

            # 显示图例（默认在右侧）
            # fig.update_layout(legend_title_text="文献类型")



