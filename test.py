import pyautogui
import pygetwindow as gw
from PIL import Image

# 获取所有屏幕的信息
screens = gw.getAllWindows()

for i, screen in enumerate(screens):
    # 获取屏幕的区域
    x = screen.left
    y = screen.top
    width = screen.width
    height = screen.height

    # 截取屏幕截图
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    print("1")