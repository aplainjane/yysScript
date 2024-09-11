import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import pyautogui
import threading
import time
from pynput import keyboard
import cv2
import numpy as np
import random

class ImageClickApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片点击坐标设定 by ky")

        # 保存上传的图片路径和点击坐标
        self.image_paths = []
        self.click_positions = {}

        # 创建GUI界面
        self.upload_button = tk.Button(root, text="上传图片", command=self.upload_images)
        self.upload_button.pack(pady=10)

        self.start_button = tk.Button(root, text="开始识别并点击", command=self.start_recognition)
        self.start_button.pack(pady=10)

        # 用于显示图片的 Frame 和 Canvas
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(pady=10)

        self.canvas_list = []

        # 用于显示点击坐标的 Label
        self.coordinates_label = tk.Label(root, text="点击坐标：")
        self.coordinates_label.pack(pady=10)

        # 用于显示调试信息的 Text 小部件
        self.debug_text = tk.Text(root, height=10)
        self.debug_text.pack(pady=10)

        # 保存 tkinter 图片对象（防止垃圾回收）
        self.tk_images = {}

        # 标记是否在运行
        self.running = False

        # 标记是否正在等待用户按下'v'键
        self.waiting_for_v = False

        # 创建监听器线程
        self.create_esc_listener()

    def append_debug_info(self, message):
        """将调试信息追加到Text控件中"""
        self.debug_text.insert(tk.END, message + "\n")
        self.debug_text.see(tk.END)  # 自动滚动到最后

    def upload_images(self):
        # 选择多张图片
        file_paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_paths:
            for img_path in file_paths:
                self.image_paths.append(img_path)
                self.append_debug_info(f"已上传图片: {img_path}")
                # 为每张图片设置点击坐标
                self.append_debug_info(f"请移动鼠标到要设置为点击位置的地方，然后按下'v'键以确认 {img_path} 的点击坐标")
                self.wait_for_v_key(img_path)
                # 显示上传的图片
                self.display_uploaded_images()

    def wait_for_v_key(self, img_path):
        self.waiting_for_v = True
        def on_press(key):
            try:
                if key.char == 'v' and self.waiting_for_v:
                    self.waiting_for_v = False
                    x, y = pyautogui.position()
                    self.click_positions[img_path] = (x, y)
                    self.append_debug_info(f"设置图片 {img_path} 的点击坐标为: {x}, {y}")
                    self.display_click_coordinates()  # 更新界面上显示的点击坐标
                    return False
            except AttributeError:
                pass  # 忽略其他按键

        # 创建一个新的线程来监听键盘事件
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        # 等待监听器结束
        while self.waiting_for_v:
            time.sleep(0.1)

    def start_recognition(self):
        if not self.image_paths:
            self.append_debug_info("请先上传图片并设置点击坐标。")
            return
        self.running = True
        self.append_debug_info("开始识别并点击...")
        recognition_thread = threading.Thread(target=self.recognize_and_click)
        recognition_thread.start()

    def recognize_and_click(self):
        while self.running:
            for img_path in self.image_paths:
                if not self.running:  # 检查停止标志
                    break
                # 读取图片
                template = cv2.imread(img_path, 0)  # 读取为灰度图
                screen = pyautogui.screenshot()
                screen = np.array(screen)
                screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

                # 模板匹配
                result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                threshold = 0.8  # 匹配的阈值
                if max_val >= threshold:
                    # 找到图片后，添加随机延迟点击时间
                    delay = random.uniform(0.5, 3)
                    self.append_debug_info(f"检测到图片 {img_path}，将在 {delay:.2f} 秒后点击")
                    time.sleep(delay)

                    # 点击的坐标随机偏移范围为±2
                    click_x, click_y = self.click_positions[img_path]
                    offset_x = random.randint(-2, 2)
                    offset_y = random.randint(-2, 2)
                    random_click_x = click_x + offset_x
                    random_click_y = click_y + offset_y
                    self.append_debug_info(f"点击位置 {random_click_x}, {random_click_y} (原始坐标: {click_x}, {click_y}，偏移: {offset_x}, {offset_y})")
                    pyautogui.click(random_click_x, random_click_y)
                else:
                    self.append_debug_info(f"未检测到图片 {img_path}，匹配值: {max_val}")

                time.sleep(1)  # 每次检测间隔1秒

    def display_uploaded_images(self):
        """显示所有已上传的图片"""
        # 清空之前的 Canvas
        for canvas in self.canvas_list:
            canvas.destroy()
        self.canvas_list.clear()

        for img_path in self.image_paths:
            # 打开并加载图像
            pil_image = Image.open(img_path)
            pil_image = pil_image.resize((200, 150), Image.ANTIALIAS)

            # 将 PIL 图像转换为 tkinter 可用的格式
            tk_image = ImageTk.PhotoImage(pil_image)
            self.tk_images[img_path] = tk_image  # 保存引用防止被垃圾回收

            # 在新的 Canvas 上显示图像
            canvas = tk.Canvas(self.canvas_frame, width=200, height=150)
            canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
            canvas.pack(side=tk.LEFT, padx=5)
            self.canvas_list.append(canvas)

    def display_click_coordinates(self):
        """更新界面上显示的点击坐标"""
        coord_text = "点击坐标：\n"
        for img_path, (x, y) in self.click_positions.items():
            coord_text += f"{img_path}: ({x}, {y})\n"
        self.coordinates_label.config(text=coord_text)

    def stop(self):
        self.running = False
        self.append_debug_info("识别已停止。make by ky")

    def create_esc_listener(self):
        """创建一个监听器，监听 Esc 键以停止识别"""
        def on_press(key):
            if key == keyboard.Key.esc:
                self.stop()  # 调用停止函数
                return False  # 停止监听

        # 在单独的线程中启动监听器
        listener_thread = threading.Thread(target=lambda: keyboard.Listener(on_press=on_press).start())
        listener_thread.daemon = True  # 将线程设置为守护线程
        listener_thread.start()

# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageClickApp(root)
    root.mainloop()
