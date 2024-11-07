import os.path
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from datetime import datetime
import json
from google.oauth2 import service_account


SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS = 'client_secret.json'
TOKENJSON = 'tokenDriveUpload.json'

class DriveUtils:

  auctions_folder_id = '1zisWhpuN0ntGo4TMjEerHLV10UBltp21'
  current_auction_folder_id =""
  
  ##################################################################################################
  def __init__(self):
    creds =self.__getCreds()   
    self.service = build('drive', 'v3', credentials=creds)  
    self.folder_list = self._listItems(DriveUtils.auctions_folder_id, 'application/vnd.google-apps.folder') 
    
  ##################################################################################################
  def __getCreds(self):

    with open("googlesheetcreds.json", "r") as file:
      service_account_info = json.load(file)

    credentials = service_account.Credentials.from_service_account_info(
      service_account_info,
      scopes=["https://www.googleapis.com/auth/drive"]
    )

    return credentials

  ###########################################################################################################################  
  def __create_token_json_from_client_secrets_file(self):
    
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
    creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(TOKENJSON, 'w') as token:
      token.write(creds.to_json())

    return creds 
  
  ###########################################################################################################################  
  def mkdir(self, dirName,log):
    listedFolders = self.folder_list
    listedFolderNames = [item['name'].strip() for item in listedFolders]
    if not dirName in listedFolderNames: 
      file_metadata = {
        'name': dirName,
        "parents": [DriveUtils.auctions_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
      }
      file = self.service.files().create(body=file_metadata, fields='id').execute()
      DriveUtils.current_auction_folder_id = file.get('id')
      log(f"driveutils = new folder '{dirName}' ID = {file.get('id')}")
    else:
      DriveUtils.current_auction_folder_id = next(filter(lambda item: item["name"] == dirName, listedFolders), None)["id"]
      log(f"driveutils = {dirName} already exists , dirid={DriveUtils.current_auction_folder_id}")      
  ###########################################################################################################################  
  def _listItems(self, folder_id, mime_type):
    page_token = None
    folders = []
    while True:
      # Call the Drive v3 API
      results = (
          self.service.files()
          .list(q=f"'{folder_id}' in parents and mimeType='{mime_type}'",
                spaces="drive",
                fields="nextPageToken, files(id, name)",
                pageToken = page_token)
          .execute()
      )
      items = results.get("files", [])
      for item in items:
        folders.append(item)
      page_token = results.get('nextPageToken')
      if page_token is None:
        break 
    return folders 
  
 ###########################################################################################################################  
  def uploadFile(self, filename, fileInMemory,log):
    log(f"current_auction_folder_id={DriveUtils.current_auction_folder_id}")
    current_pdf_files = self._listItems(DriveUtils.current_auction_folder_id, 'application/pdf')
    current_pdf_file_names = [item['name'] for item in current_pdf_files]
    if not filename in current_pdf_file_names: 
      file_metadata = {'name': filename,
                     "parents": [DriveUtils.current_auction_folder_id]
                     }
      media = MediaIoBaseUpload(io.BytesIO(fileInMemory), mimetype='application/pdf', resumable=True)
      request = self.service.files().create(
      media_body=media,
      body=file_metadata)
      response = None
      while response is None:
        status, response = request.next_chunk()
        if status:
          log("Uploaded %d%%." % int(status.progress() * 100))
      log(f"google drive {filename} saved successfully") 
    else:
      log(f"google drive {filename} already exists")  

###########################################################################################################################
  def folderIdByFolderName(self,folderName):
    listedFolders = self.folder_list
    result = next((item for item in listedFolders if item['name'] == folderName), None)
    if result is not None:
      return result["id"]
    else:
      return None   

###########################################################################################################################
  def isFileAlreadyExists(self, filename):
    current_pdf_files = self._listItems(DriveUtils.current_auction_folder_id, 'application/pdf')
    current_pdf_file_names = [item['name'] for item in current_pdf_files]
    return filename in current_pdf_file_names 

###########################################################################################################################
  def getAllPlotIdS(self, folder_id):     
    all_plots = self._listItems(DriveUtils.current_auction_folder_id, 'application/vnd.google-apps.spreadsheet')
    return  [item['id'] for item in all_plots] 

###########################################################################################################################  
  def __buildFoldersDic(self):
    page_token = None
    dic = {}
    folder_id = '1zisWhpuN0ntGo4TMjEerHLV10UBltp21'
    mime_type = 'application/vnd.google-apps.folder'
    while True:
      # Call the Drive v3 API
      results = (
          self.service.files()
          .list(q=f"'{folder_id}' in parents and mimeType='{mime_type}'",
                spaces="drive",
                fields="nextPageToken, files(id, name, modifiedTime)",
                pageToken = page_token)
          .execute()
      )
      items = results.get("files", [])
      for item in items:
        if dic.get(item["name"]):
          dic[item["name"]].append(item)
        else:  
          dic[item["name"]] = [item]

      page_token = results.get('nextPageToken')
      if page_token is None:
        break 
    
    return dic 

###########################################################################################################################  
  def __delete_folder(self, folder_id):
    try:
      self.service.files().delete(fileId=folder_id).execute()
      print(f"Folder with ID {folder_id} deleted successfully.")
    except Exception as e:
      print(f"An error occurred: {e}")    

###############################################################################################################################      
  def delete_duplicate_name_folders(self):
    dic = self.__buildFoldersDic()
    for ind, key in enumerate(dic):
      if(len(dic[key]) > 1):
        max_date = datetime.strptime("1970-01-01", '%Y-%m-%d').date()
        for folder in dic[key]:
          if datetime.strptime(folder["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ").date() > max_date:
            max_date = datetime.strptime(folder["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ").date()  
        for folder in dic[key]:
          if datetime.strptime(folder["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ").date() < max_date:
            self.__delete_folder(folder["id"])
    
