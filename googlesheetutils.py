import gspread
from oauth2client.service_account import ServiceAccountCredentials
from driveutils import DriveUtils
import time
from datetime import datetime

class GsUtils:

  ID_COL = 1
  AUCTION_NUMBER_COL = 2
  UNITS_COL = 3
  CITY_COL = 4
  TYPE_COL = 5
  VOCATION_COL = 6
  OPEN_DATE_COL = 7
  PUBLISH_DATE_COL = 8
  LAST_DATE_COL = 9
  IS_BOOKLET_PUBLISHED_COL = 10
  NUM_DEADLINES_POSTPONED_COL = 11
  NUM_PLOTS_COL = 12
  NUM_COMPOUNDS_COL = 13
  NUM_OFFERS_COL = 14
  BAIL_AMOUNT_COL = 15
  MINIMAL_PRICE_COL = 16
  DEV_EXPENSES_COL = 17
  IS_OPEN_FOR_BIDS_COL = 18
  UPDATE_DATE_COL = 19
  LINK_TO_FOLDER_COL = 20
  
################################################################################
  def __init__(self):
    scope = [
        "https://spreadsheets.google.com/feeds",
        'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name('googlesheetcreds.json', scope)
    self.gc = gspread.authorize(credentials)
    self.wks = self.gc.open('auctions').sheet1
    #self.__insHeaderColumns()
    self.driveUtils = DriveUtils()
    self.auctionsDict = {}
    self.__buildAuctionsDic()
     
  ################################################################################
  def integrate(self, data,log):
    #wks.update(f'A{row_number}:F{row_number}', [[idno, name, email, phone, created_on, updated_on]])  
    ###try:
        folder_id = self.driveUtils.current_auction_folder_id
        if(not self.isAuctionExist(data["misMichraz"].strip())): #Insert row
          self.__insertRow(data, log, folder_id)    
        else: #Update row
          self.__updateRow(data, log, folder_id)    

  ################################################################################
  def __insertRow(self, data, log, folder_id): 
    is_quota_exceeded = True
    while is_quota_exceeded == True:
      try:
        insertedRowInd = len(self.auctionsDict) + 2
        row_data = [
          str(insertedRowInd),
          data["misMichraz"].strip(),
          data["numUnits"],
          data["city"],
          data["auction_type"],
          data["vocation"],
          data["openDate"],
          data["publishDate"],
          data["lastDate"],
          data["isBookletPublished"],
          data["numDeadlinesPostponed"],
          data["numPlots"],
          data["numCompounds"],
          data["numOffers"],
          data["bailAmount"],
          data["minPrice"],
          data["devExpences"],
          data["is_open_for_bids"],
          datetime.now().strftime("%Y-%m-%d"),
          '=HYPERLINK("https://drive.google.com/drive/u/2/folders/' + folder_id + '", "קישור")'
        ]
        # insert entire row
        self.wks.update(f'A{insertedRowInd}:T{insertedRowInd}', [row_data])
        link = '=HYPERLINK("https://drive.google.com/drive/u/2/folders/' + folder_id + '", "קישור")'
        self.wks.update_cell(insertedRowInd, GsUtils.LINK_TO_FOLDER_COL, link)
               
        
        '''
        self.wks.update_cell(insertedRowInd, GsUtils.ID_COL, str(insertedRowInd))
        self.wks.update_cell(insertedRowInd, GsUtils.AUCTION_NUMBER_COL, data["misMichraz"].strip())
        self.wks.update_cell(insertedRowInd, GsUtils.UNITS_COL, data["numUnits"])
        self.wks.update_cell(insertedRowInd, GsUtils.CITY_COL, data["city"])
        self.wks.update_cell(insertedRowInd, GsUtils.VOCATION_COL, data["vocation"])
        self.wks.update_cell(insertedRowInd, GsUtils.OPEN_DATE_COL, data["openDate"])
        self.wks.update_cell(insertedRowInd, GsUtils.PUBLISH_DATE_COL, data["publishDate"])
        self.wks.update_cell(insertedRowInd, GsUtils.LAST_DATE_COL, data["lastDate"])
        self.wks.update_cell(insertedRowInd, GsUtils.IS_BOOKLET_PUBLISHED_COL, data["isBookletPublished"])
        self.wks.update_cell(insertedRowInd, GsUtils.NUM_DEADLINES_POSTPONED_COL, data["numDeadlinesPostponed"])
        self.wks.update_cell(insertedRowInd, GsUtils.NUM_PLOTS_COL, data["numPlots"])
        self.wks.update_cell(insertedRowInd, GsUtils.NUM_COMPOUNDS_COL, data["numCompounds"])
        self.wks.update_cell(insertedRowInd, GsUtils.NUM_OFFERS_COL, data["numOffers"])
        self.wks.update_cell(insertedRowInd, GsUtils.BAIL_AMOUNT_COL, data["bailAmount"])
        self.wks.update_cell(insertedRowInd, GsUtils.MINIMAL_PRICE_COL, data["minPrice"])
        self.wks.update_cell(insertedRowInd, GsUtils.DEV_EXPENSES_COL, data["devExpences"])
        link = '=HYPERLINK("https://drive.google.com/drive/u/2/folders/' + folder_id + '", "קישור")'
        self.wks.update_cell(insertedRowInd, GsUtils.LINK_TO_FOLDER_COL, link)
        self.wks.update_cell(insertedRowInd, GsUtils.IS_OPEN_FOR_BIDS_COL, data["is_open_for_bids"])
        '''
        
        self.auctionsDict[data["misMichraz"]] = {"index": insertedRowInd}
        log(f"google sheet -row Inserted Successfully - {data['misMichraz']}")
        is_quota_exceeded = False
      except Exception as e:
        if "Quota exceeded" in str(e):  
          log(f"google sheet insert row quota exceeded, sleep for 60 seconds") 
          time.sleep(60)
        else:
          log(f"google sheet insert row exception, {str(e)}") 
          is_quota_exceeded = False

    

  ################################################################################
  def __updateRow(self, data, log, folder_id):
    is_quota_exceeded = True
    while is_quota_exceeded == True:
      try:
        updatedRowInd = self.auctionsDict[data["misMichraz"].strip()]["index"]
        log(f"updatedRowInd={updatedRowInd}")
        row = self.auctionsDict[data["misMichraz"].strip()]["row"]
        # Prepare the row data
        row_data = [
          row[GsUtils.ID_COL-1],
          data["misMichraz"].strip(),
          data["numUnits"],
          data["city"],
          data["auction_type"],
          data["vocation"],
          data["openDate"],
          data["publishDate"],
          data["lastDate"],
          data["isBookletPublished"],
          data["numDeadlinesPostponed"],
          row[GsUtils.NUM_PLOTS_COL-1],
          row[GsUtils.NUM_COMPOUNDS_COL-1],
          data["numOffers"],
          data["bailAmount"],
          data["minPrice"],
          data["devExpences"],
          data["is_open_for_bids"],
          datetime.now().strftime("%Y-%m-%d"),
          '=HYPERLINK("https://drive.google.com/drive/u/2/folders/' + folder_id + '", "קישור")'
        ]

        # Update the entire row
        self.wks.update(f'A{updatedRowInd}:T{updatedRowInd}', [row_data])
        link = '=HYPERLINK("https://drive.google.com/drive/u/2/folders/' + folder_id + '", "קישור")'
        self.wks.update_cell(updatedRowInd, GsUtils.LINK_TO_FOLDER_COL, link)
        

        '''
        self.wks.update_cell(updatedRowInd, GsUtils.UNITS_COL, data["numUnits"])
        self.wks.update_cell(updatedRowInd, GsUtils.OPEN_DATE_COL, data["openDate"])
        self.wks.update_cell(updatedRowInd, GsUtils.PUBLISH_DATE_COL, data["publishDate"])
        self.wks.update_cell(updatedRowInd, GsUtils.LAST_DATE_COL, data["lastDate"])
        # update if auction booklet published
        self.wks.update_cell(updatedRowInd, GsUtils.IS_BOOKLET_PUBLISHED_COL ,data["isBookletPublished"])
        self.wks.update_cell(updatedRowInd, GsUtils.NUM_DEADLINES_POSTPONED_COL, data["numDeadlinesPostponed"])
        self.wks.update_cell(updatedRowInd, GsUtils.NUM_OFFERS_COL, data["numOffers"])
        self.wks.update_cell(updatedRowInd, GsUtils.BAIL_AMOUNT_COL, data["bailAmount"])
        self.wks.update_cell(updatedRowInd, GsUtils.MINIMAL_PRICE_COL, data["minPrice"])
        self.wks.update_cell(updatedRowInd, GsUtils.DEV_EXPENSES_COL, data["devExpences"])
        #link = '=HYPERLINK("https://drive.google.com/drive/u/2/folders/' + folder_id + '", "קישור")'
        #self.wks.update_cell(updatedRowInd, GsUtils.LINK_TO_FOLDER_COL, link)
        self.wks.update_cell(updatedRowInd, GsUtils.IS_OPEN_FOR_BIDS_COL, data["is_open_for_bids"])
        ##self.wks.update_cell(misMichraz, GsUtils.NUM_PLOTS_COL, data["numPlots"])
        ##self.wks.update_cell(misMichraz, GsUtils.NUM_COMPOUNDS_COL, data["numCompounds"])
        '''
        
        log(f"google sheet -row Updated Successfully - {data['misMichraz']}")
        

        
        is_quota_exceeded = False
      except Exception as e:
        if "Quota exceeded" in str(e):  
          log(f"google sheet update row quota exceeded, sleep for 60 seconds") 
          time.sleep(60)
        else:
          log(f"google sheet update row exception, {str(e)}") 
          is_quota_exceeded = False


################################################################################
  def auctions_dict(self):
    return self.auctionsDict

################################################################################
  def isAuctionExist(self,misMichraz):
    return misMichraz.strip() in self.auctionsDict

################################################################################
  def __buildAuctionsDic(self):    
    all_values = self.wks.get_all_values()
    all_values = all_values[1:]
    if all_values != [[]]:
      index = 0
      for row in all_values:
        #print(row)
        id_val = row[GsUtils.ID_COL].strip()
        self.auctionsDict[id_val] = {"index" : index+2, "row": row}
        index = index + 1
################################################################################
  def __insHeaderColumns(self):

    self.wks.insert_row(["מס' סידורי", 
      "מס' מכרז", 
      "מס' יחידות", 
      "יישוב", 
      "ייעוד" , 
      "תאריך פתיחה", 
      "תאריך פרסום",
      "מועד אחרון להגשת הצעות",
      "פורסמה חוברת המכרז",
      ""
     ],1)

####################################################################################
  def createPlotsGS(self, dfs, log):
    
    # Specify the folder ID where you want to create the Google Sheet
    folder_id = self.driveUtils.current_auction_folder_id  #self.driveUtils.folderIdByFolderName(folderName)
    #delete previous plots
    plot_ids= self.driveUtils.getAllPlotIdS(folder_id)
    for plot_id in plot_ids:
      self.gc.del_spreadsheet(plot_id)
    log("after delete previous plots, founded " + str(len(plot_ids)))

    # Create a new Google Sheet
    #spreadsheet = self.gc.create('מגרשים', folder_id=folder_id)
    spreadsheet = self.gc.create('plots',folder_id=folder_id)
      # Open the new spreadsheet
    worksheet = spreadsheet.get_worksheet(0)  # Get the first sheet
    
    all_values_list = []
    for df in dfs:
      df.fillna('',inplace=True) # change any nulls for blank space
      all_values_list += df.values.tolist()
    unique_all_values_list = self.__uniqueAllValuesList(all_values_list)
    
    # Update the Google Sheet with DataFrame
    worksheet.update(unique_all_values_list)

  ####################################################################################
  def __uniqueAllValuesList(self, all_values_list):
    seen = []
    unique_arr =  []
    for item in all_values_list:
      if item not in seen:
        seen.append(item)
        unique_arr.append(item)   
    return unique_arr
    