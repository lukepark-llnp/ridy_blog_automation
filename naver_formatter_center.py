"""네이버 에디터 Center Aligned 포맷터 - 정렬 지원"""
import time
import logging
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import platform

logger = logging.getLogger(__name__)


class NaverFormatterCenter:
    """
    Center Aligned 포맷터:
    - pyperclip으로 텍스트 붙여넣기
    - 툴바 버튼 클릭으로 정렬/볼드 등 스타일 적용 (JS 주입 X)
    - 이미지 그룹 지원
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.is_mac = platform.system() == "Darwin"
        self.cmd_or_ctrl = Keys.COMMAND if self.is_mac else Keys.CONTROL
    
    def _focus_editor(self):
        """에디터에 포커스 (커서를 항상 맨 끝으로 이동)"""
        try:
            script = """
            var editor = document.querySelector('div[contenteditable="true"]');
            if (editor) {
                editor.focus();
                
                // 커서를 맨 끝으로 이동 (Range API 사용)
                var range = document.createRange();
                range.selectNodeContents(editor);
                range.collapse(false); // false = 끝점, true = 시작점
                
                var sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
                
                return true;
            }
            return false;
            """
            return self.driver.execute_script(script)
        except Exception as e:
            logger.error(f"❌ Focus failed: {e}")
            return False
    
    def _click_element_js(self, element):
        """JavaScript로 요소 강제 클릭 (가려짐 무시)"""
        try:
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            logger.warning(f"      ⚠️ JS Click failed: {e}")
            return False

    def _click_toolbar_button(self, name_keywords):
        """툴바 버튼 클릭 (이름/클래스 키워드로 검색)"""
        try:
            # 툴바 영역 내에서만 검색 (최적화)
            try:
                toolbars = self.driver.find_elements(By.CSS_SELECTOR, ".se-toolbar, .se-main-toolbar, [role='toolbar']")
                if toolbars:
                    buttons = toolbars[0].find_elements(By.TAG_NAME, "button")
                else:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
            except:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
            
            target_btn = None
            
            for btn in buttons:
                txt = btn.text
                cls = btn.get_attribute("class") or ""
                title = btn.get_attribute("title") or ""
                aria_label = btn.get_attribute("aria-label") or ""
                
                # 키워드 매칭 (리스트)
                for keyword in name_keywords:
                    if (keyword in txt or keyword in cls or keyword in title or keyword in aria_label):
                        target_btn = btn
                        break
                if target_btn:
                    break
            
            if target_btn:
                # JS 클릭 사용 (가려짐 방지)
                self._click_element_js(target_btn)
                logger.info(f"      👉 Clicked button (JS): {name_keywords[0]}...")
                return True
            else:
                logger.warning(f"      ⚠️ Button not found: {name_keywords}")
                return False
                
        except Exception as e:
            logger.warning(f"      ⚠️ Click button failed: {e}")
            return False

    def _apply_center_align(self):
        """현재 라인에 가운데 정렬 적용 (드롭다운 방식 + JS 클릭)"""
        try:
            # 1. 정렬 드롭다운 버튼 찾기
            dropdown_btns = self.driver.find_elements(By.CSS_SELECTOR, ".se-toolbar-item-align button")
            if not dropdown_btns:
                logger.warning("      ⚠️ Align dropdown button not found")
                return False
            
            # 드롭다운 열기 (JS 클릭)
            self._click_element_js(dropdown_btns[0])
            time.sleep(0.5)
            
            # 2. '가운데 정렬' 옵션 선택 (Luke님이 찾아주신 정확한 클래스명!)
            # .se-toolbar-option-align-center-button
            center_btns = self.driver.find_elements(By.CSS_SELECTOR, ".se-toolbar-option-align-center-button, button[data-value='center']")
            
            if not center_btns:
                # 못 찾으면 텍스트로 찾기 (fallback)
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    aria_label = btn.get_attribute("aria-label") or ""
                    title = btn.get_attribute("title") or ""
                    
                    if btn.is_displayed() and ("가운데" in aria_label or "가운데" in title):
                        center_btns = [btn]
                        break
            
            if center_btns:
                # JS 클릭
                self._click_element_js(center_btns[0])
                logger.info("      👉 Clicked Center Align button (JS)")
                return True
            else:
                logger.warning("      ⚠️ Center align option not found")
                return False
                
        except Exception as e:
            logger.warning(f"      ⚠️ Align failed: {e}")
            return False
    
    def _apply_bold(self):
        """현재 선택 영역에 볼드 적용 (버튼 클릭 방식)"""
        # 클래스명 수정: se-bold-toolbar-button
        # Luke님 제보: <button ... class="se-bold-toolbar-button ..."><span class="se-blind">굵게</span></button>
        # 텍스트가 안 보일 수 있으므로 클래스로 찾음
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, "button.se-bold-toolbar-button")
            self._click_element_js(btn)
            logger.info("      👉 Clicked Bold button (JS)")
            return True
        except:
            # Fallback: title로 찾기
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, "button[title='굵기 적용'], button[data-name='bold']")
                self._click_element_js(btn)
                logger.info("      👉 Clicked Bold button (JS/Fallback)")
                return True
            except:
                logger.warning("      ⚠️ Bold button not found")
                return False

    def _apply_font_size(self, size):
        """폰트 크기 변경 (드롭다운 방식 + JS 클릭)"""
        if size == 'normal':
            return
            
        try:
            # 1. 폰트 크기 드롭다운 버튼 찾기 (se-toolbar-item-font-size-code)
            dropdown_btns = self.driver.find_elements(By.CSS_SELECTOR, ".se-toolbar-item-font-size-code button")
            if not dropdown_btns:
                logger.warning("      ⚠️ Font size dropdown not found")
                return False
            
            # 드롭다운 열기
            self._click_element_js(dropdown_btns[0])
            time.sleep(0.5)
            
            # 2. 크기 선택 (19, 24, 30 등)
            target_size = '19' # large
            if size == 'xlarge':
                target_size = '24' # 더 크게
            elif size == 'xxlarge':
                target_size = '30'
                
            # 버튼 찾기: data-value="19" 등
            size_btns = self.driver.find_elements(By.CSS_SELECTOR, f"button[data-value='{target_size}']")
            
            if size_btns:
                self._click_element_js(size_btns[0])
                logger.info(f"      👉 Changed font size to {target_size}")
                return True
            else:
                logger.warning(f"      ⚠️ Font size {target_size} option not found")
                return False
                
        except Exception as e:
            logger.warning(f"      ⚠️ Font size change failed: {e}")
            return False

    def type_text(self, text, align='left', bold=False, size='normal', color='black'):
        """텍스트 입력 (클립보드 방식 + 개행문자 2개)"""
        try:
            if not self._focus_editor():
                logger.warning("  ⚠️ Focus failed, trying anyway...")
            
            # 1. 정렬 설정
            if align == 'center':
                self._apply_center_align()
                time.sleep(0.1)
            
            # 2. 볼드 설정
            if bold:
                self._apply_bold()
                time.sleep(0.1)
                
            # 3. 폰트 크기 설정 (추가됨!)
            if size != 'normal':
                self._apply_font_size(size)
                time.sleep(0.1)
            
            # 4. 텍스트 입력
            paste_text = text + "\n\n"
            
            pyperclip.copy(paste_text)
            time.sleep(0.1)
            
            # 붙여넣기
            self._focus_editor()
            actions = ActionChains(self.driver)
            actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
            time.sleep(0.3)
            
            # 5. 스타일 해제 (다음 텍스트를 위해)
            if bold:
                self._apply_bold()
                time.sleep(0.1)
            
            if size != 'normal':
                # 폰트 크기 복구는 복잡하므로, 다음 텍스트 입력 시 다시 설정하는 것으로 가정
                # 하지만 기본값으로 돌려놓는 게 안전함 (16px)
                # self._apply_font_size('16') # normal
                pass

            logger.info(f"      ✅ Text: {text[:30]}... [align={align}, bold={bold}, size={size}]")
            return True
            
        except Exception as e:
            logger.error(f"❌ type_text failed: {e}")
            return False
    
    def insert_divider(self):
        """구분선 추가 (버튼 클릭 + 텍스트 Fallback)"""
        try:
            # 구분선 버튼 클릭 (JS 강제 클릭)
            try:
                # se-toolbar-option-insert-horizontal-line-default-button
                # 또는 data-name="horizontal-line"
                btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-name='horizontal-line'], button[data-name='insert-horizontal-line']")
                
                # 포커스 먼저
                self._focus_editor()
                time.sleep(0.1)
                
                self._click_element_js(btn)
                logger.info("      👉 Clicked Divider button (JS)")
                
                # 렌더링 대기
                time.sleep(1.0)
                
                # 줄바꿈 (구분선 다음 줄로 이동)
                self._focus_editor()
                ActionChains(self.driver).send_keys(Keys.RETURN).perform()
                
                return True
            except:
                # 버튼 실패 시 텍스트로 대체 (확실하게 보이도록 유니코드 사용)
                logger.warning("      ⚠️ Divider button not found, using text fallback")
                return self.type_text("━━━━━━━━━━━━━━━━━━━━", align='center', bold=True)
        except Exception as e:
            logger.error(f"❌ insert_divider failed: {e}")
            return False
    
    def type_list(self, items, align='left'):
        """리스트 입력 + 정렬"""
        try:
            # 불렛 포인트 버튼 클릭 시도 (선택 사항)
            # keywords = ["se-toolbar-button-list", "목록"]
            # self._click_toolbar_button(keywords)
            
            for item in items:
                bullet_text = f"• {item}"
                self.type_text(bullet_text, align=align, bold=False)
            
            logger.info(f"      ✅ List ({len(items)} items, align={align})")
            return True
            
        except Exception as e:
            logger.error(f"❌ type_list failed: {e}")
            return False
    
    def insert_emoji(self, emoji, size='large'):
        """이모지 입력"""
        try:
            if size == 'large':
                # 큰 이모지는 스티커처럼 보이게
                # 정렬 먼저 적용하고 입력?
                # 입력하고 정렬 적용?
                pass
            
            return self.type_text(emoji, align='center', bold=False)
            
        except Exception as e:
            logger.error(f"❌ insert_emoji failed: {e}")
            return False
    
    def insert_sticker(self, sticker_id):
        """스티커 = 이모지 대체"""
        # 실제 스티커 버튼을 클릭하려면 복잡함 (팝업 뜨고 선택해야 함)
        # 일단 텍스트 이모지로 대체하되 가운데 정렬 확실하게
        if sticker_id == 45:
            return self.insert_emoji('🐶💕', size='large')
        elif sticker_id == 46:
            return self.insert_emoji('🐶👍', size='large')
        else:
            return self.insert_emoji('🐶', size='large')
    
    def insert_link(self, url, text):
        """링크 입력 (실제 하이퍼링크로)"""
        try:
            # 1. 텍스트 먼저 입력
            logger.info(f"      → Inserting link: {text}")
            
            # 클립보드에 텍스트 복사
            import pyperclip
            pyperclip.copy(text)
            
            # 붙여넣기
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
            actions.key_down(cmd_or_ctrl).send_keys('v').key_up(cmd_or_ctrl).perform()
            time.sleep(0.3)
            
            # 2. 텍스트 전체 선택 (JS로 확실하게)
            try:
                self.driver.execute_script("""
                    var sel = window.getSelection();
                    if (sel.rangeCount > 0) {
                        var range = document.createRange();
                        var node = sel.focusNode;
                        // 현재 포커스된 노드의 전체 내용 선택
                        if (node) {
                            // 텍스트 노드면 부모 요소 기준
                            var target = (node.nodeType === 3) ? node.parentNode : node;
                            range.selectNodeContents(target);
                            sel.removeAllRanges();
                            sel.addRange(range);
                        }
                    }
                """)
                logger.info("      → Selected text via JS")
            except:
                # Fallback: Shift+Home
                actions = ActionChains(self.driver)
                actions.key_down(Keys.SHIFT).send_keys(Keys.HOME).key_up(Keys.SHIFT).perform()
            
            time.sleep(0.5)
            
            # 3. 링크 버튼 클릭 (툴바에서 찾기 또는 단축키)
            try:
                # 1순위: 단축키 Ctrl+K / Cmd+K
                actions = ActionChains(self.driver)
                actions.key_down(cmd_or_ctrl).send_keys('k').key_up(cmd_or_ctrl).perform()
                time.sleep(1.0)
                
                # 링크 모달 확인
                try:
                    url_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='URL'], input[type='url'], input[name='url']")
                    logger.info("      → Link modal opened via shortcut")
                except:
                    # 2순위: 버튼 클릭 (JS로 더 강력하게 찾기)
                    logger.info("      → Shortcut failed, searching button via JS...")
                    script = """
                    var btns = document.querySelectorAll('button');
                    for (var i=0; i<btns.length; i++) {
                        var btn = btns[i];
                        var name = btn.getAttribute('data-name') || '';
                        var cls = btn.className || '';
                        var title = btn.getAttribute('title') || '';
                        if (name === 'link' || cls.includes('se-toolbar-button-link') || title.includes('링크')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                    """
                    result = self.driver.execute_script(script)
                    if result:
                        logger.info("      → Clicked link button via JS loop")
                        time.sleep(1.0)
                    else:
                        raise Exception("Link button not found")
                    
                    url_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='URL'], input[type='url'], input[name='url']")
                
                # 4. URL 입력
                url_input.clear()
                url_input.send_keys(url)
                time.sleep(0.2)
                
                # 입력 이벤트 트리거 (필수)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", url_input)
                time.sleep(0.2)
                
                # Enter 키 입력 (확인 버튼 누르는 효과)
                url_input.send_keys(Keys.RETURN)
                time.sleep(0.5)
                
                # 5. 새창 열기 체크박스
                try:
                    # 체크박스 찾기 (여러 선택자 시도)
                    checkbox_script = """
                    var inputs = document.querySelectorAll('input[type="checkbox"]');
                    for (var i=0; i<inputs.length; i++) {
                        var label = inputs[i].nextElementSibling; # 보통 라벨이 뒤에 있음
                        if ((inputs[i].value === '_blank') || (label && label.textContent.includes('새 창'))) {
                            if (!inputs[i].checked) inputs[i].click();
                            return true;
                        }
                    }
                    return false;
                    """
                    self.driver.execute_script(checkbox_script)
                except:
                    pass
                
                # 6. 확인 버튼 클릭
                confirm_script = """
                var btns = document.querySelectorAll('button');
                for (var i=0; i<btns.length; i++) {
                    if (btns[i].className.includes('confirm') || btns[i].textContent.includes('확인') || btns[i].textContent.includes('적용')) {
                        btns[i].click();
                        return true;
                    }
                }
                return false;
                """
                self.driver.execute_script(confirm_script)
                time.sleep(0.5)
                
                logger.info(f"      ✅ Link inserted: {text} -> {url}")
                
                # 7. 줄바꿈
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.RIGHT).perform()
                time.sleep(0.1)
                
                pyperclip.copy("\n\n")
                actions.key_down(cmd_or_ctrl).send_keys('v').key_up(cmd_or_ctrl).perform()
                time.sleep(0.2)
                
                return True
                
            except Exception as link_error:
                logger.warning(f"      ⚠️ Link insertion failed: {link_error}")
                # 실패 시 텍스트로 폴백 (URL 포함)
                # 이미 텍스트는 입력되어 있으니 URL만 추가 (괄호 없이)
                # 괄호가 있으면 네이버 자동 링크가 괄호까지 포함시킴 (%29 문제)
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.END).perform() # 끝으로 이동
                pyperclip.copy(f" - {url}\n\n")
                actions.key_down(cmd_or_ctrl).send_keys('v').key_up(cmd_or_ctrl).perform()
                return True
            
        except Exception as e:
            logger.error(f"❌ insert_link failed: {e}")
            return False
    
    def finalize(self):
        """완료 (더미 함수)"""
        logger.info("📤 Finalize (no-op for Center formatter)")
        return True
