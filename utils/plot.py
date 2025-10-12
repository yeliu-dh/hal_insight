import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from utils.mapping import map_axe

def wrap_text(text, max_len=30):
    # 调整图例 ：textwrap.wrap 会在空格处换行，不会切断单词
    lines = textwrap.wrap(text, width=max_len, break_long_words=False, replace_whitespace=False)
    return "<br>".join(lines)



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


def make_pie_chart(df, col, title, top_n=5):
    if col=="Axe":
        df=map_axe(df, col)

    #--------------处理multivalues str-----------------
    df=explode_by_col(df, col)
    counts=df[col].value_counts()
    
    # if col=='domain_s' or col=="Axe":
    #     counts=df[col].fillna('nan').str.split(";").explode().str.strip().value_counts()
    # else:
    #     counts = df[col].fillna("nan").value_counts()
    

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
    # if col=='domain_s' or col=="Axe":
    #     counts=df[col].fillna('nan').str.split(";").explode().str.strip().value_counts()
    # else:
    #     counts = df[col].fillna("nan").value_counts()
    
    
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
