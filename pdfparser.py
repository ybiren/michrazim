from pdfreader import PdfReader
import pandas as pd
import tabula.io as tabula
import re

class PdfParser:
  
  RELEVANT_PAGE_FOR_BOOKLET = 6

  ###################################################################################################################################3333
  def numPlotsAndCompounds(self, pdfData, auctionNumberFormatted,log):
    log("checking num plots and compounds " + str(auctionNumberFormatted))
    txt = PdfReader().convertFromBytes({"content": pdfData}, 1, 1)  
    #with open(f"{auctionNumberFormatted}.txt",'w',encoding='utf-8') as file:
      #file.write(txt)  
      #file.close()  

    num_plots = "N.A"
    num_compounds = "N.A"
    for line in txt.splitlines():
      if "מגרש" in line:
        log(line)
        if "מגרש אחד" in line:
          num_plots = "1"
        elif "שני מגרשים" in line:   
          num_plots = "2"
        else:
          for index,word in enumerate(line.split()): 
            if "מגרש" in word and line.split()[index-1].isnumeric():
              num_plots = line.split()[index-1]  #  מגרשים X 
       
      if "מתחם" in line:
        log(line)
        if "מתחם אחד" in line:
          num_compounds = "1"
        elif "שני מתחמים" in line:   
          num_compounds = "2"
        else:
          for index,word in enumerate(line.split()): 
            if "מתחם" in word and line.split()[index-1].isnumeric():
              num_compounds = line.split()[index-1]  #  מתחמים X 
    
    return {"num_plots": num_plots,"num_compounds": num_compounds}
  
  ###################################################################################################################################3333
  def bookletData(self, pdfData, auctionNumberFormatted,log):
    #txt = PdfReader().convertFromBytes({"content": pdfData}, PdfParser.RELEVANT_PAGE_FOR_BOOKLET, PdfParser.RELEVANT_PAGE_FOR_BOOKLET)  
    with open('file.pdf', 'wb') as f:
      f.write(pdfData)

    dfs = tabula.read_pdf('file.pdf', stream=True,pages="all", pandas_options={'header': None})
    log("bookletdata num tables=" + str(len(dfs)) + "----------" + auctionNumberFormatted)
    #print(dfs[0])
  
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

      dev_expences_col = self.__findColInTable(df, lambda col: "הוצ" in col)
      bail_amount_col =  self.__findColInTable(df, lambda col: "פיקדון" in col or "ערבות" in col)
      min_price_col =    self.__findColInTable(df, lambda col: "מיני" in col and "מחיר" in col) 
      num_offers_col =   self.__findColInTable(df, lambda col: "מציע" in col) 
    
      if dev_expences_col!=-1 and bail_amount_col!=-1 and min_price_col!=-1: 
        relevant_df = df
        all_relevant_dfs.append(df)
        log("founded dfs all" + str(auctionNumberFormatted)+ "-----dev_expences_col=" + str(dev_expences_col) + ",bail_amount_col=" + str(bail_amount_col) + ",min_price_col=" + str(min_price_col) +  ",num_offers_col=" + str(num_offers_col))
        founded_dev_expences_col = dev_expences_col 
        founded_min_price_col = min_price_col
        founded_bail_amount_col = bail_amount_col
        founded_num_offers_col = num_offers_col
      elif (dev_expences_col!=-1 and bail_amount_col!=-1 and dev_expences_col != bail_amount_col) or (dev_expences_col!=-1 and min_price_col!=-1 and dev_expences_col != min_price_col) or (bail_amount_col!=-1 and min_price_col!=-1 and bail_amount_col != min_price_col) : 
        relevant_df = df
        all_relevant_dfs.append(df)
        if bail_amount_col == -1:
          next_relevant_df = dfs[idx+1]
        log("founded dfs partly" + str(auctionNumberFormatted)+ "-----dev_expences_col=" + str(dev_expences_col) + ",bail_amount_col=" + str(bail_amount_col) + ",min_price_col=" + str(min_price_col) +  ",num_offers_col=" + str(num_offers_col))
        founded_dev_expences_col = dev_expences_col 
        founded_min_price_col = min_price_col
        founded_bail_amount_col = bail_amount_col
        founded_num_offers_col = num_offers_col
            
    dev_expences_val = "N.A"
    min_price_val = "N.A"
    bail_amount_val = "N.A"
    num_offers_val = "N.A"

    if len(relevant_df) > 0:
      dev_expences_val = self.__findValueForColumn(relevant_df, founded_dev_expences_col,log)
      min_price_val = self.__findValueForColumn(relevant_df, founded_min_price_col,log)
      bail_amount_val = self.__findValueForColumn(relevant_df, founded_bail_amount_col,log)
      num_offers_val = self.__findValueForColumn(relevant_df, founded_num_offers_col,log)
    # למקרה שפקדון נמצא בטבלה הבאה
    if len(next_relevant_df) > 0:    
      founded_bail_amount_col =  self.__findColInTable(next_relevant_df, lambda col: "פיקדון" in col or "ערבות" in col)
      bail_amount_val = self.__findValueForColumn(next_relevant_df, founded_bail_amount_col,log)
        

    if dev_expences_val == "N.A" and min_price_val == "N.A" and bail_amount_val == "N.A" and num_offers_val == "N.A":
      relevant_df = pd.DataFrame()
    
    log({"devExpences": dev_expences_val, "minPrice": min_price_val, "bailAmount": bail_amount_val, "numOffers":num_offers_val})
    return {"devExpences": dev_expences_val, "minPrice": min_price_val, "bailAmount": bail_amount_val, "numOffers":num_offers_val, "all_relevant_dfs": all_relevant_dfs}
  
  ###################################################################################################################################3333
  def __findColInTable(self,df,cond):
    accumulated_row_arr =[]
    for i in range(100):
      accumulated_row_arr.append("")  

    ####arr = df.to_numpy()
    #Find relevant columns
    ####for item in arr:
      ####item1 = re.sub(r'\([^)]*\)', '', numpy.array2string(item)) 
      ####row_arr = item1.replace('"','').replace("'ס","ס").replace("[","").replace("]","").split()
      #row_arr = item1.replace('"','').replace("'ס","ס").split("'")
      ####for index, col in enumerate(row_arr):
        ####accumulated_row_arr[index]=accumulated_row_arr[index] + col
      ####for index, col in enumerate(accumulated_row_arr):
        ####if(cond(col)):
          ####return index
    ####return -1
    
    arr = df.values.tolist()
    for row_arr in arr:
      for index, col in enumerate(row_arr):
        accumulated_row_arr[index]=accumulated_row_arr[index] + str(col)
      for index, col in enumerate(accumulated_row_arr):
        if(cond(col)):
          return index
    return -1


  ###################################################################################################################################3333
  def __findValueForColumn(self, df, col,log):
    
    arr = df.values.tolist()
    for row_arr in arr:
      if col != -1 and col<len(row_arr) and str(row_arr[col]).split()[0].replace(",","").replace("'","").replace('"','').isnumeric():
        return str(row_arr[col]).split()[0]
    return "N.A"
    
  #217/2024 - exception
    
              
