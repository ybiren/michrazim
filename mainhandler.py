from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException
import time
from auctionmanager import AuctionManager
from pdfparser import PdfParser
from googlesheetutils import GsUtils
import pandas as pd
import subprocess
import logging 
import os
import json
import openpyxl
import datetime
from pdfdownloader import PdfDownloader
import tabula.io as tabula
import pyautogui
import traceback
from  mailsender import MailSender
import configparser

class MainHandler:
  
  def __init__(self):
    self.michrazim_url = 'https://apps.land.gov.il/MichrazimSite/#'
    self.exceution_time = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    self.reciever_mail = ""
    self.pause_bwtween_auctions_in_seconds = 0
    self.day_log_files_expires = 30 #default is 30
    self.curr_auction_idx = 0
    self.auctionObjs = []
    self.auctionDataArr = []
    self.driver = webdriver.Chrome()

#################################################################################
  def main(self, checkboxes):
    try:
      if not os.path.exists("logs"):
        os.makedirs("logs") 
      self.log("read config")
      self.__read_config("config.ini")
      self.log("killProcesses")
      self.__killProcesses()
      self.log("initSeleniumDriver")
      self.driver = self.__initSeleniumDriver()
      self.log("del_old_log_files")
      self.__del_old_log_files()
      self.log("navigateToHomePage")
      self.__navigateToHomePage(self.driver,checkboxes)
      self.log("__get_all_auctions")
      self.auctionObjs = self.__get_all_auctions(self.driver)
          
      #auctionObjs = auctionObjs[:200].copy()
      self.log("init gsUtils")
      gsUtils = GsUtils()
      self.log("init auctionManager")
      auctionManager = AuctionManager(self.log)
      self.log("init mailSender")
      mailSender = MailSender()
      self.log("init pdfParser")
      pdfParser = PdfParser()
      
      '''
      temp_arr = []
      for index,auctionObj in enumerate(self.auctionObjs):
        spanElem = self.auctionObj.find_element(By.CLASS_NAME, 'mis-michraz') 
        misMichraz = spanElem.get_attribute("textContent")
        misMichraz = misMichraz.strip()
      
        if ("320/2024" in misMichraz) :
        #if  ("407" in misMichraz) or ("468" in misMichraz) :
        #if not gsUtils.isAuctionExist(misMichraz):
          temp_arr.append(auctionObj)
          print(misMichraz)
          print("yes!!!!!") 
      self.auctionObjs = temp_arr.copy()
      ''' 

      self.log("before create auctionDataArr")
      self.auctionDataArr = auctionManager.getAuctionsData(self.auctionObjs,self.log, self.saveDataToExcel)
      self.log("after create auctionDataArr")
    
      #for idx, auctionData in enumerate(auctionDataArr):
      self.curr_auction_idx = 0
      while self.curr_auction_idx < len(self.auctionDataArr):
        try:
          auctionData = self.auctionDataArr[self.curr_auction_idx]
          self.log(str(self.curr_auction_idx) + "-----------------------------------" + str(len(self.auctionDataArr)))
          auctionNumber = auctionData['misMichraz'].strip()
          
          if not auctionData['numUnits'].isnumeric() and auctionNumber in gsUtils.auctions_dict(): 
            auctionData['numUnits'] = gsUtils.auctions_dict()[auctionNumber]["row"][GsUtils.UNITS_COL -1]
            self.log("numUnits is not numeric" + str(auctionData['numUnits']));

          #time.sleep(2)
          self.driver.get(f"{self.michrazim_url}/search")
          #time.sleep(2)
          numerator, denominator = map(str, auctionNumber.split('/'))
          auctionNumberFormatted = denominator.strip() + numerator.strip().zfill(4)
          folderName = f"{auctionNumberFormatted}-{auctionData['city']}-{auctionData['vocation']}-{auctionData['numUnits']}".replace("/","_")
          isAuctionExist = gsUtils.isAuctionExist(auctionNumber)
          self.__keepAlive()   
          pdfData = auctionManager.dealWithPdfs(self.driver, auctionNumberFormatted, folderName, isAuctionExist, self.log)
          if pdfData!=None:
            auctionData["numDeadlinesPostponed"] = pdfData["numDeadlinesPostponed"] 
            self.log(f"numDeadlinesPostponed= {auctionData["numDeadlinesPostponed"]}")
            auctionData["auction_type"] = self.__remove_units_from_auction_type(pdfData["auction_type"].replace(auctionNumber, "")) 
            self.__set_is_open_for_bids(mailSender, gsUtils, auctionData, pdfData, auctionNumber, isAuctionExist)
            self.__set_num_plots_and_compounds(pdfParser, auctionData, pdfData, auctionNumberFormatted)
            self.__set_booklet_data(pdfParser, gsUtils, auctionData, pdfData, auctionNumberFormatted, auctionNumber)
            gsUtils.integrate(auctionData, self.log)
            #sleeping for 2 minutes
        except Exception as e:
          self.log("exception dealwithpdfs:" + str(e))  
          self.log(traceback.format_exc())
          if("שגיאה" in str(e)): #pdf downloader blocked us
            self.log("sleep for 180 seconds")
            time.sleep(180)
        self.curr_auction_idx+=1
        time.sleep(self.pause_bwtween_auctions_in_seconds)
    except Exception as e:
      self.curr_auction_idx = -1 # exception indication
      self.log("exception="  + str(e))
    finally: 
      self.log("end!!")
      self.driver.quit()


#################################################################################
  def log(self,msg):
    #print(msg.encode('utf-8').decode('utf-8'))
    filename = f"logs/log_{self.exceution_time}.txt"
    with open(filename,'a',encoding='utf-8') as file:
      file.write(datetime.datetime.now().strftime('%H:%M') + "    " + str(msg) + "\n")  
      file.close()  

#################################################################################
  def __read_config(self, file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    self.reciever_mail = config.get('General', 'reciever_mail')
    self.pause_bwtween_auctions_in_seconds = int(config.get('General', 'pause_bwtween_auctions_in_seconds'))
    self.day_log_files_expires = int(config.get('General', 'day_log_files_expires'))
    
#################################################################################
  def __killProcesses(self): 
    self.log('before terminating chrome')
    # Terminate all running Chrome processes
    for num in range(1, 5):
      #subprocess.call("TASKKILL /f /IM CHROME.EXE")
      subprocess.call("TASKKILL /f /IM CHROMEDRIVER.EXE")
      #subprocess.call("TASKKILL /f /IM EXCEL.EXE")
      #os.system("taskkill /f /IM EXCEL.exe")

    self.log('after terminating chrome')
  
#################################################################################
  def __initSeleniumDriver(self):
    # Setup Chrome options to run in headless mode
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--log-level=3") # Fatal errors only
    #options.add_argument("--headless")
    options.add_argument("--headless=new")
    #options.add_argument("--disable-gpu")
    options.add_argument("--window-position=-2400,-2400")
  
    #driver_path = r'C:\Users\yossi\.wdm\drivers\chromedriver\win64\127.0.6533.72\chromedriver-win32\chromedriver.exe'
    # Setup WebDriver
    #return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return webdriver.Chrome(options=options)

#################################################################################
  def __del_old_log_files(self):
  
    folder_path = 'logs'
    # Get the current time
    current_time = time.time()
    # Iterate over all files in the folder
    for filename in os.listdir(folder_path):
      file_path = os.path.join(folder_path, filename)
      # Check if it's a file (not a directory)
      if os.path.isfile(file_path):
        # Get the file's creation time
        file_creation_time = os.path.getctime(file_path)
        # Check if the file is older than 30 days
        if (current_time - file_creation_time) > (self.day_log_files_expires * 24 * 60 * 60):
            os.remove(file_path)
            self.log(f'Deleted log {file_path}')

#################################################################################
  def saveDataToExcel(dataArr, custom_headers):
    df = pd.DataFrame(dataArr)
    df.columns = custom_headers
    excel_file = "output.xlsx"
    df.to_excel(excel_file, index=False)
  
#################################################################################
  def __navigateToHomePage(self, driver, checkboxes):
    #url = "https://apps.land.gov.il/MichrazimSite/#/homePage"
    self.log("before navigating to url")
    driver.get(f"{self.michrazim_url}/homePage")
    self.log("after navigating to url")
    enterBtn = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.CLASS_NAME, "button-enter")))
    self.log("after enter")
    enterBtn.click()
    
    p_multiselect_label = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.CLASS_NAME, "p-multiselect-label")))
    p_multiselect_label.click()
  
    # Wait until at least one element is clickable
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.TAG_NAME, "p-multiselectitem")))
    p_multiselectitems = driver.find_elements(By.TAG_NAME, "p-multiselectitem")
    
    if checkboxes != None:
      for i, checkbox in enumerate(checkboxes):
        if checkbox.get() == 1:
          p_multiselectitems[i].find_element(By.CLASS_NAME, "p-checkbox").click()
    else:
      p_multiselectitems[4].find_element(By.CLASS_NAME, "p-checkbox").click()   #  מכרז למגרש בלתי מסוים


    srchBtn = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.CLASS_NAME, "icon-search")))
    self.log("after search")
    srchBtn.click()
    self.log("after search btn click")

#################################################################################
  def __keepAlive(self):
    pyautogui.FAILSAFE = False
    screenWidth, screenHeight = pyautogui.size()
    currentMouseX, currentMouseY = pyautogui.position()
    screenWidth, screenHeight = pyautogui.size()
    pyautogui.moveRel( 15, 0)
    currentMouseX, currentMouseY = pyautogui.position()
    pyautogui.moveRel(-15, 0)
    pyautogui.press('left')

#################################################################################
  def __get_all_auctions(self, driver):
    prev_scroll_height = driver.execute_script("return document.body.scrollHeight;")  
    scroll_height = -1
    is_end_scrolling = False    
    while not is_end_scrolling:
      auctionObjs = WebDriverWait(driver, 30).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "app-michraz-details")))
      self.log('len(auctionObjs)=' + str(len(auctionObjs)))
      driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
      time.sleep(2)
      scroll_height = driver.execute_script("return document.body.scrollHeight;")
      print(" prev_scroll_height=" + str(prev_scroll_height) + " scroll_height=" + str(scroll_height))
      if scroll_height == prev_scroll_height:
        is_end_scrolling = True
      else:
        prev_scroll_height = scroll_height  
    return auctionObjs

################################################################################
  def __set_is_open_for_bids(self, mailSender, gsUtils, auctionData, pdfData, auctionNumber, isAuctionExist):
    ##mailSender.send("yossi1316@gmail.com", auctionNumber, auctionData, self.michrazim_url, self.log)
    ##time.sleep(3600)
    if not isAuctionExist:
      auctionData["is_open_for_bids"] = pdfData["is_open_for_bids"] 
      self.log(f"is_open_for_bids= {auctionData["is_open_for_bids"]}")
    else:   
      if gsUtils.auctions_dict()[auctionNumber]["row"][GsUtils.IS_OPEN_FOR_BIDS_COL -1] != AuctionManager.YES_HEB:
        auctionData["is_open_for_bids"] = pdfData["is_open_for_bids"] 
        self.log(f"is_open_for_bids= {auctionData["is_open_for_bids"]}")
        # המכרז נפתח להצעות
        if auctionData["is_open_for_bids"] == AuctionManager.YES_HEB and  (auctionNumber in gsUtils.auctions_dict()) and gsUtils.auctions_dict()[auctionNumber]["row"][GsUtils.IS_OPEN_FOR_BIDS_COL -1] == AuctionManager.NO_HEB:
          self.log(f"send mail to {self.reciever_mail} {auctionNumber} ,opened for bids")
          mailSender.send(self.reciever_mail, auctionNumber, auctionData, self.michrazim_url, self.log)
      else:
        auctionData["is_open_for_bids"] = AuctionManager.YES_HEB

################################################################################
  def __set_num_plots_and_compounds(self, pdfParser, auctionData, pdfData, auctionNumberFormatted):

    auctionData["numPlots"] = " "
    auctionData["numCompounds"] = " "
    if pdfData["firstPublishDataInBytes"] != None:
      numPlotsAndCompounds= pdfParser.numPlotsAndCompounds(pdfData["firstPublishDataInBytes"], auctionNumberFormatted, self.log)
      auctionData["numPlots"] = numPlotsAndCompounds["num_plots"]
      auctionData["numCompounds"] = numPlotsAndCompounds["num_compounds"]

################################################################################
  def __set_booklet_data(self, pdfParser, gsUtils, auctionData, pdfData, auctionNumberFormatted, auctionNumber):

    auctionData["devExpences"] = " "
    auctionData["minPrice"] = " "
    auctionData["bailAmount"] = " "
    auctionData["numOffers"] = " "
    if pdfData["bookletDataInBytes"] != None:
      self.log("before parse booklet " + str(auctionNumber))
      bookletData = pdfParser.bookletData(pdfData["bookletDataInBytes"], auctionNumberFormatted, self.log)
      auctionData["devExpences"] = bookletData["devExpences"]
      auctionData["minPrice"] = bookletData["minPrice"]
      auctionData["bailAmount"] = bookletData["bailAmount"]
      auctionData["numOffers"] = bookletData["numOffers"]
      self.log("after parse booklet " + str(auctionNumber)) 
      if len(bookletData["all_relevant_dfs"]) > 0:
        self.log("before create plot gs " + str(auctionNumber) + "len all relevant dfs=" + str(len(bookletData["all_relevant_dfs"]))) 
        gsUtils.createPlotsGS(bookletData["all_relevant_dfs"], self.log)       
        self.log("after create plot gs " + str(auctionNumber)) 

  ################################################################################
  def __remove_units_from_auction_type(self, auction_type):
    if 'יח"ד' in auction_type:
      words = auction_type.split()[:-2]
      stripped_words = [word.strip() for word in words]
      return  " ".join(stripped_words)
    return  auction_type

################################################################################
  def quitSeleniumDriver(self):
    self.driver.quit()
