from requests_html import HTMLSession
import requests
import os
from driveutils import DriveUtils

class PdfDownloader:

    def __init__(self):
      self.driveUtils = DriveUtils() 
      #if not os.path.isdir("auctions"):
        #os.mkdir("auctions")
      #dir_path = os.path.join("auctions",folderName)
      #if not os.path.isdir(dir_path):
        #os.mkdir(dir_path)
      self.fileContentUrl = 'https://apps.land.gov.il/MichrazimSite/api/MichrazDetailsApi/GetFileContent'                           
###########################################################################################################    
    def createFolder(self, folderName, log):
      self.driveUtils.mkdir(folderName, log)
    

###########################################################################################################    

    def download(self,data,log):

        #self.__savePdfToLocal(url,data,log)
        self.__savePdfToGoogleDrive(self.fileContentUrl,data,log)
        
        #page = requests.get(url)  

        #with open("Output.txt", "w") as text_file:
            #text_file.write(str(page.content))

        # Data to include in the POST request
        #data = {
            #'MichrazID': '20230263',
            #'DocName': 'פרסום דחיית מועדים.pdf',
            #'FileType': 'application/pdf',
            #'RowID': '71029',
            #'Teur': 'פרסום דחיית מועדים',
            #'MahutMismachID': '0',
            #'PirsumType': '3'
        #}
###########################################################################################################    
    def getFileContent(self,data):
      #data = {'MichrazID': '20220469', 'Size': '4765223', 'FileType': 'application/pdf', 'RowID': '1', 'Teur': 'חוברת המכרז', 'DocName': 'חוברת המכרז.pdf', 'UpdateDate': '2023-05-23T10:53:02.23+03:00', 'Url': 'null', 'MahutMismachID': '0', 'PirsumType': '2'}
      response = requests.post(self.fileContentUrl, data=data)
      return response.content

###########################################################################################################    
    def __savePdfToLocal(self,url,data,log):
      dir_path = os.path.join("auctions",data['MichrazID'])
      pdfFileName= os.path.join(dir_path, data['Teur'] + '_' + data['UpdateDate'].split('T')[0] + '.pdf')
      if os.path.isfile(pdfFileName):
        log(data['MichrazID'] + " : " + pdfFileName + " already exists.")
      else:
        # Send the POST request
        response = requests.post(url, data=data)
        if response.status_code == 200:
          with open(pdfFileName, 'wb') as f:
            f.write(response.content)
            log(data['MichrazID'] + " : " + pdfFileName + " saved successfully.")
        else:
          #print(response.content)
          log(data['MichrazID'] + " : " + "Failed to save " + pdfFileName + ". Status code:" +  str(response.status_code))

    ###########################################################################################################    
    def __savePdfToGoogleDrive(self,url,data,log):          
      pdf_file_name= data['Teur'] + '_' + data['UpdateDate'].split('T')[0] + '.pdf'
      
      if not self.driveUtils.isFileAlreadyExists(pdf_file_name):
        response = requests.post(url, data=data)
        if response.status_code == 200:
          self.driveUtils.uploadFile(pdf_file_name, response.content,log)
        else:
          #print(response.content)
          log(data['MichrazID'] + " : " + "Failed to download " + pdf_file_name + ". Status code:" +  str(response.status_code))
      else:
        log("pdf file already exists!!!!!--" + pdf_file_name)