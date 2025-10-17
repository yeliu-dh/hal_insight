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
from utils.wordcloud import preprocess_text


# def wrap_text(text, max_len=30):
#     import textwrap
#     # 调整图例 ：textwrap.wrap 会在空格处换行，不会切断单词
#     lines = textwrap.wrap(text, width=max_len, break_long_words=False, replace_whitespace=False)
#     return "<br>".join(lines)


# def wrap_text(text, max_len=30):
#     import textwrap
   
#     lines = textwrap.wrap(
#         text, 
#         width=max_len, 
#         break_long_words=False, 
#         replace_whitespace=False
#     )
#     return "<br>".join(lines)



def wrap_text(text, max_len=30, html=True):
    import textwrap
    """
    在 空格 处换行，而不会拆开单词；

    把太长的文字（超过 max_len）自动插入 <br>；

    返回一个 HTML 字符串，适合用于 Streamlit 或 Plotly 的可视化标签。

    可选使用\n（适用于str）或者 <br>（适用于网页）   
    默认是在网页中显示   


    replace_whitespace=True（默认）
        会把文本中所有的空白字符（\n, \t, \r, 等）都替换成普通的 " "（空格）。
        这样可以避免出现“奇怪的换行”或“制表符错位”等问题。

    replace_whitespace=False
        则会保留原文中的这些空白字符，不会替换。
        例如：原来有换行符 \n，它就会被保留下来


    """

    lines = textwrap.wrap(text, width=max_len, break_long_words=False)
    return ("<br>" if html else "\n").join(lines)


# utils.wordcloud.py
def explode_by_col(df, col):
    """"
    空值填nan，
    多值按照，/；分割成list
    =>在某一col上explode；
    检查notna

    """
    df = df.copy()
    df[col] = df[col].fillna('nan').astype(str).str.split("[,;]") # axe中有nan所以type:objet，先变成str
    df = df.explode(col)
    df[col] = df[col].str.strip()
    return df[df[col].notna() & (df[col] != "")]



def assign_time_unit(df, date_col="submittedDate_s"):
    """
    给 DataFrame 增加一个 'time_unit' 列，根据整个 df 的时间范围自动选择粒度：
    - <=12个月：按月
    - 12~36个月：按季度
    - >36个月：按年

    参数：
        df : pd.DataFrame
        date_col : str，日期列名，默认 "submittedDate_s"

    返回：
        df : 增加 'time_unit' 列的 DataFrame
        period_m : 总月份数
        x_label_format : 可用于 matplotlib 的时间格式化字符串
    """
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        earliest_date = df[date_col].min()
        latest_date = df[date_col].max()

        if pd.notnull(earliest_date) and pd.notnull(latest_date):
            period_m = (latest_date.year - earliest_date.year) * 12 + \
                       (latest_date.month - earliest_date.month) + 1

            # 自动选择时间粒度
            if period_m <= 12:
                df['time_unit'] = df[date_col].dt.to_period('M')
                x_label_format = "%Y-%m"
            elif period_m <= 36:
                df['time_unit'] = df[date_col].dt.to_period('Q')
                x_label_format = "Q%q-%Y"
            else:
                df['time_unit'] = df[date_col].dt.to_period('Y')
                x_label_format = "%Y"
        else:
            period_m = 0
            df['time_unit'] = pd.NaT
            x_label_format = "%Y-%m"
    else:
        period_m = 0
        df['time_unit'] = pd.NaT
        x_label_format = "%Y-%m"

    return df


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


    # # 初始化 trend_data
    # trend_data = {kw: df.groupby('time_unit')['text_clean'].apply(lambda texts: sum(kw in t for t in texts)) 
    #             for kw in keywords}
    trend_data = {}
    missing_keywords = []  # 用于收集未出现的词

    for kw in keywords:
        series = df.groupby('time_unit')['text_clean'].apply(lambda texts: sum(kw in t for t in texts))
        if series.sum() == 0:
            missing_keywords.append(kw)
        else:
            trend_data[kw] = series

    # 如果有关键词没出现，显示 warning
    if missing_keywords:
        st.warning(
            f"⚠️ Les mots suivants n'ont été trouvés dans aucun texte : "
            + ", ".join(missing_keywords)
        )
    # 如果所有关键词都没出现，可以提前返回
    if len(trend_data) == 0:
        st.stop()  # Streamlit 会停止执行并显示 warning

        

    colors = cm.viridis(np.linspace(0,1,len(keywords)))

    fig, ax = plt.subplots(figsize=(10,5))
    for i, kw in enumerate(keywords):
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



            







# colors = cm.viridis(np.linspace(0,1,len(keywords)))

# for i, kw in enumerate(keywords):
#     plt.plot(trend_data[kw].index, trend_data[kw].values, label=kw, color=colors[i])
# plt.xlabel("Année / Mois")
# plt.ylabel("Nombre d'occurrences")
# plt.title("Évolution des mots-clés")
# plt.grid(True)
# plt.legend()
# plt.show()





def make_pie_chart(df, col, title, top_n=5):
    #----------------map axe---------------------------
    if col=="Axe":
        df=map_axe(df, col)

    #--------------处理multivalues str-----------------
    df=explode_by_col(df, col)
    counts=df[col].value_counts()

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
    if col=="Axe":
        df=map_axe(df, col)

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



