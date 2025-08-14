"""
Script to quickly create daytypes in MEASUR
"""
import pyautogui
import time

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


print("Starting in 5")
time.sleep(5)

for day in weekdays:
    pyautogui.typewrite(str(day))
    pyautogui.press('tab')
    pyautogui.typewrite("52.14285715")
    pyautogui.press('tab')
    pyautogui.press('tab')