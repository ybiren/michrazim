#solved bug yhat plot was not correct

import pandas as pd
import tabula.io as tabula
import re
from driveutils import DriveUtils
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def uniqueAllValuesList(all_values_list):
    seen = []
    unique_arr =  []
    for item in all_values_list:
      if item not in seen:
        seen.append(item)
        unique_arr.append(item)   
    return unique_arr
  


def createPlotsGS(driveUtils, gc, dfs):
    # Specify the folder ID where you want to create the Google Sheet
    folder_id = "1wjaJuppiXCI2ZVDhIOGQt0IwYo-BZ6eU"
    #delete previous plots
    plot_ids= driveUtils.getAllPlotIdS(folder_id)
    for plot_id in plot_ids:
      gc.del_spreadsheet(plot_id)
    print("after delete previous plots, founded " + str(len(plot_ids)))

    # Create a new Google Sheet
    #spreadsheet = self.gc.create('מגרשים', folder_id=folder_id)
    spreadsheet = gc.create('plots',folder_id=folder_id)
      # Open the new spreadsheet
    worksheet = spreadsheet.get_worksheet(0)  # Get the first sheet
    
    all_values_list = []
    for df in dfs:
      df.fillna('',inplace=True) # change any nulls for blank space
      all_values_list += df.values.tolist()
    unique_all_values_list = uniqueAllValuesList(all_values_list)
    
    # Update the Google Sheet with DataFrame
    worksheet.update(unique_all_values_list)


def __findColInTable(df,cond):
    accumulated_row_arr =[]
    for i in range(100):
      accumulated_row_arr.append("")  
    arr = df.values.tolist()
    for row_arr in arr:
      for index, col in enumerate(row_arr):
        accumulated_row_arr[index]=accumulated_row_arr[index] + str(col)
      for index, col in enumerate(accumulated_row_arr):
        if(cond(col)):
          return index
    return -1

def __findValueForColumn(df, col):
    
    arr = df.values.tolist()
    for row_arr in arr:
      if col != -1 and col<len(row_arr) and str(row_arr[col]).split()[0].replace(",","").replace("'","").replace('"','').isnumeric():
        return str(row_arr[col]).split()[0]
    return "N.A"
  
driveUtils = DriveUtils()
DriveUtils.current_auction_folder_id = "1wjaJuppiXCI2ZVDhIOGQt0IwYo-BZ6eU"
plot_ids = driveUtils.getAllPlotIdS("1wjaJuppiXCI2ZVDhIOGQt0IwYo-BZ6eU")
scope = [
        "https://spreadsheets.google.com/feeds",
        'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
credentials = ServiceAccountCredentials.from_json_keyfile_name('googlesheetcreds.json', scope)
gc = gspread.authorize(credentials)

dfs = tabula.read_pdf('file.pdf', stream=True,pages="all", pandas_options={'header': None})
relevant_df = pd.DataFrame()
next_relevant_df = pd.DataFrame()
all_relevant_dfs = []

founded_dev_expences_col =-1
founded_min_price_col = -1
founded_bail_amount_col = -1
founded_num_offers_col = -1

for idx,df in enumerate(dfs):
      
   dev_expences_col =-1
   min_price_col = -1
   bail_amount_col = -1
   num_offers_col = -1

   dev_expences_col = __findColInTable(df, lambda col: "הוצ" in col)
   bail_amount_col =  __findColInTable(df, lambda col: "פיקדון" in col or "ערבות" in col)
   min_price_col =    __findColInTable(df, lambda col: "מיני" in col and "מחיר" in col) 
   num_offers_col =   __findColInTable(df, lambda col: "מציע" in col) 
    
   if dev_expences_col!=-1 and bail_amount_col!=-1 and min_price_col!=-1: 
     relevant_df = df
     all_relevant_dfs.append(df)
     founded_dev_expences_col = dev_expences_col 
     founded_min_price_col = min_price_col
     founded_bail_amount_col = bail_amount_col
     founded_num_offers_col = num_offers_col
   elif (dev_expences_col!=-1 and bail_amount_col!=-1 and dev_expences_col != bail_amount_col) or (dev_expences_col!=-1 and min_price_col!=-1 and dev_expences_col != min_price_col) or (bail_amount_col!=-1 and min_price_col!=-1 and bail_amount_col != min_price_col) : 
     relevant_df = df
     all_relevant_dfs.append(df)
     if bail_amount_col == -1:
       next_relevant_df = dfs[idx+1]
       founded_dev_expences_col = dev_expences_col 
       founded_min_price_col = min_price_col
       founded_bail_amount_col = bail_amount_col
       founded_num_offers_col = num_offers_col
            
   dev_expences_val = "N.A"
   min_price_val = "N.A"
   bail_amount_val = "N.A"
   num_offers_val = "N.A"

   if len(relevant_df) > 0:
      dev_expences_val = __findValueForColumn(relevant_df, founded_dev_expences_col)
      min_price_val = __findValueForColumn(relevant_df, founded_min_price_col)
      bail_amount_val = __findValueForColumn(relevant_df, founded_bail_amount_col)
      num_offers_val = __findValueForColumn(relevant_df, founded_num_offers_col)
   # למקרה שפקדון נמצא בטבלה הבאה
   if len(next_relevant_df) > 0:    
      founded_bail_amount_col =  __findColInTable(next_relevant_df, lambda col: "פיקדון" in col or "ערבות" in col)
      bail_amount_val = __findValueForColumn(next_relevant_df, founded_bail_amount_col)
        

   if dev_expences_val == "N.A" and min_price_val == "N.A" and bail_amount_val == "N.A" and num_offers_val == "N.A":
     relevant_df = pd.DataFrame()
 
print(len(all_relevant_dfs))
createPlotsGS(driveUtils, gc, all_relevant_dfs)
print("end")   
      