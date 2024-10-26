from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pdfdownloader import PdfDownloader
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
import copy
import json
import traceback

class AuctionManager:

  YES_HEB = "כן"
  NO_HEB = "לא"
  
  def __init__(self,log):
    self.pdfDownloader = PdfDownloader() 
  
  ####################################################################################################################
  def getAuctionsData(self,auctionObjs,log,saveDataToExcel):
    dataArr = []
    idx=0
    for auctionObj in auctionObjs:
      #log(auctionObj.get_attribute('outerHTML'))
      idx=idx+1
      titleElem = auctionObj.find_element(By.CLASS_NAME, '_row')
      numUnits = ""
      if titleElem.find_elements(By.CLASS_NAME, 'ng-star-inserted'):
        #numUnits = titleElem.find_element(By.CLASS_NAME, 'ng-star-inserted').get_attribute("textContent").replace('יח"ד',"יחידות").replace(" ","_")
        numUnits = titleElem.find_element(By.CLASS_NAME, 'ng-star-inserted').get_attribute("textContent").replace('יח"ד',"").replace(" ","")
      
      
      spanElem = auctionObj.find_element(By.CLASS_NAME, 'mis-michraz') 
      misMichraz = spanElem.get_attribute("textContent")
      log("---------" + misMichraz + "--------" + " (" + str(idx) + "/" + str(len(auctionObjs)) + ")")
      rowElems = auctionObj.find_elements(By.CLASS_NAME, 'col-md-12') 
      #for rowElem in rowElems:
      rowElem = rowElems[0]
      spanElems = auctionObj.find_elements(By.CSS_SELECTOR, 'span') 
      city = ""
      vocation = ""
      openDate = ""
      publishDate = ""
      lastDate = ""
      isBookletPublished = AuctionManager.NO_HEB
      for ind, spanElem in enumerate(spanElems):
        if "יישוב:" in spanElems[ind-1].get_attribute("textContent")  :
          city = spanElems[ind].get_attribute("textContent")
        if "ייעוד:" in spanElems[ind-1].get_attribute("textContent")   :
          vocation = spanElems[ind].get_attribute("textContent")
        if ("תאריך פתיחה:" in spanElems[ind-2].get_attribute("textContent")) and ("תאריך" in spanElems[ind-1].get_attribute("textContent")) :
          openDate = spanElems[ind].get_attribute("textContent")
        if ("תאריך פרסום:" in spanElems[ind-2].get_attribute("textContent")) and ("תאריך" in spanElems[ind-1].get_attribute("textContent")) :
          publishDate = spanElems[ind].get_attribute("textContent")
        if ("מועד אחרון להגשת הצעות:" in spanElems[ind-1].get_attribute("textContent")) and ("/" in spanElems[ind].get_attribute("textContent")) :
          lastDate = spanElems[ind].get_attribute("textContent")
        if "פורסמה חוברת המכרז" in spanElems[ind].get_attribute("textContent")   :
          isBookletPublished = AuctionManager.YES_HEB
             
      dataArr.append({
        "misMichraz": misMichraz,
        "numUnits": numUnits,
        "city": city,
        "vocation": vocation,
        "openDate": openDate,
        "publishDate": publishDate,
        "lastDate": lastDate,
        "isBookletPublished": isBookletPublished
      })         
      #log(city + "XXX" + vocation + "XXX" + openDate + "XXX" + publishDate + "XXX" + isBookletPublished)
    custom_headers = ['מספר מכרז', 'עיר', 'תאריך פתיחה','תאריך פרסום',"מועד אחרון","פורסמה חוברת?"]
    #saveDataToExcel(dataArr, custom_headers) 
    #log(dataArr)
    
    return dataArr
    #return [item['misMichraz'] for item in dataArr]
  
  ####################################################################################################################
  def dealWithPdfs(self,driver,auctionNumberFormatted,folderName, isAuctionExistInGS, log):
    
    log("##############################" + str(isAuctionExistInGS))
    
    current_window = driver.current_window_handle
    
    pdf_data = None
    try:
      self.pdfDownloader.createFolder(folderName,log)
      url = "https://apps.land.gov.il/MichrazimSite/#/michraz/" + auctionNumberFormatted
      log(url)
      driver.get(url)
            
      #remove all forms from dom
      pdfIcons = None
      try:
        pdfIcons = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "icon-pdf")))
      except:
        log("pdfIcons not found A")
      if pdfIcons:
        forms = driver.find_elements(By.TAG_NAME, 'form')
        if forms:
          for form in forms:
            driver.execute_script("arguments[0].remove()", form)
     
      pdfIcons = None
      try:
        pdfIcons = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "icon-pdf")))
      except:
        log("pdfIcons not found B")
      if pdfIcons:
        log(f"Number of elements with class 'icon-pdf': {len(pdfIcons)}")
        self.__clickOnPdfs(driver,pdfIcons,log)
        
      is_open_for_bids = AuctionManager.NO_HEB
      bidElems = driver.find_elements(By.CLASS_NAME, 'send-hatzaa')  
      if bidElems and bidElems[0].tag_name == "a":
         is_open_for_bids = AuctionManager.YES_HEB
      if not bidElems:
         log("bid element not found")
      
      auction_type = ""
      auctionTypeElems = driver.find_elements(By.CLASS_NAME, 'michraz-title')
      if auctionTypeElems:
        auction_type = auctionTypeElems[0].get_attribute("textContent")

      #<a tabindex="0" target="_blank" class="send-hatzaa align-self-center ng-star-inserted" href="https://my.land.gov.il/HatzaaOnline/Home?michrazId=20200312">הגשת הצעה</a>
      
      pdf_data = self.__downloadAndGetDataFromPdfs(driver,auctionNumberFormatted,isAuctionExistInGS,log) 
      pdf_data["is_open_for_bids"] = is_open_for_bids
      pdf_data["auction_type"] = auction_type
    

      # Get the handles of all open windows
      all_windows = driver.window_handles

      # Close all windows except the current one
      for window in all_windows:
        if window != current_window:
          driver.switch_to.window(window)
          driver.close()
    
      driver.switch_to.window(current_window)
    except:
      log("exception from dealWithPdfs")  
      log(traceback.format_exc())

    return pdf_data

  ####################################################################################################################
  def __clickOnPdfs(self,driver,elements,log):
    for element in elements:
      try:
        log("try to clickonpdf-----------") 
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        parent_element = driver.execute_script("return arguments[0].parentNode;", element)
        driver.execute_script("arguments[0].scrollIntoView(true);", parent_element)
        driver.execute_script("arguments[0].click();", element)
      except Exception as e:
         log(f"exception!!!! clickOnPdfs {e}")
     

  ####################################################################################################################
  def __downloadAndGetDataFromPdfs(self,driver,auctionNumberFormatted,isAuctionExistInGS,log):
    numDeadlinesPostponed = 0 
    firstPublishDataInBytes = None
    outer_html = driver.execute_script("return document.documentElement.outerHTML")
    # Parse the outer HTML with BeautifulSoup
    soup = BeautifulSoup(outer_html, "html.parser")
    forms = soup.find_all('form')
        
    log("num forms=" + str(len(forms)))
    max_postpone_date = datetime.strptime("1970-01-01", '%Y-%m-%d').date() 
    attr_json_obj_that_has_max_pospone_date = {}
    latest_booklet_date = datetime.strptime("1970-01-01", '%Y-%m-%d').date() 
    latest_booklet = {}
    bookletDataInBytes = None
    
    for form in forms:
      attr_json_obj = {}
      for item in form:
        pattern = r'<input name="([^"]+)" type="hidden" value="([^"]+)"'
        # Use re.search() to find the first match
        match = re.search(pattern, str(item))
        if match:
          name = match.group(1)
          value = match.group(2)
          attr_json_obj[name] = value
      if attr_json_obj['MichrazID'] == auctionNumberFormatted and (not "דחיית" in attr_json_obj['Teur']):
        self.pdfDownloader.download(attr_json_obj, log)
      if "דחיית" in attr_json_obj['Teur']:
        postpone_date = datetime.strptime(attr_json_obj['UpdateDate'].split('T')[0], '%Y-%m-%d').date()
        if(max_postpone_date < postpone_date):
          max_postpone_date = postpone_date
          attr_json_obj_that_has_max_pospone_date = copy.deepcopy(attr_json_obj)
        numDeadlinesPostponed = numDeadlinesPostponed + 1
      if "ראשון" in attr_json_obj['Teur'] and (not isAuctionExistInGS):
        firstPublishDataInBytes = self.pdfDownloader.getFileContent(attr_json_obj)
        log("len first publish pdf data=" + str(len(firstPublishDataInBytes)))
      if "חוברת" in attr_json_obj['Teur']:
        booklet_date = datetime.strptime(attr_json_obj['UpdateDate'].split('T')[0], '%Y-%m-%d').date()
        if(latest_booklet_date < booklet_date):
          latest_booklet_date = booklet_date
          latest_booklet = copy.deepcopy(attr_json_obj)
        
    if len(latest_booklet) > 0:
      bookletDataInBytes = self.pdfDownloader.getFileContent(latest_booklet)
      log("len booklet pdf data=" + str(len(bookletDataInBytes)))
    
    log("max_postpone_obj---" + str(attr_json_obj_that_has_max_pospone_date))    
    if len(attr_json_obj_that_has_max_pospone_date)>0:
      self.pdfDownloader.download(attr_json_obj_that_has_max_pospone_date, log)

    return {"numDeadlinesPostponed": numDeadlinesPostponed, "firstPublishDataInBytes": firstPublishDataInBytes, "bookletDataInBytes": bookletDataInBytes}
  