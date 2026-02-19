#!/usr/bin/env python3
"""네이버 스마트에디터 ONE 심층 분석 - 모든 요소 재귀 탐색"""
import time
import pickle
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def deep_analyze():
    """에디터 모든 요소 재귀 탐색"""
    
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
        print("🔍 DEEP ANALYSIS - All Elements Recursive Scan")
        print("="*60 + "\n")
        
        analysis = {}
        
        # 1. 모든 contenteditable 요소 찾기
        print("1️⃣ Finding ALL contenteditable elements...")
        contenteditable_script = """
        var editables = document.querySelectorAll('[contenteditable="true"]');
        return Array.from(editables).map(el => ({
            tagName: el.tagName,
            className: el.className,
            id: el.id,
            textContent: el.textContent.substring(0, 50),
            innerHTML: el.innerHTML.substring(0, 200),
            parentClassName: el.parentElement ? el.parentElement.className : null
        }));
        """
        analysis['contenteditable'] = driver.execute_script(contenteditable_script)
        print(f"   ✅ Found {len(analysis['contenteditable'])} contenteditable elements:")
        for idx, el in enumerate(analysis['contenteditable']):
            print(f"      [{idx+1}] {el['tagName']}.{el['className'][:40]}")
        
        # 2. 모든 .se- 클래스 요소 찾기
        print("\n2️⃣ Finding ALL .se- elements...")
        se_elements_script = """
        var seElements = document.querySelectorAll('[class*="se-"]');
        var grouped = {};
        
        seElements.forEach(el => {
            if (typeof el.className !== 'string') return;
            var mainClass = el.className.split(' ').find(c => c.startsWith('se-'));
            if (!mainClass) return;
            
            if (!grouped[mainClass]) {
                grouped[mainClass] = {
                    count: 0,
                    examples: []
                };
            }
            
            grouped[mainClass].count++;
            if (grouped[mainClass].examples.length < 2) {
                grouped[mainClass].examples.push({
                    tagName: el.tagName,
                    fullClassName: el.className,
                    id: el.id,
                    contenteditable: el.getAttribute('contenteditable')
                });
            }
        });
        
        return grouped;
        """
        analysis['se_elements'] = driver.execute_script(se_elements_script)
        print(f"   ✅ Found {len(analysis['se_elements'])} unique .se- classes:")
        for cls, data in sorted(analysis['se_elements'].items())[:20]:
            print(f"      - {cls}: {data['count']} instances")
        
        # 3. 텍스트 에디터 영역 정확한 셀렉터 찾기
        print("\n3️⃣ Finding TEXT EDITOR area...")
        text_editor_script = """
        // 다양한 셀렉터 시도
        var selectors = [
            '.se-main-container',
            '.se-component.se-text',
            '.se-text-paragraph',
            'div[contenteditable="true"]',
            '.se-section',
            '.se-section-container',
            '#smartEditor'
        ];
        
        var results = {};
        selectors.forEach(selector => {
            var elements = document.querySelectorAll(selector);
            results[selector] = {
                found: elements.length > 0,
                count: elements.length,
                examples: Array.from(elements).slice(0, 2).map(el => ({
                    tagName: el.tagName,
                    className: el.className,
                    id: el.id,
                    contenteditable: el.getAttribute('contenteditable'),
                    innerHTML: el.innerHTML.substring(0, 150)
                }))
            };
        });
        
        return results;
        """
        analysis['text_editor_search'] = driver.execute_script(text_editor_script)
        print("   Results:")
        for selector, result in analysis['text_editor_search'].items():
            status = "✅" if result['found'] else "❌"
            print(f"      {status} {selector}: {result['count']} found")
        
        # 4. React 구조 확인
        print("\n4️⃣ Checking React structure...")
        react_script = """
        var root = document.querySelector('#root');
        if (!root) return {error: 'No root found'};
        
        function getStructure(el, depth = 0, maxDepth = 5) {
            if (depth > maxDepth) return '...';
            
            var structure = {
                tagName: el.tagName,
                className: el.className.substring(0, 50),
                id: el.id,
                children: []
            };
            
            for (var i = 0; i < Math.min(el.children.length, 5); i++) {
                structure.children.push(getStructure(el.children[i], depth + 1, maxDepth));
            }
            
            if (el.children.length > 5) {
                structure.children.push('... and ' + (el.children.length - 5) + ' more');
            }
            
            return structure;
        }
        
        return getStructure(root);
        """
        analysis['react_structure'] = driver.execute_script(react_script)
        print("   ✅ React structure captured")
        
        # 5. 툴바 버튼들의 onClick/data 속성 분석
        print("\n5️⃣ Analyzing toolbar button events...")
        toolbar_events_script = """
        var toolbar = document.querySelector('.se-toolbar');
        if (!toolbar) return [];
        
        var buttons = toolbar.querySelectorAll('button');
        return Array.from(buttons).map(btn => ({
            text: btn.textContent.substring(0, 30).trim(),
            className: btn.className.split(' ').slice(0, 3).join(' '),
            onclick: btn.onclick ? 'has onclick' : null,
            dataAttrs: Array.from(btn.attributes)
                .filter(attr => attr.name.startsWith('data-'))
                .map(attr => ({name: attr.name, value: attr.value}))
        }));
        """
        analysis['toolbar_events'] = driver.execute_script(toolbar_events_script)
        print(f"   ✅ Analyzed {len(analysis['toolbar_events'])} buttons")
        
        # 저장
        output_file = Path('docs/editor_deep_analysis.json')
        output_file.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding='utf-8')
        
        print(f"\n✅ Deep analysis saved to: {output_file}")
        print("\n" + "="*60)
        print("Press Enter to close browser...")
        input()
        
    finally:
        driver.quit()

if __name__ == '__main__':
    deep_analyze()
