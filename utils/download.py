
import streamlit as st
import pandas as pd
import sys
import os
import json
from pathlib import Path
import io
from datetime import datetime   

#my utils :
from utils.HAL_search_api import build_period






#===========================================SAVE=======================================================#
def get_default_filename(df,start_year=None, start_month=None, end_year=None, end_month=None):
    # ---download date---
    today_s = datetime.now().strftime("%Y%m%d")

    # 若filename包含起止时间！
    if start_year and start_month and end_year and end_month:
        start_date, end_date=build_period(start_year=start_year, start_month=start_month,
                                        end_year=end_year, end_month=end_month)
        # 已经统一*
        
        if start_date =="*" :
            date_s=f"before_{end_date.split('T')[0]}"
        elif end_date=="*":
            date_s=f"after_{start_date.split('T')[0]}"
        elif start_year =="*" and end_year =="*":
            date_s=""             
        else :
            date_s=f"{start_year}{start_month}-{end_year}{end_month}"

        if date_s.strip():
            filename=f"{today_s}-ProductionScientifiqueIRG-{date_s}_{len(df)}art"
        else :
            filename= f"{today_s}-ProductionScientifiqueIRG_{len(df)}art"
            
            
        # if end_year=="aujourd'hui" or end_month=="aujourd'hui":
        #     now = datetime.now()
        #     current_year, current_month = now.year, now.month
        #     end_year, end_month=current_year, current_month
        
        # # 去掉时间戳：
        # if 'T' in start_date:
        #     start_date=start_date.split('T')[0]
        # if 'T' in end_date:    
        #     end_date=end_date.split('T')[0]
            
        return f"{today_s}-ProductionScientifiqueIRG-{date_s}_{len(df)}art"
    
    else :
        return f"{today_s}-ProductionScientifiqueIRG_{len(df)}art"

  


  
    
def save_file_csv_xlsx(df,start_year, start_month, end_year, end_month, key_filename):
    """
    保存数据模块！
    
    默认：filename下载年月，irg，文章数量
    可选：是否在filename中加入起止年月
        
    """

    # st.markdown(f"**📥 Téléchargement**")

    default_filename=get_default_filename(df,start_year, start_month, end_year, end_month)
    
    if df is not None and not df.empty:
        try : 
            # ----------------SAVE TO LOCAL----------------- 
            cols = st.columns([3, 1, 1, 1])
            
            #---------------define file name------------------- 
            with cols[0]:
                # 用户输入框
                file_name = st.text_input(
                    f"📥 Télécharger le fichier sous le nom :",  # 提示文字
                    value=default_filename,            # 默认值
                    key=key_filename
                )

            #---------------as CSV------------------- 
            with cols[2]:
                st.markdown("<br>", unsafe_allow_html=True)
                csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    label="as CSV",
                    data=csv_data,
                    file_name = file_name+".csv",
                    mime="text/csv",
                    key=f"download_{key_filename}_csv"      
                )
                
                
            
            #---------------as XLSX------------------- 
            # xlsx不接受tdate!
            
            with cols[3]:
                st.markdown("<br>", unsafe_allow_html=True)
                
                # ---clean tdate---
                df_export=df.copy()
                for col in df_export.select_dtypes(include=["datetimetz"]).columns:
                    df_export[col] = df_export[col].dt.tz_localize(None)
                
                # XLSX → 需要用 io.BytesIO() 来缓存二进制数据，再传给 download_button。
                xlsx_buffer = io.BytesIO()
                with pd.ExcelWriter(xlsx_buffer, engine="xlsxwriter") as writer:
                    df_export.to_excel(writer, index=False, sheet_name="Articles")
                xlsx_data = xlsx_buffer.getvalue()

                st.download_button(
                    label="as XLSX",
                    data=xlsx_data,
                    file_name=file_name+".xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{key_filename}_xlsx"  
                )
                # 这是 XLSX 文件的 MIME 类型，告诉浏览器这是一个 Excel 文件，否则st button可能无法识别文件类型 
        except Exception as e :
            st.warning (f"ERROR in save_file_csv_xlsx :\n {e}")   
    
    else : 
        st.warning(f"df.empty!")
    st.markdown("<br>", unsafe_allow_html=True)

    return


def save_file_csv_xlsx_by_filename(df, filename):
    import io
    from datetime import datetime   
    import streamlit as st
    
    if df is not None and not df.empty:
    #  ----------------SAVE TO LOCAL----------------- 
        cols=st.columns(4)
        #---------------file name------------------- 
        with cols[0]:
            file_name = st.text_input(
                f"Nom du fichier :",  # 提示文字
                value=filename,            # 默认值
            )
        #---------------as CSV------------------- 
        with cols[2]:
            csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="Télécharger CSV",
                data=csv_data,
                file_name = file_name+".csv",
                mime="text/csv"
            )

        #---------------as XLSX------------------- 
        with cols[3]:
            # XLSX → 需要用 io.BytesIO() 来缓存二进制数据，再传给 download_button。
            xlsx_buffer = io.BytesIO()
            with pd.ExcelWriter(xlsx_buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Articles")
            xlsx_data = xlsx_buffer.getvalue()

            st.download_button(
                label="Télécharger XLSX",
                data=xlsx_data,
                file_name=file_name+".xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 这是 XLSX 文件的 MIME 类型，告诉浏览器这是一个 Excel 文件，否则st button可能无法识别文件类型 
    else : 
        st.warning(f"df.empty!")
    return



