import os, sys, time
import pandas as pd
import re
import numpy as np
import json


import logging
from pypdf import PdfReader, PdfWriter
import camelot




# my utils
    

def get_fnege_tables(pdf_path, year, start_page, end_page, 
                   output_folder):
    """
    PdfReader:save the pdf pages that only has tables to fnege_tables
       
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
   
    # read
    for page_num in range(start_page-1, end_page):
        writer.add_page(reader.pages[page_num])

    # save:
    output_file = f"fnege_{year}_p{start_page}-{end_page}.pdf"
    os.makedirs(output_folder, exist_ok=True)
    output_path=os.path.join(output_folder, output_file)
    with open(output_path, "wb") as f:
        writer.write(f)


    return 



def get_info_from_pdf_tables (pdf_path, ):
    
    # read & extract
    
    tables = camelot.read_pdf(pdf_path, pages="all")#camelot只提取
    df_list = [t.df for t in tables]
    df = pd.concat(df_list, ignore_index=True)
    logging.info(f'[CHECK] {len(df_list)} tables in {os.path.basename(pdf_path)} file => one csv')
    # reorder?
    
    display(df)
    
    # save as csv in same folder:
    outpath_csv=pdf_path.replace('.pdf', '.csv')
    df.to_csv(outpath_csv,index=False)
    logging.info(f"[SAVE] fnege csv saved to {outpath_csv}!")
    
    return 


#------------------------------------with clean fnege of each year------------------------------

def clean_issn(issn):
    if not isinstance(issn, str):
        return None
    # 去掉空格
    issn = issn.strip().replace(' ', '')
    # 如果已经是 XXXX-XXXX 格式，直接返回
    if re.match(r'^\d{4}-\d{3}[\dX]$', issn):
        return issn
    # 如果是连续 8 位数字，加上 '-'
    elif re.match(r'^\d{8}$', issn):
        return issn[:4] + '-' + issn[4:]
    else:
        # 不符合标准，返回原值或 None
        return issn



def read_clean_fnege_v1(year, csv_path):
    cols=['nom de la revue', 'issn', 'domaine', "rang"]
    
    df = pd.read_csv(csv_path)
    missing_cols=[c for c in cols if c not in df.columns]
    if len(missing_cols)> 0:
        print(f"[MISSING] missings cols:{'; '.join(missing_cols)}!!")
        
        
    df.columns = [c.strip().lower() for c in df.columns]
    rename_map = {
        "nom de la revue": "journal"
    #     "issn": "issn",
    #     "domaine": f"domaine_{year}",
    #     "rang": f"rang_{year}"
    }
    df = df.rename(columns=rename_map)

    # CHECK :仅保留需要的列（避免多余列影响 merge）
    keep = ["journal", "issn", f"domaine", f"rang"]
    df = df[[c for c in keep if c in df.columns]]    
    
    print(f"[INFO] fnege {year} : {len(df)} lines! {df.issn.nunique()} journaux!")
    # print(f"[CHECK] {df['rang'].value_counts(dropna=False)}\n")
    # display(df.head())
    return df



def clean_journal_name(journal):
    journal = re.sub("\n","",journal.strip()) #.replace('\n', ' ')#去掉首位换行
    journal = re.sub(r'\s+', ' ', journal) # multi spaces=>one
    journal = re.sub(r'\s+', ' ', journal) # multi spaces=>one

    return journal.lower()

# find
def find_journals_hal(journals_str, fnege_hal):
    journal_list=journals_str.split(';')
    
    journal_list=[clean_journal_name(j) for j in journal_list]
    fnege_hal_keys_clean=[clean_journal_name(j) for j in fnege_hal.keys()]
    
    dict_hal=dict(zip(fnege_hal_keys_clean,fnege_hal.keys()))
    
    # 按照干净keys寻找，返回原始的hal keys
    journal_hal_list=set([dict_hal.get(j,None) for j in journal_list if j in fnege_hal_keys_clean])
    return '; '.join(journal_hal_list) if len(journal_hal_list)>0 else None
 
 
 

def get_fnege_main(input_folder, 
                   fnege_hal_path, 
                   output_folder):

    print("clean & reorder csv".center(100, '-'),"\n") 
    years=['2011',"2013", "2016", "2019", "2022"]
    dict_fnege=dict()
    for y in years:
        df=read_clean_fnege_v1(year=y, csv_path=os.path.join(input_folder, f"fnege_{y}.csv"))
        dict_fnege[y]=df
    print(f"[CHECK] years of fnege: {dict_fnege.keys()}")
    
    

    print('get all issn'.center(100, '-'),"\n")
    all_ids=[]
    for y in years:
        df_y=dict_fnege[y]
        ids=list(df_y['issn'])
        
        ## clean issn: 出现这种情况：0959- 6526 !=0959-6526
        ids=[clean_issn(id) for id in ids]
        print(f"len {y}: {len(ids)}")
        all_ids.extend(ids)
    all_ids=set(all_ids)
    print(f'len({min(years)}-{max(years)}) :{len(all_ids)}') 

    
    # N=>1
    print("concateante all df by issn: issn, rang_yrs, journal_names".center(100,"-"),"\n")
    
    years = sorted(dict_fnege.keys())
    rows = []
    for issn_id in set(all_ids):
        row = {'issn': issn_id}
        
        journal_names = []
        
        for y in years:
            df_y = dict_fnege[y]
            row_match = df_y[df_y['issn'] == issn_id]
            
            if not row_match.empty:
                # 取该年的 rang 和 journal
                row[f'rang_{y}'] = row_match['rang'].iloc[0]  # 标量
                journal_names.append(row_match['journal'].iloc[0])
            else:
                row[f'rang_{y}'] = None  # 如果这一年没有该 ISSN
        
        # 去重保留顺序
        row['journal_names'] = '; '.join(list(dict.fromkeys(journal_names)))
        rows.append(row)
        # break # chq id

    df_all = pd.DataFrame(rows)
    print(f"[CHECK] len(df_all) {len(df_all)}")
    # display(df_all.head())
    
    print('find journal_names in journal by cleaning first'.center(100, "-"),"\n")
    with open(fnege_hal_path, "r", encoding='utf-8') as f:
        fnege_hal=json.load(f)
    df_all['journal_hal'] = df_all['journal_names'].apply(lambda x : find_journals_hal(x, fnege_hal))

        
    print('merge df with journal_hal by it'.center(100, "-"),"\n")
    df_nonan = df_all[df_all['journal_hal'].notna()]
    df_nan=df_all[~df_all['issn'].isin(df_nonan['issn'])]
    print(f'[CHECK]{len(df_nonan)} df has corresponding journal hal; {len(df_nan)} doesnt')
    
    df_merged = df_nonan.groupby('journal_hal').agg({
        'issn': 'first',  # 保留一个 ISSN（或者可以用 list 保存多个）
        'journal_names': lambda x: '; '.join(x),  # 合并 journal_names 列
        'rang_2011': 'first',  # 每年的排名列取第一个非空值
        'rang_2013': 'first',
        'rang_2016': 'first',
        'rang_2019': 'first',
        'rang_2022': 'first'
    }).reset_index()
    
    print('concatenate df with and without journal_hal'.center(100,'-'),"\n")
    df_final=pd.concat([df_merged,df_nan],axis=0)
    df_final=df_final[['issn','journal_names','journal_hal','rang_2011','rang_2013','rang_2016','rang_2019','rang_2022']]
    print(f"[CHECK] len df final: {len(df_final)} !")
    # display(df_final.head())

    outpath_fnege_final=os.path.join(output_folder, 'fnege_final_hal.csv')
    df_final.to_csv(outpath_fnege_final, index=False) 
    print(f"[SAVE] fnege_final_hal saved to {outpath_fnege_final}!!")
    
    return df_final

















