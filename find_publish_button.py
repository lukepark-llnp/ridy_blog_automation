"""Find the publish button in current Naver blog editor"""
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
import pickle

def find_publish_button():
    """Connect to existing Chrome and find publish button"""
    
    # Load cookies
    cookie_file = Path('.naver_cookies.pkl')
    if not cookie_file.exists():
        cookie_file = Path('.naver_cookies_selenium.pkl')
    
    if not cookie_file.exists():
        print("❌ No cookies found")
        return
    
    data = pickle.loads(cookie_file.read_bytes())
    cookies = data.get('cookies', [])
    
    # Launch Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Go to naver.com first for cookies
        driver.get("https://naver.com")
        
        # Add cookies
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        
        # Go to write page
        driver.get("https://blog.naver.com/ridyservice?Redirect=Write&categoryNo=28")
        time.sleep(3)
        
        print("="*60)
        print("🔍 Searching for ALL buttons...")
        print("="*60)
        
        # Find all buttons
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        
        print(f"\n📊 Found {len(all_buttons)} buttons in total\n")
        
        # Search for publish-related buttons
        publish_candidates = []
        
        for i, btn in enumerate(all_buttons):
            try:
                # Get button info
                text = btn.text.strip()
                class_name = btn.get_attribute("class") or ""
                id_attr = btn.get_attribute("id") or ""
                
                # Check if it's a publish button
                is_publish = (
                    "발행" in text or
                    "publish" in class_name.lower() or
                    "publish" in id_attr.lower()
                )
                
                if is_publish:
                    print(f"✅ [{i}] PUBLISH CANDIDATE:")
                    print(f"    Text: {text}")
                    print(f"    Class: {class_name}")
                    print(f"    ID: {id_attr}")
                    print(f"    Visible: {btn.is_displayed()}")
                    print(f"    Enabled: {btn.is_enabled()}")
                    print()
                    
                    publish_candidates.append({
                        'index': i,
                        'text': text,
                        'class': class_name,
                        'id': id_attr,
                        'visible': btn.is_displayed(),
                        'enabled': btn.is_enabled()
                    })
                
                elif text or class_name or id_attr:
                    # Show other buttons briefly
                    if i < 20:  # First 20 buttons
                        print(f"[{i}] Text: {text[:30]} | Class: {class_name[:40]}")
            
            except Exception as e:
                pass
        
        print("\n" + "="*60)
        print(f"🎯 Found {len(publish_candidates)} publish candidates")
        print("="*60)
        
        if publish_candidates:
            print("\n📋 Best candidate:")
            best = publish_candidates[0]
            print(f"  Index: {best['index']}")
            print(f"  Text: {best['text']}")
            print(f"  Class: {best['class']}")
            print(f"  ID: {best['id']}")
            
            # Try to click it
            if best['visible'] and best['enabled']:
                print("\n🖱️ Attempting to click...")
                try:
                    all_buttons[best['index']].click()
                    print("✅ Clicked successfully!")
                    time.sleep(2)
                    print(f"Current URL: {driver.current_url}")
                except Exception as e:
                    print(f"❌ Click failed: {e}")
        else:
            print("\n❌ No publish button found!")
        
        print("\nBrowser will stay open. Press Enter to close...")
        input()
        
    finally:
        driver.quit()


if __name__ == "__main__":
    find_publish_button()
