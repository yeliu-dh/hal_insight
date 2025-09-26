import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import textwrap #分行
import altair as alt
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import io

#my utils:
from utils.upload import csv_uploader


# session state :
#上传csv，保存在session state中，相当于一个外部字典，不会再操作(刷新)中丢失
# Streamlit 每次用户操作控件（比如点击 radio、selectbox）都会重新运行整个脚本!!
# 通过控件加入筛选条件，和保存在session中的数据一起重新输入分析部分的code



# -------------------- 页面配置 --------------------
# st.set_page_config(page_title="HAL Insights Dashboard", layout="wide")

st.set_page_config(page_title="Tendance & Répartition", page_icon="🛸", layout="wide")
st.title("📊 Tendance & Répartition")


# -------------------------------
# 1️⃣ 初始化 Session State
# -------------------------------
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "started" not in st.session_state:
    st.session_state.started = False


# -------------------------------
# 2️⃣ 检查/上传 CSV
# -------------------------------

# uploaded_file = st.file_uploader("charger HAL CSV", type=["csv"])

# if uploaded_file is not None:
#     st.session_state.uploaded_df = pd.read_csv(uploaded_file)
#     # st.success("CSV 上传成功！")
#     corpus = st.session_state.uploaded_df #pd.read_csv(uploaded_file)
#     st.write("### Corpus original", corpus.head())


csv_uploader()# 调用上传器（会自动处理已有/新上传）
if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:

    # -------------------------------
    # 3️⃣ 点击开始统计按钮
    # -------------------------------
    col1, col2 = st.columns([5, 1])  # 最右边一列放按钮
    with col2:
        summary_button = st.button("Commencer")

    if not st.session_state.started:#未开始
        if summary_button:#点击了开始按钮
            # if st.session_state.uploaded_df is not None:#且已经上传数据
            st.session_state.started = True#更新为“开始状态”，df储存在session中，数据不会在变化?            
        
    # -------------------------------
    # # 4️⃣ 分析界面
    # # -------------------------------
    if st.session_state.started:
        df = st.session_state.uploaded_df.copy()

        #-----------  global-----------------
        #----------- période ----------------
        if "publicationDate_s" in df.columns:
            df["publicationDate_s"] = pd.to_datetime(df["publicationDate_s"], errors="coerce")
            latest_date = df["publicationDate_s"].max()
            latest_ym = latest_date.strftime("%Y-%m") if pd.notnull(latest_date) else "Aucune date valide"
        else:
            latest_ym = "Colonne manquante"

        st.header("📌 Aperçu global")

        # 小函数：检查列是否存在于df，否就返回 None
        # 且定义是否按照分号切割
        def safe_count(col, split=False, unique=True):
            if col not in df.columns:
                return None
            series = df[col].dropna()
            if split:
                series = series.str.split(";").explode()
            return series.nunique() if unique else len(series)

        total_articles = len(df)
        total_authors = safe_count("authFullName_s", split=True)
        total_journals = safe_count("journalTitle_s")
        total_domains = safe_count("domain_s", split=True)
        total_languages = safe_count("language_s")
        total_labs = safe_count("labStructName_s", split=True)
        total_countries = safe_count("country_s")

        # 平均每作者产出
        # avg_per_author = total_articles / total_authors if total_authors and total_authors > 0 else 0

        # 显示时：如果值为 None，则提示 "Colonne manquante"
        def display_metric(col, label, value, suffix=""):
            if value is None:
                col.metric(label, "Colonne manquante")
            else:
                col.metric(label, value, suffix)

        col1, col2, col3, col4 = st.columns(4)
        display_metric(col1, "Nombre total d’articles", total_articles, f" jusqu’à {latest_ym}")
        display_metric(col2, "Nombre total d’auteurs", total_authors)  # , f"Moyenne par auteur: {avg_per_author:.2f}"
        display_metric(col3, "Nombre total de revues", total_journals)
        display_metric(col4, "Nombre total de domaines", total_domains)

        col1, col2, col3, col4 = st.columns(4)
        display_metric(col1, "Nombre total de laboratoires", total_labs)
        display_metric(col2, "Nombre total de langues", total_languages)
        display_metric(col3, "Nombre total de pays", total_countries)
        col4 = st.empty()  # 占位不显示内容

        st.write("\n\n")


        # # -------------------- 增强版 趋势折线图 --------------------
        st.header("📈 Tendance de production scientifique")

        if "publicationDate_s" not in df.columns:
                st.error("la colonne 'publicationDate_s' manque dans CSV")
        else:
            # 转换日期
            # df["publicationDate_s"] = pd.to_datetime(df["publicationDate_s"], errors="coerce")
            
            st.info(f"⚠️ La date est manquante dans {df.publicationDate_s.isna().sum()} ({df.publicationDate_s.isna().sum()*100/len(df):.2f}%) articles!")

            # # -------------------------------
            # # 4a. 选择时间范围
            # # -------------------------------
            # 输入具体数值（无法选择years=none）
            # years = st.number_input(
            #     "Afficher les X dernières années ",
            #     min_value=1,
            #     max_value=100,
            #     value=10,  # 默认值
            #     step=1
            # )
            # if not years:
            #     years = None

            # if years is not None:
            #     cutoff = pd.Timestamp.today() - pd.DateOffset(years=years)
            #     df = df[df["publicationDate_s"] >= cutoff]

            # -------------------------------
            # 4a. 选择时间范围 (横向滑块)
            # -------------------------------
            years = st.slider(
                "Afficher les X dernières années",
                min_value=0,
                max_value=100,
                value=10,
                step=1,
                help="Déplacez le curseur. 0 = toutes les années"
            )

            if years == 0:
                # 不限制时间范围
                df_filtered = df.copy()
            else:
                cutoff = pd.Timestamp.today() - pd.DateOffset(years=years)
                df= df[df["publicationDate_s"] >= cutoff]

            # -------------------------------
            # 4b. 选择时间颗粒
            # -------------------------------
            period_option = st.radio(
                "Choisir la granularité temporelle",
                ["Par mois", "Par an"],
                horizontal=True
            )

            if period_option == "Par mois":
                df["Period"] = df["publicationDate_s"].dt.to_period("M").astype(str)
            else:
                df["Period"] = df["publicationDate_s"].dt.to_period("Y").astype(str)

            # -------------------------------
            # 4c. 聚合统计
            # -------------------------------

            trend = df.groupby("Period").size().reset_index(name="count")
            trend["cumulative"] = trend["count"].cumsum()

            # -------------------------------
            # 4d. 标题：显示起止年月
            # -------------------------------
            min_date = df["publicationDate_s"].min()
            max_date = df["publicationDate_s"].max()
            if pd.notnull(min_date) and pd.notnull(max_date):
                min_label = min_date.strftime("%b %Y")
                max_label = max_date.strftime("%b %Y")
                chart_title = f"Tendance de production scientifique ({min_label} – {max_label})"
            else:
                chart_title = "Tendance de production scientifique"

            # -------------------------------
            # 4e. 双折线趋势图（当期 + 累计）
            # Q:quantitative连续变量，O:ordinal 序数型,T:temporal, N:nominal
            # -------------------------------
            base = alt.Chart(trend).encode(x="Period:O")

            line_count = base.mark_line(point=True, color="#440154").encode(
                y=alt.Y("count:Q", axis=alt.Axis(title="Articles (période)")),
                tooltip=["Period:O", "count:Q"]
            )

            line_cum = base.mark_line(point=True, color="#2ca25f", strokeDash=[5, 2]).encode(
                y=alt.Y("cumulative:Q", axis=alt.Axis(title="Articles (cumulés)")),
                tooltip=["Period:O", "cumulative:Q"]
            )

            chart = alt.layer(line_count, line_cum).resolve_scale(
                y="independent"
            ).properties(
                width=800, height=400, title=alt.TitleParams(chart_title, anchor="middle")  # 居中标题
            ).configure_axis(
                labelAngle=-30
            )

            st.altair_chart(chart, use_container_width=True)


### ------------------------通用def生成图-------------------------------- 

        # ------------------- 通用函数 -------------------
        import textwrap

        def wrap_text(text, max_len=30):
            # textwrap.wrap 会在空格处换行，不会切断单词
            lines = textwrap.wrap(text, width=max_len, break_long_words=False, replace_whitespace=False)
            return "<br>".join(lines)

        def make_pie_chart(df, col, title, top_n=5):
            if col=='domain_s':
                counts=df[col].fillna('nan').str.split(";").explode().str.strip().value_counts()
            else:
                counts = df[col].fillna("nan").value_counts()
            
            # 如果类别大于top_n, 只保留 top_n，其余归为 "其他"
            if len(counts) > top_n:
                counts = pd.concat([
                    counts.head(top_n),
                    pd.Series({"Autres": counts[top_n:].sum()})
                ])

            counts_df = counts.reset_index()
            counts_df.columns = [col, "count"]

            # 标签分行，见上函数
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
                margin=dict(t=80, b=80, l=100, r=150),  # 上下左右留白
                # yaxis=dict(tickfont=dict(size=10))       # 缩小字体
            )

            fig.update_yaxes(tickangle=0, automargin=True)#或者让 y 轴自动换行
    
            return fig

        def make_bar_chart(df, col, title, top_n=10):
            if col=='domain_s':
                counts=df[col].fillna('nan').str.split(";").explode().str.strip().value_counts()
            else:
                counts = df[col].fillna("nan").value_counts()
                    
            if len(counts) > top_n:
                counts = pd.concat([
                    counts.head(top_n),
                    pd.Series({"Autres": counts[top_n:].sum()})
                ])

            counts_df = counts.reset_index()
            counts_df.columns = [col, "count"]
            # 标签分行
            counts_df[col] = counts_df[col].apply(lambda x: wrap_text(str(x)))
            # counts_df[col] = counts_df[col].apply(lambda x: '<br>'.join([x[i:i+25] for i in range(0,len(x),10)]))

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
                margin=dict(t=80, b=80, l=100, r=150)  # 上下左右留白
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

        # ------------------- 示例应用 -------------------

        st.header("📊 Répartition statistique")
        st.info(
            "ℹ️ Remarques :\n"
            "- Cliquez sur la légende pour masquer/afficher une catégorie.\n"
            "- Passez la souris pour voir les données statistiques.\n"
            "- Cliquez sur 📷 en haut à droite pour télécharger l'image.\n"
            "- Les valeurs manquantes sont remplacées par « nan ». Vous pouvez cliquer sur la légende pour  masquer/afficher une catégorie.\n"
            "- Seules les N premières catégories sont affichées, les autres sont regroupées sous « Autres ».\n"
            "- Note qu'un document peut appartenir à plusieurs domaines scientifiques.\n"
        )

        for col, title in {
            "docType_s": "Répartition par type de document",
            "domain_s": "Répartition par domaine scientifique",
            "journalTitle_s":"Répartition par journal",
            "language_s": "Répartition par langue",
            "country_s": "Répartition par pays"
        }.items():
            # st.subheader(title)
            if col in df.columns:
                cols = st.columns(2)
                with cols[0]:
                    # 如果是 domain_s 默认选中 "bar"，否则默认 "pie"
                    default_index = 1 if col == "domain_s" else 0

                    chart_type = st.radio(
                        f"Type de figure:",
                        ["pie", "bar"],
                        index=default_index,
                        key=col,
                        horizontal=True
                    )
                with cols[1]:
                    top_n = st.number_input(
                        f"Top N:", 
                        min_value=1, max_value=100, value=5, step=1, key=f"topn_{col}"
                    )
            

                if chart_type == "pie":
                    fig = make_pie_chart(df, col, title, top_n=top_n)


                else:
                    fig = make_bar_chart(df, col, title, top_n=top_n)
                st.plotly_chart(fig, use_container_width=True)#网页显示自适应
                st.write("\n")

            else:
                st.error(f"⚠️ La colonne « {col} » est absente des données !")


                # # ------------------ 下载 PNG ------------------
                # try:
                #     img_bytes = fig.to_image(format="png", width=800, height=600)
                #     cols = st.columns([4,1])  # 4:1 比例，右侧放按钮    
                #     with cols[1]:
                #         st.download_button(
                #             label="Télécharger le graphique",
                #             data=img_bytes,
                #             file_name=f"{col}_{chart_type}_chart.png",
                #             mime="image/png"
                #         )

                # except Exception as e:
                #     st.error(f"Impossible d'exporter le graphique : {e}\nAssurez-vous que 'kaleido' est installé et Chrome/Chromium disponible.")
        


        # # -------------------- Top 5 排行 --------------------
        # # 作者，杂志，会议

        # st.header("🏆 Top 5 排行")
        # def get_top(series, top=5):
        #     return series.dropna().str.split(",").explode().str.strip().value_counts().head(top)

        # top_authors = get_top(df["authFullName_s"])
        # top_domains = get_top(df["domain_s"])
        # top_journals = get_top(df["journalTitle_s"])
        # top_conferences = get_top(df["conferenceTitle_s"])

        # col1, col2 = st.columns(2)
        # with col1:
        #     st.subheader("Top 5 Authors")
        #     st.bar_chart(top_authors)
        #     st.subheader("Top 5 Domains")
        #     st.bar_chart(top_domains)
        # with col2:
        #     st.subheader("Top 5 Journals")
        #     st.bar_chart(top_journals)
        #     st.subheader("Top 5 Conferences")
        #     st.bar_chart(top_conferences)

        