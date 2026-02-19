"""네이버 에디터 API 분석"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import pickle
from pathlib import Path

# ChromeDriver 경로
CHROMEDRIVER_PATH = str(Path.home() / "bin" / "chromedriver")

def analyze_editor_api():
    """네이버 에디터의 JavaScript API 분석"""
    
    # Chrome 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        print("=" * 60)
        print("네이버 에디터 API 분석")
        print("=" * 60)
        
        # 쿠키 로드
        cookie_file = Path('.naver_cookies.pkl')
        if cookie_file.exists():
            driver.get("https://blog.naver.com")
            time.sleep(1)
            
            data = pickle.loads(cookie_file.read_bytes())
            cookies = data.get('cookies', [])
            
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    pass
            
            print(f"✅ Loaded {len(cookies)} cookies")
        
        # 글쓰기 페이지
        write_url = "https://blog.naver.com/ridyservice?Redirect=Write&categoryNo=28"
        print(f"📍 Opening: {write_url}")
        driver.get(write_url)
        time.sleep(2)
        
        # iframe 전환
        print("⏳ Waiting for mainFrame iframe...")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
        print("✅ mainFrame switched")
        
        # 팝업 닫기
        try:
            cancel_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-popup-button-cancel"))
            )
            cancel_btn.click()
            print("✅ Popup closed")
            time.sleep(0.5)
        except:
            print("No popup")
        
        print("\n" + "=" * 60)
        print("1. 전역 객체 분석")
        print("=" * 60)
        
        # 전역 객체 찾기
        global_objects = driver.execute_script("""
            var keys = Object.keys(window);
            var editorKeys = keys.filter(k => 
                k.toLowerCase().includes('editor') || 
                k.toLowerCase().includes('se') ||
                k.startsWith('__')
            );
            return editorKeys.slice(0, 30);
        """)
        
        print("전역 에디터 관련 객체:")
        for obj in global_objects:
            print(f"  - {obj}")
        
        print("\n" + "=" * 60)
        print("2. SE 객체 탐색")
        print("=" * 60)
        
        # SE 관련 함수들
        se_functions = driver.execute_script("""
            var result = [];
            
            // window.SE 확인
            if (typeof window.SE !== 'undefined') {
                result.push({name: 'window.SE', type: typeof window.SE, keys: Object.keys(window.SE).slice(0, 10)});
            }
            
            // document에서 SE 관련 찾기
            var allScripts = Array.from(document.querySelectorAll('script'));
            var seScripts = allScripts.filter(s => s.textContent.includes('SE.') || s.textContent.includes('editor'));
            result.push({scriptCount: seScripts.length});
            
            return result;
        """)
        
        print("SE 객체 정보:")
        for info in se_functions:
            print(f"  {info}")
        
        print("\n" + "=" * 60)
        print("3. 툴바 버튼 분석")
        print("=" * 60)
        
        # 툴바 버튼들 찾기
        toolbar_info = driver.execute_script("""
            var toolbar = document.querySelector('.se-toolbar');
            if (toolbar) {
                var buttons = Array.from(toolbar.querySelectorAll('button, [role="button"]'));
                return buttons.slice(0, 20).map(btn => ({
                    class: btn.className,
                    title: btn.title || btn.getAttribute('aria-label'),
                    onclick: btn.onclick ? 'has onclick' : 'no onclick'
                }));
            }
            return [];
        """)
        
        print("툴바 버튼들:")
        for btn in toolbar_info:
            print(f"  - {btn.get('title', 'no title')}: {btn.get('class', '')[:50]}")
        
        print("\n" + "=" * 60)
        print("4. 정렬 버튼 이벤트 추적")
        print("=" * 60)
        
        # 가운데 정렬 버튼 찾기
        align_button = driver.execute_script("""
            var buttons = Array.from(document.querySelectorAll('button[title*="중앙"], button[aria-label*="중앙"], button[title*="center"]'));
            if (buttons.length > 0) {
                return {
                    found: true,
                    class: buttons[0].className,
                    title: buttons[0].title || buttons[0].getAttribute('aria-label')
                };
            }
            return {found: false};
        """)
        
        print(f"가운데 정렬 버튼: {align_button}")
        
        print("\n" + "=" * 60)
        print("5. ContentEditable 영역 분석")
        print("=" * 60)
        
        # 편집 가능 영역 확인
        editable_info = driver.execute_script("""
            var editor = document.querySelector('div[contenteditable="true"]');
            if (editor) {
                return {
                    found: true,
                    class: editor.className,
                    id: editor.id,
                    parent: editor.parentElement.className,
                    hasEventListeners: !!editor._listeners || !!editor.__eventListeners
                };
            }
            return {found: false};
        """)
        
        print(f"편집 영역: {editable_info}")
        
        print("\n" + "=" * 60)
        print("6. 이미지 업로드 input 분석")
        print("=" * 60)
        
        # 파일 input 찾기
        file_input_info = driver.execute_script("""
            var inputs = Array.from(document.querySelectorAll('input[type="file"]'));
            return inputs.map(inp => ({
                class: inp.className,
                id: inp.id,
                accept: inp.accept,
                multiple: inp.multiple
            }));
        """)
        
        print("File input들:")
        for inp in file_input_info:
            print(f"  - id={inp.get('id')}, accept={inp.get('accept')}, multiple={inp.get('multiple')}")
        
        print("\n" + "=" * 60)
        print("분석 완료!")
        print("=" * 60)
        
        # 30초 대기 (수동 확인용)
        print("\n30초 대기 중... (브라우저에서 수동으로 기능 테스트 가능)")
        time.sleep(30)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_editor_api()
