# utils/screenshot_utils.py
import ctypes
from ctypes import wintypes
import math
from PIL import Image, ImageChops, ImageTk
import os
import shutil
import tkinter as tkinter  # Sửa import ở đây
from tkinter import messagebox
from config.language import lang
from config.config import MARKER_IMAGE_PATH
from utils.window_utils import center_window

user32 = ctypes.windll.user32

def capture_window(hwnd):
    gdi32 = ctypes.windll.gdi32
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    hwindc = user32.GetWindowDC(hwnd)
    srcdc = gdi32.CreateCompatibleDC(hwindc)
    bmp = gdi32.CreateCompatibleBitmap(hwindc, width, height)
    gdi32.SelectObject(srcdc, bmp)
    result = user32.PrintWindow(hwnd, srcdc, 2)
    if result != 1:
        print("Consolog [WARNING]: PrintWindow không thành công hoặc chỉ chụp được 1 phần.")

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint32),
            ("biWidth", ctypes.c_int32),
            ("biHeight", ctypes.c_int32),
            ("biPlanes", ctypes.c_uint16),
            ("biBitCount", ctypes.c_uint16),
            ("biCompression", ctypes.c_uint32),
            ("biSizeImage", ctypes.c_uint32),
            ("biXPelsPerMeter", ctypes.c_int32),
            ("biYPelsPerMeter", ctypes.c_int32),
            ("biClrUsed", ctypes.c_uint32),
            ("biClrImportant", ctypes.c_uint32),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buffer_len = width * height * 4
    buffer = ctypes.create_string_buffer(buffer_len)
    _ = gdi32.GetDIBits(srcdc, bmp, 0, height, buffer, ctypes.byref(bmi), 0)

    image = Image.frombuffer('RGBA', (width, height), buffer, 'raw', 'BGRA', 0, 1)

    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(srcdc)
    user32.ReleaseDC(hwnd, hwindc)

    return image

def compare_screenshot_with_marker(screenshot, marker_image, threshold=20):
    print("Consolog: So sánh ảnh chụp với marker image...")
    if screenshot.size != marker_image.size:
        marker_image = marker_image.resize(screenshot.size)
    diff = ImageChops.difference(screenshot, marker_image)
    h = diff.histogram()
    sq = (value * ((idx % 256) ** 2) for idx, value in enumerate(h))
    sum_sq = sum(sq)
    rms = math.sqrt(sum_sq / (screenshot.size[0] * screenshot.size[1]))
    print(f"Consolog: Giá trị RMS = {rms}")
    return rms < threshold

def show_marker_selection_popup(screenshot_paths):
    print("Consolog: Hiển thị popup chọn marker image...")
    popup = tkinter.Toplevel(root)  # Sửa tk thành tkinter
    popup.title("Chọn marker image")
    center_window(popup, 800, 600)
    instruction = tkinter.Label(
        popup,
        text="Hãy chỉ ra cho tôi đâu là dấu hiệu nhận biết tài khoản telegram đã chết bằng cách chọn ảnh từ danh sách bên trái",
        font=("Arial Unicode MS", 10, "bold"),
        wraplength=780
    )
    instruction.pack(pady=10)

    selected_path = {"path": None}

    frame = tkinter.Frame(popup)
    frame.pack(fill=tkinter.BOTH, expand=True, padx=10, pady=10)

    listbox = tkinter.Listbox(frame, width=40)
    listbox.pack(side=tkinter.LEFT, fill=tkinter.Y, padx=5, pady=5)

    for path in screenshot_paths:
        listbox.insert(tkinter.END, os.path.basename(path))

    preview_label = tkinter.Label(frame)
    preview_label.pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=True, padx=5, pady=5)

    def on_select(event):
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            file_path = screenshot_paths[index]
            selected_path["path"] = file_path
            try:
                img = Image.open(file_path)
                img.thumbnail((400, 400))
                photo = ImageTk.PhotoImage(img)
                preview_label.config(image=photo)
                preview_label.image = photo
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi mở ảnh {file_path}: {e}")

    listbox.bind("<<ListboxSelect>>", on_select)

    def on_confirm():
        if not selected_path["path"]:
            messagebox.showwarning("Warning", "Vui lòng chọn một ảnh!")
            return
        if os.path.exists(MARKER_IMAGE_PATH):
            try:
                os.remove(MARKER_IMAGE_PATH)
                print("Consolog: Xóa file marker cũ.")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi xóa file marker cũ: {e}")
        try:
            shutil.copy(selected_path["path"], MARKER_IMAGE_PATH)
            print(f"Consolog: Đã lưu marker image tại {MARKER_IMAGE_PATH}")
        except Exception as e:
            print(f"Consolog: Đã lưu marker image tại {MARKER_IMAGE_PATH}")
        popup.destroy()

    confirm_button = tkinter.Button(popup, text="Xác nhận", command=on_confirm)
    confirm_button.pack(pady=10)
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)