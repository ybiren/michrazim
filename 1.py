import os
import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkinter import messagebox
import threading
import psutil
from mainhandler import MainHandler


##stream_handler = logging.StreamHandler()
##stream_handler.setLevel(logging.DEBUG)
##logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
##                    handlers=[logging.FileHandler("my_log.log", mode='a'),
##                              stream_handler])
auction_types_options_txt = ['מכרז פומבי רגיל', 'מחיר מטרה', 'דיור במחיר מופחת', 'מכרז ייזום', 'מכרז למגרש בלתי מסוים', 'הרשמה והגרלה', 'דיור להשכרה', 'מכרזי עמידר', 'מכרזי החברה לפיתוח עכו']
vocation_options_text = ['בנייה רוויה' , 'בניה נמוכה/צמודת קרקע']

checkboxes = []
checkbuttons = []

# Create the main window
root = tk.Tk()
root.title("מכרזים 1.2")
root.geometry("800x600")
root.configure(bg='lightblue')
seconds_from_start = 0

main_handler = MainHandler()

################################################################################
def seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds_remaining = seconds % 60
    return hours, minutes, seconds_remaining

################################################################################
def refresh_window(auction_ind_label, seconds_from_start_label, start_button, checkbuttons):
    global seconds_from_start
    #print("focusing!!!")
    if thread.is_alive():
      start_button.config(state='disabled')
      for checkbutton in checkbuttons: 
        checkbutton.config(state='disabled')
      
      if len(main_handler.auctionDataArr)>0 and len(main_handler.auctionDataArr) == main_handler.curr_auction_idx:
        messagebox.showinfo("", "הסתיים בהצלחה")
        psutil.Process(os.getpid()).terminate()
      
      if main_handler.curr_auction_idx == -1:
        messagebox.showinfo("", "הסתיים בכשלון,לפרטים ראה קובץ לוג")
        psutil.Process(os.getpid()).terminate()
      
      if len(main_handler.auctionDataArr) > 0:
        auction_ind_label.config(text=f"{(main_handler.curr_auction_idx + 1)} \\ {len(main_handler.auctionDataArr)}")
      else:
        if len(main_handler.auctionObjs) == 0: 
          auction_ind_label.config(text=f"...אוסף מידע")
        else: 
          auction_ind_label.config(text=f"מכרזים {len(main_handler.auctionObjs)}")
      
      seconds_from_start+=1
      hours, minutes, seconds = seconds_to_hms(seconds_from_start)
      seconds_from_start_label.config(text = f"{str(hours).zfill(2)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}",borderwidth=1, relief="solid", padx=10, pady=10)
      
    root.after(1000, refresh_window, auction_ind_label, seconds_from_start_label, start_button, checkbuttons)  # Refresh every 1000 milliseconds (1 second)

################################################################################
def on_closing():
  main_handler.quitSeleniumDriver()
  psutil.Process(os.getpid()).terminate()

#סוגי מכרזים
for ind,option in enumerate(auction_types_options_txt):
  var = tk.IntVar()
  checkbox = tk.Checkbutton(root, text="", variable=var, bg='lightblue')
  label = tk.Label(root, text=option, bg='lightblue')
  if ind <4:
    label.grid(row=ind, column=2, sticky='e')
    checkbox.grid(row=ind, column=3, sticky='w')
  else: 
    label.grid(row=ind-4, column=0, sticky='e')
    checkbox.grid(row=ind-4, column=1, sticky='w')
  
  checkboxes.append(var)
  checkbuttons.append(checkbox)

#ייעוד
for ind,option in enumerate(vocation_options_text):
  var = tk.IntVar()
  vocation_checkbox = tk.Checkbutton(root, text="", variable=var, bg='lightblue')
  label = tk.Label(root, text=option, bg='lightblue')
  label.grid(row=ind+10, column=2, sticky='e')
  vocation_checkbox.grid(row=ind+10, column=3, sticky='w')
  checkboxes.append(var)
  checkbuttons.append(vocation_checkbox)
  
  

thread = threading.Thread(target=main_handler.main, args=(checkboxes,))
start_button = tk.Button(root, text="הפעלה", font=font.Font(size=22), bg='lightgray', command=thread.start)
root.grid_rowconfigure(5, weight=0, minsize=50)  # This makes the empty row expandable
start_button.grid(row=7,column=2, sticky='e')

auction_ind_label = tk.Label(root, text="", font=font.Font(size=24), bg='lightblue')
auction_ind_label.grid(row=7,column=1, sticky='w')

seconds_from_start_label = tk.Label(root, text="", font=font.Font(size=24), bg='lightblue')
seconds_from_start_label.grid(row=8,column=1, sticky='w')
      

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.protocol("WM_DELETE_WINDOW", on_closing)

seconds_from_start = 0
refresh_window(auction_ind_label, seconds_from_start_label, start_button, checkbuttons)



# Run the application
root.mainloop()


##if __name__ == '__main__':
  #dfs = tabula.read_pdf('file.pdf', stream=True,pages="all", pandas_options={'header': None})
  #print("bookletdata num tables=" + str(len(dfs)))
  ##main()