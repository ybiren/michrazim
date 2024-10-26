from multilingual_pdf2text.pdf2text import PDF2Text
from multilingual_pdf2text.models.document_model.document import Document
#import logging
from pdf2image import convert_from_path,convert_from_bytes
from PIL import Image
import pytesseract
import os


class PdfReader:

    def __init__(self):
      #logging.basicConfig(level=logging.INFO)
      pytesseract.pytesseract.tesseract_cmd = f'{os.getcwd()}\\ocr\\tesseract.exe'
###################################################################################################################################3333
    def read(self):
      print("image convert")
      file = "1.pdf"
      pages = convert_from_path(file, 200, poppler_path=f'{os.getcwd()}\\poppler\\poppler-24.02.0\\Library\\bin')  
      print("text convert")
      
      text= ""
      for count, page in enumerate(pages):
        print(count)
        #page.save(f'xxx\\out{count}.png', 'PNG')
        #image_path = r'D:\yossi\python\michrazim\xxx\out1.png'
        #img = Image.open(image_path)
        text = text + "\n" + pytesseract.image_to_string(page, lang='heb')
      
      return text
###################################################################################################################################3333
    def convertFromBytes(self, data, first_page, last_page):
      pages = convert_from_bytes(data["content"], dpi=500, poppler_path=f'{os.getcwd()}\\poppler\\poppler-24.02.0\\Library\\bin',first_page=first_page,last_page=last_page)  
      text= ""
      for count, page in enumerate(pages):
          #page.save(f'xxx\\out{count}.png', 'PNG')
          #image_path = r'D:\yossi\python\michrazim\xxx\out1.png'
          #img = Image.open(image_path)
          text = text + "\n" + pytesseract.image_to_string(page, lang='heb')
      
      return text



