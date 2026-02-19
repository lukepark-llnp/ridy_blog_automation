#!/usr/bin/env python3
"""작성중인 글 확인"""
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
    
    # "확인" 버튼 클릭 (작성중인 글 불러오기)
    try:
        confirm_btn = driver.find_element(By.XPATH, "//button[contains(text(), '확인')]")
        confirm_btn.click()
        print("✅ Clicked '확인' button")
        time.sleep(3)
    except Exception as e:
        print(f"⚠️ No popup or confirm button: {e}")
    
    # iframe 안으로 들어가기
    wait = WebDriverWait(driver, 10)
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
    print("✅ Switched to iframe")
    time.sleep(2)
    
    # 제목 확인
    try:
        title_elem = driver.find_element(By.CSS_SELECTOR, ".se-component.se-documentTitle span.__se-node")
        title = title_elem.text
        print(f"📝 Title: {title}")
    except Exception as e:
        print(f"⚠️ Title not found: {e}")
    
    # 본문 텍스트 확인
    try:
        text_components = driver.find_elements(By.CSS_SELECTOR, ".se-component.se-text")
        print(f"📄 Text components found: {len(text_components)}")
        for i, comp in enumerate(text_components[:5]):  # 처음 5개만
            text = comp.text.strip()
            if text:
                print(f"  [{i+1}] {text[:100]}")
    except Exception as e:
        print(f"⚠️ Text content not found: {e}")
    
    # 이미지 개수 확인
    try:
        images = driver.find_elements(By.CSS_SELECTOR, ".se-component.se-image img")
        print(f"🖼️ Images found: {len(images)}")
    except Exception as e:
        print(f"⚠️ Images not found: {e}")
    
    # 스크린샷 (본문 포함)
    time.sleep(2)
    screenshot_path = Path("/tmp/naver_blog_draft.png")
    driver.save_screenshot(str(screenshot_path))
    print(f"📸 Screenshot saved: {screenshot_path}")
    
    time.sleep(2)
    
finally:
    driver.quit()
