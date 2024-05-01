#%%

"""Data Modeling For Statistik Perbankan indonesia
berlaku untuk Model :
Keg.usaha KBMI 1.1.-1.5.
"""

# Init module 
import pandas as pd
import numpy as np
from math import isnan
from datetime import date
from glob import glob
import re

#%%

# File Loader
df = pd.read_excel('STATISTIK PERBANKAN INDONESIA - AGUSTUS 2023.xlsx',
                    sheet_name = 'Keg.usaha KBMI 1.1.-1.5.', 
                    dtype=object, header=None)
df.insert(0, 'Sheet_Name', 'Keg.usaha KBMI 1.1.-1.5.')
df.insert(0, 'File_Name', 'STATISTIK PERBANKAN INDONESIA - AGUSTUS 2023.xlsx')

# Tabel Name
if any(df[0].notnull())==True:
    df['Table_Name']  = np.where(df[0].str.startswith('Tabel', na=False),
                        df[0], np.nan )
else:
    df['Table_Name']  = np.where(df[1].str.startswith('Tabel', na=False),
                        df[1], np.nan ) 


# Move After Sheet Name
col = df.pop('Table_Name')
df.insert(2, col.name, col)

df['Table_Name'] = df['Table_Name'].ffill()

# Drop off for 
# Starting and Ends Period Column and rows
# Value Row start from
for index, value in enumerate(df.iloc[:,2:].columns):

    if any(df[value].astype('str').str.contains(r'^[0-9]{4}', regex=True)) | \
       (any(df[value].astype('str').str.contains(r'[0-9]{4}$', regex=True)) & \
       ~any(df[value].astype('str').str.contains(r'\)', regex=True)) & \
       ~any(df[value].astype('str').str.len() > 20 )) :
        start_col_num = df.iloc[:,2:].columns[index]
        start_col_idx = index
        
        # Numerical Data starts From
        df['NUMCHECK'] = np.where((df[value].astype('str').str.contains(r'^[0-9]{4}', regex=True)) | 
                                  (df[value].astype('str').str.contains(r'[0-9]{4}$', regex=True)) |
                                  (df[start_col_num].astype('str').str.isnumeric()),True, False) 
        break

start_row_num = df['NUMCHECK'].idxmax()

# Check Ends Columns to avoid any cell value that fill outside print area
for index, value in enumerate(df.iloc[:,start_col_idx:].columns):
    if not any(df[value].astype('str').str.match(r'^[0-9]{4}')):
        end_col_num = df.iloc[:,start_col_idx:].columns[index - 1]
        end_col_idx = index
        break

# cut to first row
df_1 =  df[start_row_num:].reset_index(drop=True)
# if any(df_1[0].notnull())==True:
#     df_1[0] = df_1[0].ffill()
# else:
#     df_1[1] = df_1[1].ffill()


#%%
# kata yang Muncul di header :
with open("header_posibility.txt", "r") as f:
    lst = f.readlines()

lst = [ls.strip() for ls in lst]
headers_words = '|'.join(lst)

df_1_head = df_1.head(3)
df_1_head = df_1_head.dropna(how='all', axis=1)
df_1_head = df_1_head.loc[:,start_col_num:end_col_num].ffill(axis=1)
df_1_head = df_1_head.fillna('')
df_1_head = df_1_head.apply(lambda x: x.astype('str'))
df_1_head = df_1_head.apply(lambda x: x.str.replace('.0','', regex=False))
df_1_head = df_1_head.T
df_1_head[0] = np.where(df_1_head[1].astype('str') != '',
                        df_1_head[0].astype('str') + '_' + df_1_head[1].astype('str'),
                        df_1_head[0].astype('str'))
df_1_head = df_1_head.T

df_1.update(df_1_head)


#%%
# Rows to column
coll_tuple = list(zip(df_1.columns.to_list(), df_1.iloc[0].to_list()))

# Fix Name
def fill_col_name(col1, col2):
    if str(col1).isnumeric() \
    and (isinstance(col2, float) \
    and isnan(col2) and col1 < 15):
        result = 'level_' + str(col1)  
    elif str(col1).isnumeric() and not isinstance(col2, float):
        result = col2
    else:
        result = col1
    return result

ls_coll = [fill_col_name(col1, col2) for col1, col2 in coll_tuple]
# Rename 
ls_coll = [re.sub(headers_words,'level_0', str(s).lower()) for s in ls_coll ]

# Column Selections to avoid if any NA become column
filt_ls_coll = [item for item in ls_coll if isinstance(item, str)]

df_1.columns = ls_coll
df_1 = df_1.iloc[2:]
df_1 = df_1[filt_ls_coll]

#%%
# Level Cleanup Operations
lvl_coll = [coll for coll in df_1.columns.to_list() if coll[:5]=='level']

# Level Remove A. or a. -
df_1[lvl_coll] = df_1[lvl_coll].replace(r'^[a-zA-Z]\.$',np.nan, regex=True)
df_1[lvl_coll] = df_1[lvl_coll].replace(r'^[0-9]\.',np.nan, regex=True)
df_1[lvl_coll] = df_1[lvl_coll].replace(r'^-$',np.nan, regex=True)
df_1[lvl_coll] = df_1[lvl_coll].replace(headers_words,np.nan, regex=True)


#%%
# Get Index of Column Name

col_idx = df_1.columns.get_indexer(['table_name'])+1
col_name = df_1.columns[col_idx.tolist()[0]]

# Fix if there is same value with column table name
df_1[col_name] = np.where(df_1[col_name]==df_1['table_name'],
                           np.nan,
                           df_1[col_name])

# Clean Up if Column has all NA
df_1 = df_1.dropna(axis=1, how='all')
# refresh column level selection
lvl_coll = [coll for coll in df_1.columns.to_list() if coll[:5]=='level']


#%%
# Check last level column if there is dash and space that indicate hierarchy
if any(df_1[lvl_coll[-1]].str.match(r'^ .+|^-.+', case=False)):
    new_col_nm = f'level_{str(int(lvl_coll[-1][-1]) + 1)}'
    # Fill New Level with Value
    df_1[new_col_nm] = np.where(df_1[lvl_coll[-1]].str.match(r'^ .+|^-.+', case=False),
                            df_1[lvl_coll[-1]],
                            np.nan)
    df_1[lvl_coll[-1]] = df_1[lvl_coll[-1]].replace(r'^ .+|^-.+',np.nan, regex=True)

# refresh column level selection
lvl_coll = [coll for coll in df_1.columns.to_list() if coll[:5]=='level']

# Check last level column if there is dash that indicate hierarchy
if any(df_1[lvl_coll[-1]].str.match(r'^ .+', case=False)):
    new_col_nm = f'level_{str(int(lvl_coll[-1][-1]) + 1)}'
    # Fill New Level with Value
    df_1[new_col_nm] = np.where(df_1[lvl_coll[-1]].str.match(r'^ .+', case=False),
                            df_1[lvl_coll[-1]],
                            np.nan)
    df_1[lvl_coll[-1]] = df_1[lvl_coll[-1]].replace(r'^ .+',np.nan, regex=True)




#%%

# refresh column level selection
lvl_coll = [coll for coll in df_1.columns.to_list() if coll[:5]=='level']

# Col wise then Row wise fillup
df_1[lvl_coll] = df_1[lvl_coll].ffill(axis=1) 
df_1[lvl_coll] = df_1[lvl_coll].ffill() 


#%%

# Remove Column that has no Numbers
df_all = df_1.loc[df_1['numcheck']==True]
df_all = df_all.dropna(axis=1, how='all')
# refresh column level selection
lvl_coll = [coll for coll in df_all.columns.to_list() if coll[:5]=='level']

#%%
# Parent Child column operations

df_all['lst_level'] = df_all[lvl_coll].values.tolist()
df_all['lst_level'] = df_all['lst_level'].apply(pd.unique)

# Each list must have 2 element
# check if there is more than 2 then remove element starting from left side

df_all['lst_level'] = df_all['lst_level'].apply(lambda x: x[-2:])

# sense if having or no child
if max(df_all['lst_level'].apply(len)) == 1:
    df_all['parent'] = pd.DataFrame(df_all['lst_level'].tolist(), index= df_all.index)
    df_all['child'] = np.nan
else:
    df_all[['parent', 'child']] = pd.DataFrame(df_all['lst_level'].tolist(), index= df_all.index)

#%%
# Select Column for transpose ops

ls_main_col = ['file_name', 'sheet_name', 'table_name','parent', 'child']
ls_melt = list(set(df_all.columns.to_list()).difference(ls_main_col))

# Remove Level contains item
ls_melt = list(filter(lambda l: 'level' not in l, ls_melt))
ls_melt.sort()

#%%

# Transposed Ops
df_dt_ojk = df_all.melt(id_vars=ls_main_col, 
               value_vars=ls_melt,
               var_name='Dimension', value_name='Fact')

# df_dt_ojk.sort_values(by=3)
