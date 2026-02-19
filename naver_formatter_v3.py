"""네이버 에디터 포맷터 v3 - execCommand 완전 구현"""
import time
import logging
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip
import platform

logger = logging.getLogger(__name__)


class NaverFormatterV3:
    """
    execCommand 기반 완전한 포맷터
    - 텍스트 선택 후 포맷 적용
    - document.execCommand() 사용
    - 네이버 에디터 구조 완전 이해 기반
    """
    
    def __init__(self, driver):
        """
        Args:
            driver: Selenium WebDriver (이미 iframe 안에 있어야 함)
        """
        self.driver = driver
        self.is_mac = platform.system() == "Darwin"
        
    def _get_editor(self):
        """에디터 영역 찾기 (현재 iframe 컨텍스트에서)"""
        try:
            # Wait for contenteditable div to be present and clickable
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            wait = WebDriverWait(self.driver, 5)
            editor = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            return editor
        except Exception as e:
            logger.error(f"❌ Editor not found or not clickable: {e}")
            return None
    
    def _focus_editor(self):
        """에디터에 포커스 (JavaScript 사용)"""
        try:
            # JavaScript로 직접 포커스 (더 안정적)
            script = """
            var editor = document.querySelector('div[contenteditable="true"]');
            if (editor) {
                editor.focus();
                return true;
            }
            return false;
            """
            
            result = self.driver.execute_script(script)
            time.sleep(0.1)
            
            if result:
                return True
            else:
                logger.error("❌ Editor not found for focus")
                return False
                
        except Exception as e:
            logger.error(f"❌ Focus failed: {e}")
            return False
    
    def _paste_text(self, text):
        """클립보드로 텍스트 붙여넣기"""
        try:
            pyperclip.copy(text)
            time.sleep(0.1)
            
            actions = ActionChains(self.driver)
            if self.is_mac:
                actions.key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
            else:
                actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            
            time.sleep(0.2)
            return True
        except Exception as e:
            logger.error(f"❌ Paste failed: {e}")
            return False
    
    def _select_last_paragraph(self):
        """마지막 단락 선택 (방금 입력한 텍스트) - Naver 구조 기반"""
        try:
            # Wait a bit for Naver to process the pasted content
            time.sleep(0.3)
            
            # Naver는 .se-text-paragraph 안에 텍스트를 넣음
            script = """
            var editor = document.querySelector('div[contenteditable="true"]');
            var debug = {};
            
            // Debug: check editor content
            debug.editorHTML = editor.innerHTML.substring(0, 200);
            debug.editorChildCount = editor.childNodes.length;
            
            // Try .se-text-paragraph first (Naver's structure)
            var paragraphs = editor.querySelectorAll('.se-text-paragraph');
            debug.seTextParagraphCount = paragraphs.length;
            
            if (paragraphs.length === 0) {
                // Fallback to regular p tags
                paragraphs = editor.querySelectorAll('p');
                debug.pTagCount = paragraphs.length;
            }
            
            if (paragraphs.length === 0) {
                // Fallback to div.se-component.se-text
                paragraphs = editor.querySelectorAll('.se-component.se-text');
                debug.seComponentCount = paragraphs.length;
            }
            
            if (paragraphs.length === 0) {
                // Last resort: any child node with text
                var nodes = Array.from(editor.childNodes).filter(n => n.textContent.trim());
                paragraphs = nodes;
                debug.textNodeCount = nodes.length;
            }
            
            console.log('DEBUG:', JSON.stringify(debug));
            
            if (paragraphs.length > 0) {
                var lastP = paragraphs[paragraphs.length - 1];
                var range = document.createRange();
                
                // Try to find the text node to select
                var textNode = lastP.querySelector && lastP.querySelector('span.__se-node');
                if (!textNode) {
                    textNode = lastP.querySelector && lastP.querySelector('.se-text-paragraph');
                }
                if (!textNode) {
                    textNode = lastP;
                }
                
                range.selectNodeContents(textNode);
                
                var selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                
                console.log('Selected:', lastP.textContent ? lastP.textContent.substring(0, 50) : 'empty');
                return true;
            }
            
            console.log('No paragraph found after all attempts');
            return false;
            """
            
            result = self.driver.execute_script(script)
            time.sleep(0.1)
            
            if not result:
                # Get debug info from console
                logs = self.driver.get_log('browser')
                for entry in logs[-5:]:  # Last 5 log entries
                    if 'DEBUG' in entry['message']:
                        logger.warning(f"  ⚠️ Debug: {entry['message']}")
                logger.warning("  ⚠️ Could not find paragraph to select")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Select failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_bold(self):
        """볼드 적용 (선택된 텍스트에)"""
        try:
            self.driver.execute_script("document.execCommand('bold', false, null);")
            time.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"❌ Bold failed: {e}")
            return False
    
    def _apply_center(self):
        """가운데 정렬 (선택된 텍스트에)"""
        try:
            self.driver.execute_script("document.execCommand('justifyCenter', false, null);")
            time.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"❌ Center failed: {e}")
            return False
    
    def _apply_right(self):
        """오른쪽 정렬 (선택된 텍스트에)"""
        try:
            self.driver.execute_script("document.execCommand('justifyRight', false, null);")
            time.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"❌ Right align failed: {e}")
            return False
    
    def _clear_selection(self):
        """선택 해제"""
        try:
            self.driver.execute_script("window.getSelection().removeAllRanges();")
            time.sleep(0.05)
        except Exception as e:
            logger.error(f"❌ Clear selection failed: {e}")
    
    def _move_cursor_to_end(self):
        """커서를 맨 끝으로 이동"""
        try:
            script = """
            var editor = document.querySelector('div[contenteditable="true"]');
            var range = document.createRange();
            var selection = window.getSelection();
            
            range.selectNodeContents(editor);
            range.collapse(false); // 끝으로
            selection.removeAllRanges();
            selection.addRange(range);
            """
            
            self.driver.execute_script(script)
            time.sleep(0.05)
        except Exception as e:
            logger.error(f"❌ Move cursor failed: {e}")
    
    def type_text(self, text, align='left', bold=False):
        """
        텍스트 입력 + 포맷 적용
        
        Args:
            text: 텍스트 내용
            align: 'left' | 'center' | 'right'
            bold: True | False
        """
        try:
            # 1. 에디터 포커스
            if not self._focus_editor():
                return False
            
            # 2. 텍스트 붙여넣기
            if not self._paste_text(text):
                return False
            
            # 3. 방금 입력한 단락 선택
            if not self._select_last_paragraph():
                logger.warning("  ⚠️ Selection failed, formatting skipped")
                self._clear_selection()
                self._move_cursor_to_end()
                return True  # 텍스트는 입력됨
            
            # 4. 포맷 적용
            if bold:
                self._apply_bold()
            
            if align == 'center':
                self._apply_center()
            elif align == 'right':
                self._apply_right()
            
            # 5. 선택 해제 + 커서 이동
            self._clear_selection()
            self._move_cursor_to_end()
            
            # 6. Enter로 다음 단락 준비
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.RETURN).perform()
            time.sleep(0.1)
            
            logger.info(f"      ✅ Text: {text[:50]}... [align={align}, bold={bold}]")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ type_text failed: {e}")
            return False
    
    def insert_divider(self):
        """구분선 삽입"""
        try:
            divider = "─" * 30
            return self.type_text(divider, align='center')
            
        except Exception as e:
            logger.error(f"    ❌ insert_divider failed: {e}")
            return False
    
    def type_list(self, items):
        """리스트 입력 (• 불렛)"""
        try:
            for item in items:
                text = f"• {item}"
                if not self.type_text(text, align='left'):
                    return False
            
            logger.info(f"      ✅ List inserted ({len(items)} items)")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ type_list failed: {e}")
            return False
    
    def insert_emoji(self, emoji, size='large'):
        """
        이모지 삽입 (가운데 정렬)
        
        Args:
            emoji: 이모지 문자 (예: '🐶', '👍')
            size: 'small' | 'medium' | 'large'
        """
        try:
            # 이모지 여러 개로 크기 효과
            if size == 'large':
                emoji_text = emoji * 3
            elif size == 'medium':
                emoji_text = emoji * 2
            else:
                emoji_text = emoji
            
            return self.type_text(emoji_text, align='center')
            
        except Exception as e:
            logger.error(f"    ❌ insert_emoji failed: {e}")
            return False
    
    def insert_sticker(self, sticker_id):
        """
        스티커 대신 이모지 사용
        
        Args:
            sticker_id: 45 (하트 강아지) | 46 (엄지척 강아지)
        """
        if sticker_id == 45:
            return self.insert_emoji('🐶💕', size='large')
        elif sticker_id == 46:
            return self.insert_emoji('🐶👍', size='large')
        else:
            return self.insert_emoji('🐶', size='large')
    
    def insert_link(self, url, text):
        """
        링크 삽입 (텍스트 + URL)
        
        Args:
            url: 링크 URL
            text: 표시할 텍스트
        """
        try:
            # 일단 텍스트로 입력 (나중에 createLink로 개선 가능)
            link_text = f"{text} ({url})"
            return self.type_text(link_text, align='center', bold=False)
            
        except Exception as e:
            logger.error(f"    ❌ insert_link failed: {e}")
            return False
