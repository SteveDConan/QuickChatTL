import sys
import time
import os
import random
import threading
import win32gui
import win32con
import pyautogui
import win32ui
from PIL import Image
import win32clipboard
import json
import logging

# Cấu hình logging
logging.basicConfig(filename="auto_it.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# ------------------ THÊM KHAI BÁO CHO PAUSE/RESUME ------------------
global_pause_event = threading.Event()

def toggle_pause():
    """Hàm thay đổi trạng thái tạm dừng – tiếp tục toàn bộ tool."""
    if global_pause_event.is_set():
        global_pause_event.clear()
        print("Consolog: Tiếp tục chạy")
    else:
        global_pause_event.set()
        print("Consolog: Tạm dừng chạy")

def sleep_with_pause(duration):
    """Thay thế time.sleep() để kiểm tra trạng thái pause."""
    start = time.time()
    while time.time() - start < duration:
        if global_pause_event.is_set():
            print("Consolog: [sleep_with_pause] Đang tạm dừng, chờ tiếp...")
            while global_pause_event.is_set():
                time.sleep(0.1)
            print("Consolog: [sleep_with_pause] Tiếp tục sau khi tạm dừng.")
        time.sleep(0.1)

def pause_if_needed(pause_event):
    """Nếu pause_event được set, chờ cho đến khi clear."""
    if pause_event and pause_event.is_set():
        print("Consolog: [pause_if_needed] Đang tạm dừng, chờ tiếp...")
        while pause_event.is_set():
            time.sleep(0.1)
        print("Consolog: [pause_if_needed] Tiếp tục sau khi tạm dừng.")

# ------------------ KẾT THÚC PHẦN PAUSE/RESUME ------------------

USE_PYAUTOGUI = True
DATA_PROCESS_FILE = "data_process.text"
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "cropped_images")
print(f"Consolog: Đã chuyển sang sử dụng đường dẫn tương đối cho ảnh: {IMAGE_DIR}")

def save_table_data(table_data, tdata_dir):
    """Lưu table_data vào file table_data.json trong thư mục tdata_dir."""
    try:
        json_file = os.path.join(tdata_dir, "table_data.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(table_data, f, ensure_ascii=False, indent=4)
        print(f"Consolog: Đã lưu trạng thái bảng vào {json_file}")
        logging.info(f"Đã lưu trạng thái bảng vào {json_file}")
    except Exception as e:
        print(f"Consolog: Lỗi khi lưu trạng thái bảng: {e}")
        logging.error(f"Lỗi khi lưu trạng thái bảng: {e}")

def load_table_data(tdata_dir):
    """Tải table_data từ file table_data.json trong thư mục tdata_dir."""
    table_data = {}
    json_file = os.path.join(tdata_dir, "table_data.json")
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                table_data = json.load(f)
            print(f"Consolog: Đã tải trạng thái bảng từ {json_file}")
            logging.info(f"Đã tải trạng thái bảng từ {json_file}")
        except Exception as e:
            print(f"Consolog: Lỗi khi tải trạng thái bảng: {e}")
            logging.error(f"Lỗi khi tải trạng thái bảng: {e}")
    return table_data

def update_table_data(tdata_dir, folder_name, contact_count_increment=0, message_count_increment=0):
    """Cập nhật contact_count và message_count trong table_data.json."""
    table_data = load_table_data(tdata_dir)
    if folder_name not in table_data:
        table_data[folder_name] = {
            "live_status": "Chưa check",
            "contact_count": 0,
            "message_count": 0,
            "status": "Chưa chạy"
        }
    table_data[folder_name]["contact_count"] = table_data[folder_name].get("contact_count", 0) + contact_count_increment
    table_data[folder_name]["message_count"] = table_data[folder_name].get("message_count", 0) + message_count_increment
    save_table_data(table_data, tdata_dir)
    print(f"Consolog: Đã cập nhật table_data cho {folder_name}: contact_count={table_data[folder_name]['contact_count']}, message_count={table_data[folder_name]['message_count']}")

def get_settings():
    """
    Đọc các file cấu hình và trả về dictionary chứa:
      - avatar_path: đường dẫn thư mục chứa ảnh avatar
      - name_change_path: đường dẫn file danh sách tên cần đổi
      - phone_path: đường dẫn file số điện thoại cần thêm
      - desc_path: đường dẫn file mô tả tài khoản
      - tdata_path: đường dẫn chứa Tdata
      - welcome_message_file: đường dẫn file tin nhắn chào mừng
      - welcome_image_path: đường dẫn file ảnh gửi kèm
      - welcome_message_content: nội dung tin nhắn chào mừng
    Nếu file không tồn tại thì giá trị sẽ là None.
    """
    settings = {}
    config_files = {
        "avatar_path": "avatar_path.txt",
        "name_change_path": "name_change_path.txt",
        "phone_path": "phone_path.txt",
        "desc_path": "desc_path.txt",
        "tdata_path": "tdata_path.txt",
        "welcome_message_file": "welcome_message_file.txt",
        "welcome_image_path": "welcome_image_path.txt"
    }
    
    for key, filename in config_files.items():
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read().strip()
                settings[key] = content if content else None
                print(f"Consolog: Đã đọc {key} từ {filename}: {content}")
        except Exception as e:
            print(f"Consolog: Lỗi đọc file {filename}: {e}")
            settings[key] = None

    welcome_message_file = settings.get("welcome_message_file")
    if welcome_message_file and os.path.isfile(welcome_message_file):
        try:
            with open(welcome_message_file, "r", encoding="utf-8") as f:
                settings["welcome_message_content"] = f.read().strip()
                print(f"Consolog: Nội dung tin nhắn chào mừng: {settings['welcome_message_content']}")
        except Exception as e:
            print(f"Consolog: Lỗi đọc nội dung file tin nhắn {welcome_message_file}: {e}")
            settings["welcome_message_content"] = "Chào mừng bạn đến với Telegram!"
    else:
        print(f"Consolog: Không tìm thấy file tin nhắn chào mừng: {welcome_message_file}")
        settings["welcome_message_content"] = "Chào mừng bạn đến với Telegram!"

    return settings

def send_image_from_path():
    """
    Copy ảnh từ đường dẫn trong welcome_image_path.txt vào clipboard.
    Trả về True nếu thành công, False nếu thất bại.
    """
    settings = get_settings()
    image_path = settings.get("welcome_image_path")
    
    if not image_path or not os.path.isfile(image_path):
        print(f"Consolog: Đường dẫn welcome_image_path không hợp lệ hoặc không tồn tại: {image_path}")
        return False

    print(f"Consolog: Đã chọn ảnh: {image_path}")

    try:
        img = Image.open(image_path).convert("RGB")
        temp_bmp = "temp_clipboard_image.bmp"
        img.save(temp_bmp, "BMP")
        
        # Đọc dữ liệu BMP và bỏ header để tạo DIB
        with open(temp_bmp, "rb") as f:
            bmp_data = f.read()
        dib_data = bmp_data[14:]  # Bỏ BMP header (14 bytes cho BMP)

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib_data)
        win32clipboard.CloseClipboard()
        print(f"Consolog: Đã copy ảnh {image_path} vào clipboard")
        return True
    except Exception as e:
        print(f"Consolog: Lỗi khi xử lý ảnh {image_path}: {e}")
        return False
    finally:
        if os.path.exists(temp_bmp):
            try:
                os.remove(temp_bmp)
                print(f"Consolog: Đã xóa file tạm: {temp_bmp}")
            except Exception as e:
                print(f"Consolog: Lỗi khi xóa file tạm {temp_bmp}: {e}")

def send_text_via_post(hwnd, text):
    """
    Gửi chuỗi text tới cửa sổ hwnd, delay 3s, copy/paste ảnh, rồi nhấn Enter.
    """
    print(f"Consolog: Bắt đầu gửi văn bản: {text}")
    for ch in text:
        win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(ch), 0)
        sleep_with_pause(0.05)
    
    print("Consolog: Đã gõ xong văn bản, delay 3s...")
    sleep_with_pause(3)
    
    if send_image_from_path():
        print("Consolog: Đã copy ảnh, đang paste...")
        pyautogui.hotkey('ctrl', 'v')
        print("Consolog: Đã paste ảnh")
        sleep_with_pause(0.5)
    else:
        print("Consolog: Không thể copy ảnh, tiếp tục gửi văn bản...")
    
    pyautogui.press("enter")
    print("Consolog: Đã nhấn Enter để gửi")
    sleep_with_pause(3)

def click_at_send_message(hwnd, x, y):
    lParam = (y << 16) | (x & 0xFFFF)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    sleep_with_pause(0.05)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)

def click_at_pyautogui(hwnd, x, y):
    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))
    screen_x = client_origin[0] + int(x)
    screen_y = client_origin[1] + int(y)
    print(f"Consolog: Chuyển tọa độ client ({x}, {y}) -> tọa độ screen: ({screen_x}, {screen_y})")
    pyautogui.click(screen_x, screen_y)

def click_at(hwnd, x, y):
    if USE_PYAUTOGUI:
        click_at_pyautogui(hwnd, x, y)
    else:
        click_at_send_message(hwnd, x, y)

def send_key(hwnd, vk):
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
    sleep_with_pause(0.05)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)

def send_ctrl_a(hwnd):
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, ord('A'), 0)
    sleep_with_pause(0.05)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, ord('A'), 0)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)

def click_first_conversation_via_post(hwnd):
    x, y = 50, 150
    click_at(hwnd, x, y)

def convert_screen_to_hwnd(hwnd, x, y):
    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))
    client_x = int(x) - client_origin[0]
    client_y = int(y) - client_origin[1]
    print(f"Consolog: Client origin của hwnd {hwnd} là {client_origin}.")
    print(f"Consolog: (Modified) Tọa độ screen ({x}, {y}) => tọa độ client: ({client_x}, {client_y})")
    return (client_x, client_y)

def get_image_coordinates_in_hwnd(hwnd, image_path, confidence=0.8, debug_filename="debug_generic.png"):
    if not win32gui.IsWindow(hwnd):
        print("Consolog: HWND không hợp lệ.")
        return None
    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))
    client_rect = win32gui.GetClientRect(hwnd)
    width = client_rect[2]
    height = client_rect[3]
    region = (client_origin[0], client_origin[1], width, height)
    print(f"Consolog: Vùng tìm kiếm cho hwnd {hwnd} là: {region}")
    print("Consolog: Delay 2s để đảm bảo ảnh đã hiện đầy đủ.")
    sleep_with_pause(2)
    try:
        debug_screenshot = pyautogui.screenshot(region=region)
        debug_screenshot.save(debug_filename)
        print(f"Consolog: Đã chụp ảnh vùng client và lưu tại: {debug_filename}")
        loc = pyautogui.locateOnScreen(image_path, confidence=confidence, region=region)
    except Exception as e:
        print(f"Consolog: Lỗi locateOnScreen cho hình {image_path}: {e}")
        return None
    if loc:
        screen_x = int(loc.left)
        screen_y = int(loc.top)
        client_point = convert_screen_to_hwnd(hwnd, screen_x, screen_y)
        print(f"Consolog: (Modified) Locate hình {image_path} trả về tọa độ screen ({screen_x}, {screen_y})")
        print(f"Consolog: Sau chuyển đổi, tọa độ client là: {client_point} trong hwnd {hwnd}")
        return client_point
    else:
        print(f"Consolog: Không tìm thấy hình ảnh: {image_path}")
        return None

def image_exists_in_hwnd(hwnd, image_path, confidence=0.8, debug_filename="debug_temp.png", extra_delay=0):
    if extra_delay > 0:
        print(f"Consolog: Delay thêm {extra_delay} giây trước khi kiểm tra sự tồn tại của hình {image_path}.")
        sleep_with_pause(extra_delay)
    loc = get_image_coordinates_in_hwnd(hwnd, image_path, confidence=confidence, debug_filename=debug_filename)
    if loc:
        print(f"Consolog: (Modified) Hình ảnh {image_path} tồn tại trong hwnd {hwnd}.")
        return True
    else:
        print(f"Consolog: (Modified) Hình ảnh {image_path} không tồn tại trong hwnd {hwnd}.")
        return False

def check_image_debug(hwnd, image_path, debug_filename, confidence=0.8, extra_delay=0):
    if extra_delay > 0:
        print(f"Consolog: Delay thêm {extra_delay} giây trước khi chụp debug image '{debug_filename}'.")
        sleep_with_pause(extra_delay)
    loc = get_image_coordinates_in_hwnd(hwnd, image_path, confidence=confidence, debug_filename=debug_filename)
    if loc:
        print(f"Consolog: Debug image '{debug_filename}' - Tìm thấy đối tượng tại {loc}.")
    else:
        print(f"Consolog: Debug image '{debug_filename}' - Không tìm thấy đối tượng.")
    return loc

def click_image_in_hwnd(hwnd, image_path, confidence=0.8):
    client_point = get_image_coordinates_in_hwnd(hwnd, image_path, confidence)
    if client_point is not None:
        click_at(hwnd, client_point[0], client_point[1])
        print(f"Consolog: Click thành công hình {image_path} tại tọa độ client: {client_point} trong hwnd {hwnd}")
        return True
    else:
        print(f"Consolog: Không click được hình {image_path} vì không lấy được tọa độ trên hwnd {hwnd}.")
        return False

def dump_hwnd_image(hwnd, filename):
    try:
        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bot - top
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        result = win32gui.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
        if result == 1:
            saveBitMap.SaveBitmapFile(saveDC, filename)
            print(f"Consolog: Dump hình hwnd thành công, lưu tại {filename}")
        else:
            print("Consolog: Lỗi khi dump hình hwnd.")
        win32gui.ReleaseDC(hwnd, hwndDC)
        win32gui.DeleteObject(saveBitMap.GetHandle())
    except Exception as e:
        print("Consolog: Lỗi khi sử dụng PrintWindow:", e)

def capture_debug_screenshot(hwnd, debug_filename):
    if not win32gui.IsWindow(hwnd):
        print("Consolog: HWND không hợp lệ trong debug capture.")
        return
    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))
    client_rect = win32gui.GetClientRect(hwnd)
    width = client_rect[2]
    height = client_rect[3]
    region = (client_origin[0], client_origin[1], width, height)
    try:
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(debug_filename)
        print(f"Consolog: Debug capture đã lưu ảnh tại {debug_filename}.")
    except Exception as e:
        print(f"Consolog: Lỗi khi chụp debug screenshot: {e}")

def automate_contact_process(phone_number, hwnd, tdata_dir, folder_name):
    print("Consolog: Delay 3s trước Bước 1")
    sleep_with_pause(3)

    static_ui_image = os.path.join(IMAGE_DIR, "cropped_20250411_121250.png")
    print("Consolog: Bước 1‑3: Capture static UI debug image.")
    check_image_debug(hwnd, static_ui_image, debug_filename="debug_step1_static_ui.png", confidence=0.8)

    menu_image = os.path.join(IMAGE_DIR, "cropped_20250411_121250.png")
    if click_image_in_hwnd(hwnd, menu_image, confidence=0.8):
        print("Consolog: Bước 1: Click menu thành công.")
    else:
        print("Consolog: Bước 1: Không tìm thấy hình menu.")
    sleep_with_pause(2)

    add_contact_image = os.path.join(IMAGE_DIR, "cropped_20250404_063240.png")
    if click_image_in_hwnd(hwnd, add_contact_image, confidence=0.8):
        print("Consolog: Bước 2: Click add contact thành công.")
    else:
        print("Consolog: Bước 2: Không tìm thấy hình add contact.")
    sleep_with_pause(2)

    them_contact_image = os.path.join(IMAGE_DIR, "cropped_20250404_063308.png")
    if click_image_in_hwnd(hwnd, them_contact_image, confidence=0.8):
        print("Consolog: Bước 3: Click thêm contact thành công.")
    else:
        print("Consolog: Bước 3: Không tìm thấy hình thêm contact.")
    sleep_with_pause(2)

    print("Consolog: Bước 1‑3: Capture debug screenshot sau khi hoàn tất bước 1‑3.")
    capture_debug_screenshot(hwnd, "debug_step3_after.png")

    phone_path = get_settings().get("phone_path")
    random_phone = "0123456789"
    if phone_path and os.path.exists(phone_path):
        try:
            with open(phone_path, "r", encoding="utf-8") as f:
                phone_list = [line.strip() for line in f if line.strip()]
            if phone_list:
                random_phone = random.choice(phone_list)
                phone_list.remove(random_phone)
                with open(phone_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(phone_list))
                print("Consolog: Đã xóa SDT khỏi file cấu hình và không để lại khoảng trắng.")
                with open(DATA_PROCESS_FILE, "a", encoding="utf-8") as f_dp:
                    f_dp.write(f"{random_phone}_{hwnd}\n")
                print(f"Consolog: Ghi số điện thoại {random_phone} và hwnd {hwnd} vào file {DATA_PROCESS_FILE}.")
            else:
                print("Consolog: File số điện thoại rỗng, dùng mặc định.")
        except Exception as e:
            print("Consolog: Lỗi khi đọc hoặc ghi file số điện thoại:", e)
    else:
        print("Consolog: Không tìm thấy file cấu hình số điện thoại, dùng mặc định.")

    date_str = time.strftime("%d%m%Y")
    name = f"{random_phone}_{date_str}"
    send_text_via_post(hwnd, name)
    print(f"Consolog: Bước 4: Nhập tên {name}.")
    sleep_with_pause(2)

    print("Consolog: Bước 4: Capture debug screenshot sau khi nhập tên contact.")
    capture_debug_screenshot(hwnd, "debug_step4_after.png")

    print("Consolog: Bước 5: Chuyển focus sang trường số điện thoại bằng cách nhấn Tab 1 lần sử dụng pyautogui.press()")
    pyautogui.press("tab")
    sleep_with_pause(0.2)
    print("Consolog: Bước 5: Nhấn Tab 1 lần thành công.")
    sleep_with_pause(2)

    print("Consolog: Bước 6: Ctrl+A và Delete bằng pyautogui do đã focus đúng.")
    pyautogui.hotkey('ctrl', 'a')
    sleep_with_pause(0.2)
    pyautogui.press('delete')
    sleep_with_pause(0.5)

    sdt_to_fill = None
    phone_process_file = DATA_PROCESS_FILE
    if os.path.exists(phone_process_file):
        try:
            with open(phone_process_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            for line in lines:
                if "_" in line:
                    parts = line.split("_")
                    if parts[-1] == str(hwnd):
                        sdt_to_fill = parts[0]
                        print(f"Consolog: Tìm thấy số điện thoại {sdt_to_fill} cho hwnd {hwnd} trong {phone_process_file}.")
                        break
            if sdt_to_fill is None:
                print(f"Consolog: Không tìm thấy số điện thoại tương ứng cho hwnd {hwnd} trong {phone_process_file}. Sử dụng mặc định.")
                sdt_to_fill = "0123456789"
        except Exception as e:
            print(f"Consolog: Lỗi khi đọc file {phone_process_file}: {e}")
            sdt_to_fill = "0123456789"
    else:
        print(f"Consolog: File {phone_process_file} không tồn tại. Sử dụng số mặc định.")
        sdt_to_fill = "0123456789"

    pyautogui.write(sdt_to_fill)
    print(f"Consolog: Bước 6: Xóa nội dung cũ và nhập số điện thoại: {sdt_to_fill} bằng pyautogui.")
    sleep_with_pause(2)

    print("Consolog: Bước 6: Capture debug screenshot sau khi nhập số điện thoại.")
    capture_debug_screenshot(hwnd, "debug_step6_after.png")

    image_path_step6_extra = os.path.join(IMAGE_DIR, "cropped_20250410_232349.png")
    print("Consolog: Bước 6.1: Tìm ảnh cropped_20250410_232349.png sau khi nhập số điện thoại và tiến hành click.")
    if click_image_in_hwnd(hwnd, image_path_step6_extra, confidence=0.8):
        print("Consolog: Bước 6.1: Click ảnh cropped_20250410_232349.png thành công.")
    else:
        print("Consolog: Bước 6.1: Không tìm thấy ảnh cropped_20250410_232349.png.")
    sleep_with_pause(2)

    image_path_step5 = os.path.join(IMAGE_DIR, "cropped_20250412_223952.png")
    print("Consolog: Bước 8: Kiểm tra ảnh điều kiện với delay và debug image 'debug_step8_after.png'.")
    exists = image_exists_in_hwnd(hwnd, image_path_step5, confidence=0.8, debug_filename="debug_step8_after.png", extra_delay=1.5)
    if not exists:
        print("Consolog: Bước 8: Không tìm thấy ảnh, thêm số điện thoại thành công.")
        update_table_data(tdata_dir, folder_name, contact_count_increment=1)  # Tăng contact_count +1
        sleep_with_pause(2)
    else:
        print("Consolog: Bước 8: Tìm thấy ảnh, thêm số điện thoại thất bại, tiến hành xóa sdt_hwnd khỏi file data_process.text và khôi phục sdt gốc vào file phone_path.txt.")
        phone_process_file = DATA_PROCESS_FILE
        updated_lines = []
        removed_phone = None
        if os.path.exists(phone_process_file):
            try:
                with open(phone_process_file, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                for line in lines:
                    if "_" in line:
                        parts = line.split("_")
                        if parts[-1] == str(hwnd):
                            removed_phone = parts[0]
                            print(f"Consolog: Xóa sdt {removed_phone} cho hwnd {hwnd} khỏi {phone_process_file}.")
                            continue
                    updated_lines.append(line)
                with open(phone_process_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(updated_lines))
            except Exception as e:
                print(f"Consolog: Lỗi khi xử lý file {phone_process_file}: {e}")
        else:
            print(f"Consolog: File {phone_process_file} không tồn tại. Không có gì để xóa.")
        if removed_phone:
            phone_path_file = get_settings().get("phone_path")
            if phone_path_file:
                try:
                    with open(phone_path_file, "a", encoding="utf-8") as f:
                        f.write(f"\n{removed_phone}")
                    print(f"Consolog: Đã khôi phục sdt {removed_phone} vào file {phone_path_file}.")
                except Exception as e:
                    print(f"Consolog: Lỗi khi khôi phục sdt vào file {phone_path_file}: {e}")
            else:
                print("Consolog: File cấu hình phone_path không được xác định.")
        else:
            print("Consolog: Không tìm thấy sdt nào tương ứng với hwnd trong file data_process.text.")
        return

    warning_image = os.path.join(IMAGE_DIR, "duplicate_phone_warning.png")
    print("Consolog: Bước 7: Kiểm tra cảnh báo trùng SDT với debug image 'debug_step7_after.png'.")
    loc_warning = check_image_debug(hwnd, warning_image, debug_filename="debug_step7_after.png", confidence=0.8, extra_delay=1.0)
    if loc_warning:
        print("Consolog: Bước 7: Phát hiện cảnh báo trùng SDT.")
    else:
        print("Consolog: Bước 7: Không phát hiện cảnh báo trùng SDT.")

    settings = get_settings()
    welcome_message = settings.get("welcome_message_content", "Chào mừng bạn đến với Telegram!")
    send_text_via_post(hwnd, welcome_message)
    print(f"Consolog: Bước 9: Nhập tin nhắn: {welcome_message}")
    sleep_with_pause(1)
    print("Consolog: Bước 9: Gửi tin nhắn và ảnh xong.")
    sleep_with_pause(1)

    print("Consolog: Bước 9: Đợi 2s sau khi ấn Enter để bắt đầu kiểm tra hình ảnh xác nhận.")
    sleep_with_pause(2)

    image_path_step7 = os.path.join(IMAGE_DIR, "cropped_20250411_042803.png")
    print("Consolog: Bước 9: Kiểm tra ảnh xác nhận, debug image 'debug_step9_after.png'.")
    loc7 = check_image_debug(hwnd, image_path_step7, debug_filename="debug_step9_after.png", confidence=0.8)
    if loc7 is None:  # Không tìm thấy ảnh xác nhận lỗi => gửi tin nhắn thành công
        print("Consolog: Bước 9: Không tìm thấy ảnh xác nhận, gửi tin nhắn thành công.")
        update_table_data(tdata_dir, folder_name, message_count_increment=1)  # Tăng message_count +1
    else:
        print("Consolog: Bước 9: Tìm thấy ảnh xác nhận, gửi tin nhắn thất bại, thực hiện khôi phục SĐT.")
        phone_process_file = DATA_PROCESS_FILE
        updated_lines = []
        removed_phone = None
        if os.path.exists(phone_process_file):
            try:
                with open(phone_process_file, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                for line in lines:
                    if "_" in line:
                        parts = line.split("_")
                        if parts[-1] == str(hwnd):
                            removed_phone = parts[0]
                            print(f"Consolog: Xóa sdt {removed_phone} cho hwnd {hwnd} khỏi {phone_process_file}.")
                            continue
                    updated_lines.append(line)
                with open(phone_process_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(updated_lines))
            except Exception as e:
                print(f"Consolog: Lỗi khi xử lý file {phone_process_file}: {e}")
        if removed_phone:
            phone_path_file = get_settings().get("phone_path")
            if phone_path_file:
                try:
                    with open(phone_path_file, "a", encoding="utf-8") as f:
                        f.write(f"\n{removed_phone}")
                    print(f"Consolog: Đã khôi phục sdt {removed_phone} vào file {phone_path_file}.")
                except Exception as e:
                    print(f"Consolog: Lỗi khi khôi phục sdt vào file {phone_path_file}: {e}")
            else:
                print("Consolog: File cấu hình phone_path không được xác định.")
        else:
            print("Consolog: Không tìm thấy sdt nào tương ứng với hwnd trong file data_process.text.")
        if 'auto_thread' in globals():
            if hasattr(auto_thread, 'is_alive') and auto_thread.is_alive():
                print("Consolog: Đang chờ auto_thread kết thúc...")
                auto_thread.join()
                print("Consolog: auto_thread đã kết thúc.")
        else:
            print("Consolog: Không tìm thấy auto_thread để chờ kết thúc.")

def click_first_conversation_via_post(hwnd):
    x, y = 50, 150
    click_at(hwnd, x, y)

def main():
    if len(sys.argv) < 5:
        print("Usage: script_welcome.py <tdata_folder> <hwnd> <tdata_dir> <folder_name>")
        sys.exit(1)
    tdata_folder = sys.argv[1]
    try:
        global hwnd
        hwnd = int(sys.argv[2])
    except ValueError:
        print("Consolog: HWND không hợp lệ")
        sys.exit(1)
    tdata_dir = sys.argv[3]
    folder_name = sys.argv[4]
    settings = get_settings()
    print(f"Consolog: Sử dụng tin nhắn chào: {settings.get('welcome_message_content')}")
    print("Consolog: Trước khi gọi SetForegroundWindow, hwnd =", hwnd)
    try:
        win32gui.SetForegroundWindow(hwnd)
        print("Consolog: Sau khi gọi SetForegroundWindow, hwnd =", hwnd)
    except Exception as e:
        print("Consolog: Lỗi khi gọi SetForegroundWindow:", e)
    try:
        is_visible = win32gui.IsWindowVisible(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        print(f"Consolog: Cửa sổ hwnd = {hwnd}, IsWindowVisible = {is_visible}, Rect = {rect}")
    except Exception as e:
        print("Consolog: Lỗi khi lấy thông tin cửa sổ:", e)
    dump_hwnd_image(hwnd, "debug_hwnd_dump.bmp")
    automate_contact_process(phone_number=settings.get("phone_path") or "0123456789", hwnd=hwnd, tdata_dir=tdata_dir, folder_name=folder_name)
    click_first_conversation_via_post(hwnd)
    sleep_with_pause(2)
    
if __name__ == "__main__":
    main()
