#!/usr/bin/env python3
"""네이버 에디터 툴바 구조 확인"""
import time
import pickle
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

try:
    # 쿠키 로드
    cookie_file = Path(".naver_cookies.pkl")
    if cookie_file.exists():
        data = pickle.loads(cookie_file.read_bytes())
        cookies = data.get('cookies', [])
        
        driver.get("https://naver.com")
        for cookie in cookies:
            try:
                if 'expiry' in cookie:
                    driver.add_cookie(cookie)
            except:
                pass
        
        print(f"✅ Loaded {len(cookies)} cookies")
    
    # 글쓰기 페이지
    driver.get("https://blog.naver.com/ridyservice?Redirect=Write&categoryNo=28")
    time.sleep(3)
    
    # iframe 전환
    wait = WebDriverWait(driver, 10)
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
    print("✅ Switched to iframe")
    
    # 팝업 닫기
    try:
        cancel_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-popup-button-cancel"))
        )
        cancel_btn.click()
        time.sleep(0.5)
    except:
        pass
    
    print("\n" + "="*60)
    print("🔍 Toolbar Button Analysis")
    print("="*60)
    
    # 모든 버튼 찾기
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"\n📊 Total buttons found: {len(buttons)}")
    
    print("\n📝 Button details:")
    for i, btn in enumerate(buttons[:30]):  # 처음 30개만
        try:
            text = btn.text.strip()
            aria_label = btn.get_attribute('aria-label')
            class_name = btn.get_attribute('class')
            title = btn.get_attribute('title')
            
            if text or aria_label or '정렬' in str(class_name) or '굵게' in str(class_name):
                print(f"\n[{i+1}]")
                if text:
                    print(f"  Text: {text}")
                if aria_label:
                    print(f"  Aria: {aria_label}")
                if title:
                    print(f"  Title: {title}")
                print(f"  Class: {class_name[:100]}")
        except:
            pass
    
    # 특정 버튼 검색
    print("\n" + "="*60)
    print("🎯 Searching for specific buttons...")
    print("="*60)
    
    keywords = ['정렬', '가운데', 'center', '굵게', 'bold', '구분', 'divider', 'B']
    
    for keyword in keywords:
        print(f"\n🔍 Searching for: {keyword}")
        
        # aria-label
        try:
            btns = driver.find_elements(By.XPATH, f"//button[contains(@aria-label, '{keyword}')]")
            if btns:
                print(f"  ✅ Found {len(btns)} buttons with aria-label containing '{keyword}'")
                for btn in btns[:3]:
                    print(f"    - {btn.get_attribute('aria-label')}")
        except:
            pass
        
        # title
        try:
            btns = driver.find_elements(By.XPATH, f"//button[contains(@title, '{keyword}')]")
            if btns:
                print(f"  ✅ Found {len(btns)} buttons with title containing '{keyword}'")
                for btn in btns[:3]:
                    print(f"    - {btn.get_attribute('title')}")
        except:
            pass
        
        # text
        try:
            btns = driver.find_elements(By.XPATH, f"//button[contains(text(), '{keyword}')]")
            if btns:
                print(f"  ✅ Found {len(btns)} buttons with text containing '{keyword}'")
                for btn in btns[:3]:
                    print(f"    - {btn.text}")
        except:
            pass
    
    # 스크린샷
    driver.save_screenshot("/tmp/toolbar_inspect.png")
    print(f"\n📸 Screenshot saved: /tmp/toolbar_inspect.png")
    
    input("\nPress Enter to close...")
    
finally:
    driver.quit()
