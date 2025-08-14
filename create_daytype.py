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
    if day == 'Sunday':
        pyautogui.typewrite("52.14285716")
    else:
        pyautogui.typewrite("52.14285714")
    pyautogui.press('tab')
    pyautogui.press('tab')