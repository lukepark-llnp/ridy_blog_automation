"""Debug: Find input[type='file'] location in Naver editor"""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import pickle

def main():
    cookies_file = Path('.naver_cookies.pkl')
    if not cookies_file.exists():
        print("❌ No cookies found. Run login first.")
        return
    
    # Load cookies
    data = pickle.loads(cookies_file.read_bytes())
    cookies = data.get('cookies', [])
    
    pw_cookies = []
    for c in cookies:
        pw_c = {
            'name': c['name'],
            'value': c['value'],
            'domain': c.get('domain', '.naver.com'),
            'path': c.get('path', '/'),
        }
        if 'expires' in c:
            pw_c['expires'] = c['expires']
        pw_cookies.append(pw_c)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies(pw_cookies)
        
        page = context.new_page()
        
        # Go to write page
        url = "https://blog.naver.com/ridyservice?Redirect=Write&categoryNo=28"
        print(f"📍 Opening: {url}")
        page.goto(url, wait_until="networkidle")
        
        # Wait for iframe
        print("⏳ Waiting for mainFrame...")
        page.wait_for_selector("#mainFrame", timeout=10000)
        main_frame = page.frame(name="mainFrame")
        
        if not main_frame:
            print("❌ mainFrame not found")
            return
        
        print("✅ mainFrame loaded")
        
        # Close popups
        main_frame.evaluate("""
            () => {
                const killList = [
                    '.se-popup-dim',
                    '.se-popup-container',
                    '.se-help-panel',
                    '[class*="popup"]'
                ];
                killList.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
            }
        """)
        
        time.sleep(1)
        
        # Activate editor - click content area
        print("\n📝 Activating editor...")
        content = main_frame.locator(".se-component.se-text").first
        content.click(force=True)
        time.sleep(1)
        
        # Find all input[type='file'] in different contexts
        print("\n" + "="*60)
        print("🔍 Searching for input[type='file']...")
        print("="*60)
        
        # 1. In iframe
        print("\n1️⃣ Inside mainFrame (iframe):")
        iframe_inputs = main_frame.locator("input[type='file']")
        count = iframe_inputs.count()
        print(f"   Found: {count} inputs")
        
        if count > 0:
            for i in range(count):
                inp = iframe_inputs.nth(i)
                props = inp.evaluate("""el => ({
                    id: el.id,
                    name: el.name,
                    className: el.className,
                    accept: el.accept,
                    multiple: el.multiple,
                    style: el.getAttribute('style'),
                    visible: el.offsetParent !== null,
                    display: window.getComputedStyle(el).display,
                    visibility: window.getComputedStyle(el).visibility
                })""")
                print(f"   [{i}] {props}")
        
        # 2. In main page (outside iframe)
        print("\n2️⃣ Outside iframe (main page):")
        page_inputs = page.locator("input[type='file']")
        count = page_inputs.count()
        print(f"   Found: {count} inputs")
        
        if count > 0:
            for i in range(count):
                inp = page_inputs.nth(i)
                props = inp.evaluate("""el => ({
                    id: el.id,
                    name: el.name,
                    className: el.className,
                    accept: el.accept,
                    multiple: el.multiple,
                    style: el.getAttribute('style'),
                    visible: el.offsetParent !== null
                })""")
                print(f"   [{i}] {props}")
        
        # 3. Click image button and search again
        print("\n3️⃣ After clicking image button:")
        try:
            # Try to find and click image button
            for selector in [
                ".se-image-toolbar-button",
                "button[data-name='image']",
                ".se-insert-menu-button-image",
            ]:
                try:
                    btn = main_frame.locator(selector).first
                    if btn.count() > 0:
                        btn.evaluate("el => el.click()")
                        print(f"   ✅ Clicked: {selector}")
                        time.sleep(1)
                        break
                except:
                    continue
            
            # Search again
            print("\n   In iframe after click:")
            count = iframe_inputs.count()
            print(f"   Found: {count} inputs")
            
            if count > 0:
                for i in range(count):
                    inp = iframe_inputs.nth(i)
                    props = inp.evaluate("""el => ({
                        id: el.id,
                        visible: el.offsetParent !== null,
                        display: window.getComputedStyle(el).display
                    })""")
                    print(f"   [{i}] {props}")
            
            print("\n   In main page after click:")
            count = page_inputs.count()
            print(f"   Found: {count} inputs")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n" + "="*60)
        print("✅ Debug complete. Browser will stay open.")
        print("   Press Enter to close...")
        print("="*60)
        
        input()
        
        browser.close()


if __name__ == "__main__":
    main()
