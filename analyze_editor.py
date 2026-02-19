#!/usr/bin/env python3
"""네이버 스마트에디터 ONE 완전 분석"""
import time
import pickle
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def analyze_editor():
    """에디터 구조 완전 분석"""
    
    # 브라우저 열기
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
        
        # 에디터 접속
        print("📍 Opening editor...")
        driver.get('https://blog.naver.com/ridyservice?Redirect=Write&categoryNo=28')
        time.sleep(3)
        
        # iframe 전환
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
        print("🔍 NAVER SMART EDITOR ONE - Complete Analysis")
        print("="*60 + "\n")
        
        analysis = {}
        
        # 1. 제목 영역
        print("1️⃣ Title Area Analysis...")
        title_script = """
        var titleArea = document.querySelector('.se-component.se-documentTitle');
        if (!titleArea) return null;
        
        return {
            container: titleArea.className,
            input: titleArea.querySelector('span.__se-node') ? 
                   titleArea.querySelector('span.__se-node').className : null,
            placeholder: titleArea.querySelector('.__se-placeholder') ?
                        titleArea.querySelector('.__se-placeholder').textContent : null,
            editable: titleArea.querySelector('[contenteditable]') ? true : false
        };
        """
        analysis['title'] = driver.execute_script(title_script)
        print(f"   ✅ Title: {json.dumps(analysis['title'], indent=2, ensure_ascii=False)}")
        
        # 2. 툴바 분석
        print("\n2️⃣ Toolbar Analysis...")
        toolbar_script = """
        var toolbar = document.querySelector('.se-toolbar');
        if (!toolbar) return null;
        
        var buttons = [];
        toolbar.querySelectorAll('button, .se-toolbar-group-button').forEach(btn => {
            buttons.push({
                text: btn.textContent.trim(),
                ariaLabel: btn.getAttribute('aria-label'),
                className: btn.className,
                title: btn.title,
                dataCommand: btn.getAttribute('data-command'),
                id: btn.id
            });
        });
        
        return {
            container: toolbar.className,
            buttonCount: buttons.length,
            buttons: buttons
        };
        """
        analysis['toolbar'] = driver.execute_script(toolbar_script)
        if analysis['toolbar']:
            print(f"   ✅ Toolbar: {analysis['toolbar']['buttonCount']} buttons found")
            print(f"   📋 First 10 buttons:")
            for btn in analysis['toolbar']['buttons'][:10]:
                print(f"      - {btn['text'] or btn['ariaLabel']} ({btn['className'][:50]}...)")
        
        # 3. 본문 영역 (핵심!)
        print("\n3️⃣ Content Area Analysis...")
        content_script = """
        var mainContainer = document.querySelector('.se-main-container');
        if (!mainContainer) return {error: 'Main container not found'};
        
        var components = [];
        mainContainer.querySelectorAll('.se-component').forEach(comp => {
            components.push({
                className: comp.className,
                tagName: comp.tagName,
                contenteditable: comp.getAttribute('contenteditable'),
                dataComponent: comp.getAttribute('data-component-type')
            });
        });
        
        var textArea = mainContainer.querySelector('.se-component.se-text');
        var textDetails = null;
        if (textArea) {
            textDetails = {
                className: textArea.className,
                contenteditable: textArea.getAttribute('contenteditable'),
                innerHTML: textArea.innerHTML.substring(0, 200),
                children: Array.from(textArea.children).map(child => ({
                    tagName: child.tagName,
                    className: child.className
                }))
            };
        }
        
        return {
            mainContainer: {
                className: mainContainer.className,
                tagName: mainContainer.tagName
            },
            componentCount: components.length,
            components: components,
            textArea: textDetails
        };
        """
        analysis['content'] = driver.execute_script(content_script)
        print(f"   ✅ Content area: {json.dumps(analysis['content'], indent=2, ensure_ascii=False)}")
        
        # 4. 이미지 업로드 메커니즘
        print("\n4️⃣ Image Upload Mechanism...")
        image_script = """
        var imageBtn = document.querySelector('button[aria-label*="사진"], button[data-command="image"]');
        var fileInputs = document.querySelectorAll('input[type="file"]');
        
        return {
            imageButton: imageBtn ? {
                ariaLabel: imageBtn.getAttribute('aria-label'),
                className: imageBtn.className,
                dataCommand: imageBtn.getAttribute('data-command')
            } : null,
            fileInputs: Array.from(fileInputs).map(input => ({
                id: input.id,
                name: input.name,
                accept: input.accept,
                multiple: input.multiple,
                className: input.className
            }))
        };
        """
        analysis['image'] = driver.execute_script(image_script)
        print(f"   ✅ Image: {json.dumps(analysis['image'], indent=2, ensure_ascii=False)}")
        
        # 5. 발행 버튼
        print("\n5️⃣ Publish Button Analysis...")
        publish_script = """
        var publishBtns = Array.from(document.querySelectorAll('button'))
            .filter(btn => btn.textContent.includes('발행') || btn.getAttribute('aria-label')?.includes('발행'));
        
        return publishBtns.map(btn => ({
            text: btn.textContent,
            ariaLabel: btn.getAttribute('aria-label'),
            className: btn.className,
            id: btn.id
        }));
        """
        analysis['publish'] = driver.execute_script(publish_script)
        print(f"   ✅ Publish buttons: {len(analysis['publish'])} found")
        
        # 6. 전체 DOM 구조 (간략)
        print("\n6️⃣ Overall DOM Structure...")
        structure_script = """
        var structure = {
            body: document.body.className,
            mainSections: Array.from(document.querySelectorAll('body > *')).map(el => ({
                tagName: el.tagName,
                id: el.id,
                className: el.className.substring(0, 50)
            }))
        };
        
        return structure;
        """
        analysis['structure'] = driver.execute_script(structure_script)
        print(f"   ✅ Structure captured")
        
        # 저장
        output_file = Path('docs/editor_analysis.json')
        output_file.parent.mkdir(exist_ok=True)
        output_file.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding='utf-8')
        
        print(f"\n✅ Analysis saved to: {output_file}")
        print("\n" + "="*60)
        print("Press Enter to close browser...")
        input()
        
    finally:
        driver.quit()

if __name__ == '__main__':
    analyze_editor()
