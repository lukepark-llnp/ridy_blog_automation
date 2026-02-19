#!/usr/bin/env python3
"""네이버 블로그 스크린샷"""
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle

# 쿠키 로드
cookie_file = Path(".naver_cookies.pkl")
cookies = []
if cookie_file.exists():
    data = pickle.loads(cookie_file.read_bytes())
    cookies = data.get('cookies', [])

# 브라우저 시작
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

try:
    # 네이버 접속
    driver.get("https://naver.com")
    
    # 쿠키 추가
    for cookie in cookies:
        try:
            if 'expiry' in cookie:
                driver.add_cookie(cookie)
            else:
                cookie_copy = dict(cookie)
                cookie_copy.pop('expiry', None)
                driver.add_cookie(cookie_copy)
        except:
            pass
    
    # 블로그 글쓰기 페이지
    driver.get("https://blog.naver.com/ridyservice?Redirect=Write&categoryNo=28")
    time.sleep(3)
    
    # 전체 스크린샷
    screenshot_path = Path("/tmp/naver_blog_screenshot.png")
    driver.save_screenshot(str(screenshot_path))
    print(f"✅ Screenshot saved: {screenshot_path}")
    
    # iframe 안으로 들어가서 본문 스크린샷
    try:
        driver.switch_to.frame("mainFrame")
        time.sleep(1)
        
        # 본문 영역만 스크린샷
        editor = driver.find_element(By.CLASS_NAME, "se-main-container")
        editor_screenshot = Path("/tmp/naver_blog_editor.png")
        editor.screenshot(str(editor_screenshot))
        print(f"✅ Editor screenshot saved: {editor_screenshot}")
    except Exception as e:
        print(f"⚠️ Editor screenshot failed: {e}")
    
finally:
    driver.quit()
