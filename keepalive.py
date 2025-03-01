import threading
import time
import pyautogui

class KeepAlive:
    def __init__(self):
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
    
    def keepAlive(self):
        print("keep alive!!!!!")
        pyautogui.FAILSAFE = False
        screenWidth, screenHeight = pyautogui.size()
        currentMouseX, currentMouseY = pyautogui.position()
        pyautogui.moveRel(15, 0)
        pyautogui.moveRel(-15, 0)
        pyautogui.press('left')

    def run(self):
        print("runnnn")
        while self.running:
            self.keepAlive()
            time.sleep(60)  # Wait for 1 minute

    def start(self):
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

# Usage
