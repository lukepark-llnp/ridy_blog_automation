#!/usr/bin/env python3
"""텍스트 에디터 영역 완벽 분석"""
import time
import pickle
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def analyze_text_area():
    """텍스트 에디터 영역 완벽 분석"""
    
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 쿠키 로드 & 에디터 접속
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
        print("🎯 TEXT EDITOR AREA - Complete Structure")
        print("="*60 + "\n")
        
        analysis = {}
        
        # 1. .se-component.se-text 완벽 분석
        print("1️⃣ Analyzing .se-component.se-text structure...")
        text_component_script = """
        var textComp = document.querySelector('.se-component.se-text');
        if (!textComp) return {error: 'Not found'};
        
        function getFullStructure(el, depth = 0) {
            if (depth > 10) return '...too deep';
            
            var structure = {
                tagName: el.tagName,
                className: el.className,
                id: el.id,
                contenteditable: el.getAttribute('contenteditable'),
                textContent: el.textContent.substring(0, 50),
                children: []
            };
            
            for (var i = 0; i < el.children.length; i++) {
                structure.children.push(getFullStructure(el.children[i], depth + 1));
            }
            
            return structure;
        }
        
        return getFullStructure(textComp);
        """
        analysis['text_component_structure'] = driver.execute_script(text_component_script)
        print(f"   ✅ Structure captured:")
        print(json.dumps(analysis['text_component_structure'], indent=2, ensure_ascii=False))
        
        # 2. contenteditable DIV의 정확한 위치
        print("\n2️⃣ Finding exact contenteditable DIV...")
        contenteditable_path_script = """
        var editableDiv = document.querySelector('div[contenteditable="true"]');
        if (!editableDiv) return {error: 'Not found'};
        
        // 부모 경로 추적
        var path = [];
        var current = editableDiv;
        while (current && current !== document.body) {
            path.unshift({
                tagName: current.tagName,
                className: current.className,
                id: current.id
            });
            current = current.parentElement;
        }
        
        return {
            editableDiv: {
                tagName: editableDiv.tagName,
                className: editableDiv.className,
                id: editableDiv.id,
                contenteditable: editableDiv.getAttribute('contenteditable')
            },
            path: path,
            pathString: path.map(p => 
                p.tagName + (p.className ? '.' + p.className.split(' ')[0] : '')
            ).join(' > ')
        };
        """
        analysis['contenteditable_path'] = driver.execute_script(contenteditable_path_script)
        print(f"   ✅ Path: {analysis['contenteditable_path'].get('pathString', 'N/A')}")
        
        # 3. 텍스트 입력 테스트
        print("\n3️⃣ Testing text input methods...")
        input_test_script = """
        var editableDiv = document.querySelector('div[contenteditable="true"]');
        if (!editableDiv) return {error: 'Not found'};
        
        // Method 1: innerHTML
        var originalHTML = editableDiv.innerHTML;
        editableDiv.innerHTML = '<p>Test 1</p>';
        var method1Success = editableDiv.innerHTML.includes('Test 1');
        
        // Method 2: textContent
        editableDiv.textContent = 'Test 2';
        var method2Success = editableDiv.textContent.includes('Test 2');
        
        // Method 3: execCommand (if supported)
        editableDiv.focus();
        var method3Success = false;
        try {
            document.execCommand('insertText', false, 'Test 3');
            method3Success = editableDiv.textContent.includes('Test 3');
        } catch(e) {
            method3Success = false;
        }
        
        // 복원
        editableDiv.innerHTML = originalHTML;
        
        return {
            method1_innerHTML: method1Success,
            method2_textContent: method2Success,
            method3_execCommand: method3Success
        };
        """
        analysis['input_test'] = driver.execute_script(input_test_script)
        print(f"   Results:")
        print(f"      innerHTML: {analysis['input_test'].get('method1_innerHTML')}")
        print(f"      textContent: {analysis['input_test'].get('method2_textContent')}")
        print(f"      execCommand: {analysis['input_test'].get('method3_execCommand')}")
        
        # 4. 포맷팅 버튼 찾기 (볼드, 정렬 등)
        print("\n4️⃣ Finding formatting buttons...")
        formatting_buttons_script = """
        var buttons = {
            bold: document.querySelector('.se-bold-toolbar-button, button[aria-label*="굵게"]'),
            italic: document.querySelector('.se-italic-toolbar-button, button[aria-label*="기울임"]'),
            underline: document.querySelector('.se-underline-toolbar-button, button[aria-label*="밑줄"]'),
            alignCenter: document.querySelector('button[aria-label*="가운데"]'),
            alignLeft: document.querySelector('button[aria-label*="왼쪽"]'),
            alignRight: document.querySelector('button[aria-label*="오른쪽"]'),
            color: document.querySelector('.se-text-color-toolbar-button'),
            bgColor: document.querySelector('.se-background-color-toolbar-button')
        };
        
        var result = {};
        for (var key in buttons) {
            if (buttons[key]) {
                result[key] = {
                    found: true,
                    className: buttons[key].className,
                    ariaLabel: buttons[key].getAttribute('aria-label'),
                    text: buttons[key].textContent.substring(0, 20)
                };
            } else {
                result[key] = {found: false};
            }
        }
        
        return result;
        """
        analysis['formatting_buttons'] = driver.execute_script(formatting_buttons_script)
        print("   Results:")
        for key, data in analysis['formatting_buttons'].items():
            status = "✅" if data.get('found') else "❌"
            print(f"      {status} {key}: {data.get('className', 'N/A')[:40]}")
        
        # 저장
        output_file = Path('docs/text_area_analysis.json')
        output_file.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding='utf-8')
        
        print(f"\n✅ Text area analysis saved to: {output_file}")
        print("\n" + "="*60)
        print("Press Enter to close browser...")
        input()
        
    finally:
        driver.quit()

if __name__ == '__main__':
    analyze_text_area()
