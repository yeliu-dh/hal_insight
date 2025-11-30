import streamlit as st
import camelot
import os


fnege_folder="sandbox/fnege_pdf"
files=[f for f in os.listdir(fnege_folder) if f.endswith(".pdf")]

file=files[0]

tables = camelot.read_pdf("fnege_2023.pdf", pages="all")

# 提取所有表格并合并
import pandas as pd
df_list = [t.df for t in tables]
df = pd.concat(df_list, ignore_index=True)
