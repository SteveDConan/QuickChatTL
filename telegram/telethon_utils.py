# telegram/telethon_utils.py
import asyncio
from telethon.sync import TelegramClient
from telethon import functions, types, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
from config.config import API_ID, API_HASH
from telegram.tdata_utils import parse_2fa_info  # Sửa import ở đây
from utils.file_utils import cleanup_session_files
from tkinter import messagebox, simpledialog
import threading
import os

successful_sessions = set()

async def check_authorization(session_path, phone):
    print(f"Consolog: Kiểm tra authorization cho {phone} từ session: {session_path}")
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
        authorized = await client.is_user_authorized()
        await client.disconnect()
        print(f"Consolog: Authorization cho {phone}: {authorized}")
        return authorized
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi kiểm tra authorization cho {phone}: {e}")
        return False

def get_otp(phone):
    print(f"Consolog: Yêu cầu nhập OTP cho {phone}")
    otp_result = [None]
    event = threading.Event()
    def ask():
        otp_result[0] = simpledialog.askstring("OTP", lang["otp_prompt"].format(phone=phone), parent=root)
        print(f"Consolog: OTP đã được nhập: {otp_result[0]}")
        event.set()
    root.after(0, ask)
    event.wait()
    return otp_result[0]

async def async_login(session_path, phone, tdata_folder):
    print(f"Consolog: Bắt đầu đăng nhập cho {phone} với session: {session_path}")
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
    except Exception as e:
        log_message(f"Consolog [ERROR]: Lỗi kết nối cho {phone}: {e}")
        cleanup_session_files(session_path)
        return False
    if not await client.is_user_authorized():
        try:
            await client.send_code_request(phone)
            log_message(f"Consolog: Đã gửi OTP cho {phone}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Gửi mã OTP thất bại cho {phone}: {e}")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        otp = get_otp(phone)
        if not otp:
            messagebox.showerror("Lỗi", "Không nhập OTP.")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        auto_close_telegram()
        log_message("Consolog: Đợi 0.5 giây sau khi đóng Telegram Portable...")
        await asyncio.sleep(1)
        log_message("Consolog: Bắt đầu tiến trình đăng nhập với OTP.")
        try:
            await client.sign_in(phone, otp)
            if not await client.is_user_authorized():
                raise Exception("Đăng nhập OTP không thành công, cần 2FA")
            log_message(f"Consolog: Đăng nhập thành công cho {phone} (không 2FA)")
        except SessionPasswordNeededError:
            twofa_info = parse_2fa_info(tdata_folder)
            if "password" not in twofa_info:
                messagebox.showerror("Lỗi", lang["2fa_error"].format(phone=phone))
                await client.disconnect()
                cleanup_session_files(session_path)
                return False
            password_2fa = twofa_info["password"]
            try:
                await client.sign_in(password=password_2fa)
                if not await client.is_user_authorized():
                    raise Exception("Đăng nhập không thành công sau khi nhập mật khẩu 2FA.")
                log_message(f"Consolog: Đăng nhập thành công cho {phone} (2FA)")
            except Exception as e2:
                log_message(f"Consolog [ERROR]: Lỗi đăng nhập 2FA cho {phone}: {e2}")
                messagebox.showerror("Lỗi", f"Đăng nhập 2FA thất bại cho {phone}: {e2}")
                await client.disconnect()
                cleanup_session_files(session_path)
                return False
        except PhoneCodeInvalidError:
            messagebox.showerror("Lỗi", f"Mã OTP không đúng cho {phone}!")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        except PhoneCodeExpiredError:
            messagebox.showerror("Lỗi", f"Mã OTP đã hết hạn cho {phone}!")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đăng nhập thất bại cho {phone}: {e}")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
    log_message(f"Consolog: Session cho {phone} đã được lưu tại {session_path}")
    await client.disconnect()
    return True

def login_account(tdata_folder, update_item_callback):
    session_file = os.path.join(tdata_folder, "session.session")
    session_folder = os.path.join(tdata_folder, "session")
    phone = os.path.basename(tdata_folder)
    print(f"Consolog: Đang đăng nhập tài khoản: {phone}")
    _ = open_telegram_with_tdata(tdata_folder)
    if os.path.exists(session_file) or os.path.exists(session_folder):
        authorized = asyncio.run(check_authorization(session_folder, phone))
        if authorized:
            update_item_callback(phone, lang["skipped"])
            successful_sessions.add(phone)
            print(f"Consolog: {phone} session đã có, bỏ qua đăng nhập.")
            return True
        else:
            cleanup_session_files(session_folder)
    result = asyncio.run(async_login(os.path.join(tdata_folder, "session"), phone, tdata_folder))
    if result:
        update_item_callback(phone, lang["success"])
        successful_sessions.add(phone)
    else:
        update_item_callback(phone, lang["failure"])
    return result

async def update_privacy(session_path):
    print(f"Consolog: Đang cập nhật quyền riêng tư cho session: {session_path}")
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
    except Exception as e:
        log_message(f"Consolog [ERROR]: Lỗi kết nối cho {session_path}: {e}")
        return
    try:
        await client(functions.account.SetPrivacyRequest(
            key=types.InputPrivacyKeyPhoneNumber(),
            rules=[types.InputPrivacyValueDisallowAll()]
        ))
        if hasattr(types, "InputPrivacyKeyCalls"):
            await client(functions.account.SetPrivacyRequest(
                key=types.InputPrivacyKeyCalls(),
                rules=[types.InputPrivacyValueDisallowAll()]
            ))
        else:
            log_message("Consolog: InputPrivacyKeyCalls không khả dụng, bỏ qua.")
        log_message(f"Consolog: Cập nhật quyền riêng tư thành công cho session {session_path}")
    except Exception as e:
        log_message(f"Consolog [ERROR]: Lỗi cập nhật quyền riêng tư cho session {session_path}: {e}")
    await client.disconnect()