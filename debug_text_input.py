#!/usr/bin/env python3
"""텍스트 입력 디버깅 - 왜 안 되는지 확인"""
import time
import pickle
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip

def debug_text_input():
    """텍스트 입력 단계별 디버깅"""
    
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 쿠키 로드
        cookie_file = Path('.naver_cookies_selenium.pkl')
        if not cookie_file.exists():
            cookie_file = Path('.naver_cookies.pkl')
        
        if cookie_file.exists():
            driver.get('https://naver.com')
            cookie_data = pickle.loads(cookie_file.read_bytes())
            cookies = cookie_data.get('cookies', [])
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    pass
        
        print("📍 Opening editor...")
        driver.get('https://blog.naver.com/ridyservice?Redirect=Write&categoryNo=28')
        time.sleep(3)
        
        print("🔄 Switching to iframe...")
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'mainFrame')))
        
        # 팝업 닫기
        try:
            cancel_btn = driver.find_element(By.CSS_SELECTOR, '.se-popup-button-cancel')
            cancel_btn.click()
            time.sleep(0.5)
        except:
            pass
        
        print("\n" + "="*60)
        print("🐛 DEBUG: Text Input Step-by-Step")
        print("="*60 + "\n")
        
        # Step 1: contenteditable div 찾기
        print("Step 1: Finding contenteditable div...")
        try:
            editable = driver.find_element(By.CSS_SELECTOR, 'div[contenteditable="true"]')
            print(f"  ✅ Found: {editable.tag_name}")
            print(f"     className: {editable.get_attribute('className')}")
            print(f"     text: '{editable.text}'")
        except Exception as e:
            print(f"  ❌ NOT FOUND: {e}")
            print("\n🔍 Alternative search:")
            
            # .se-component.se-text 시도
            try:
                text_comp = driver.find_element(By.CSS_SELECTOR, '.se-component.se-text')
                print(f"  ✅ Found .se-component.se-text")
                
                # 그 안에서 contenteditable 찾기
                editables = text_comp.find_elements(By.CSS_SELECTOR, '[contenteditable]')
                print(f"     Found {len(editables)} contenteditable elements inside")
                for i, el in enumerate(editables):
                    print(f"       [{i+1}] {el.tag_name}.{el.get_attribute('className')[:40]}")
            except:
                print("  ❌ .se-component.se-text also not found")
            
            return
        
        # Step 2: 클릭 (포커스)
        print("\nStep 2: Clicking to focus...")
        editable.click()
        time.sleep(0.5)
        
        # 포커스 확인
        focused = driver.execute_script("return document.activeElement;")
        print(f"  Active element: {focused.tag_name if focused else 'None'}")
        
        # Step 3: 텍스트 입력 (pyperclip)
        print("\nStep 3: Pasting text (pyperclip)...")
        test_text = "테스트 텍스트입니다"
        pyperclip.copy(test_text)
        
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys
        
        actions = ActionChains(driver)
        cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
        
        actions.key_down(cmd_or_ctrl).send_keys('v').key_up(cmd_or_ctrl).perform()
        time.sleep(1)
        
        # 입력 확인
        current_text = editable.text
        print(f"  Current text: '{current_text}'")
        
        if test_text in current_text:
            print("  ✅ Text inserted!")
        else:
            print("  ❌ Text NOT inserted!")
            print("\n🔍 Trying alternative method: textContent...")
            
            driver.execute_script(f"arguments[0].textContent = '{test_text}';", editable)
            time.sleep(0.5)
            
            current_text = editable.text
            print(f"  Current text: '{current_text}'")
            
            if test_text in current_text:
                print("  ✅ textContent worked!")
            else:
                print("  ❌ textContent also failed!")
        
        # Step 4: 볼드 적용 테스트
        print("\nStep 4: Testing bold formatting...")
        
        # 전체 선택
        actions.key_down(cmd_or_ctrl).send_keys('a').key_up(cmd_or_ctrl).perform()
        time.sleep(0.3)
        
        # 볼드 execCommand
        result = driver.execute_script("return document.execCommand('bold');")
        print(f"  execCommand('bold') returned: {result}")
        time.sleep(0.5)
        
        # HTML 확인
        html = driver.execute_script("return arguments[0].innerHTML;", editable)
        print(f"  HTML: {html[:200]}")
        
        if '<b>' in html or '<strong>' in html or 'font-weight' in html:
            print("  ✅ Bold applied!")
        else:
            print("  ❌ Bold NOT applied!")
        
        print("\n" + "="*60)
        print("Press Enter to close browser...")
        input()
        
    finally:
        driver.quit()

if __name__ == '__main__':
    debug_text_input()
