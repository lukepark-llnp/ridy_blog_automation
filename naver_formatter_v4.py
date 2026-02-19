"""네이버 에디터 포맷터 v4 - insertHTML 방식"""
import time
import logging
import html as html_lib
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class NaverFormatterV4:
    """
    insertHTML 방식으로 직접 포맷된 HTML 삽입
    - 선택/포맷 과정 없이 한 번에 처리
    - 더 안정적이고 빠름
    """
    
    def __init__(self, driver):
        """
        Args:
            driver: Selenium WebDriver (이미 iframe 안에 있어야 함)
        """
        self.driver = driver
    
    def _wait_for_editor(self):
        """에디터 준비 대기"""
        try:
            wait = WebDriverWait(self.driver, 5)
            editor = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            return True
        except Exception as e:
            logger.error(f"❌ Editor not ready: {e}")
            return False
    
    def _focus_editor(self):
        """에디터에 포커스"""
        try:
            script = """
            var editor = document.querySelector('div[contenteditable="true"]');
            if (editor) {
                editor.focus();
                // Move cursor to end
                var range = document.createRange();
                var sel = window.getSelection();
                range.selectNodeContents(editor);
                range.collapse(false);
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
    
    def _insert_html(self, html_content):
        """HTML 직접 삽입"""
        try:
            if not self._focus_editor():
                return False
            
            # JSON-safe HTML string
            safe_html = html_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            
            script = f"""
            document.execCommand('insertHTML', false, "{safe_html}");
            """
            
            self.driver.execute_script(script)
            time.sleep(0.15)
            return True
            
        except Exception as e:
            logger.error(f"❌ insertHTML failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def type_text(self, text, align='left', bold=False):
        """
        텍스트 입력 + 포맷 적용
        
        Args:
            text: 텍스트 내용
            align: 'left' | 'center' | 'right'
            bold: True | False
        """
        try:
            # HTML escape
            safe_text = html_lib.escape(text)
            
            # Bold wrap
            if bold:
                safe_text = f"<strong>{safe_text}</strong>"
            
            # Alignment style
            style_parts = []
            if align == 'center':
                style_parts.append('text-align: center')
            elif align == 'right':
                style_parts.append('text-align: right')
            
            style_attr = f' style="{"; ".join(style_parts)}"' if style_parts else ''
            
            # Build paragraph
            html_content = f'<p{style_attr}>{safe_text}</p>'
            
            # Insert
            if self._insert_html(html_content):
                logger.info(f"      ✅ Text: {text[:50]}... [align={align}, bold={bold}]")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ type_text failed: {e}")
            return False
    
    def insert_divider(self):
        """구분선 삽입"""
        try:
            divider = "─" * 30
            html_content = f'<p style="text-align: center;">{divider}</p>'
            
            if self._insert_html(html_content):
                logger.info("      ✅ Divider inserted")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ insert_divider failed: {e}")
            return False
    
    def type_list(self, items):
        """리스트 입력 (• 불렛)"""
        try:
            for item in items:
                safe_item = html_lib.escape(item)
                html_content = f'<p>• {safe_item}</p>'
                if not self._insert_html(html_content):
                    return False
            
            logger.info(f"      ✅ List ({len(items)} items)")
            return True
            
        except Exception as e:
            logger.error(f"❌ type_list failed: {e}")
            return False
    
    def insert_emoji(self, emoji, size='large'):
        """
        이모지 삽입 (가운데 정렬)
        
        Args:
            emoji: 이모지 문자
            size: 'small' | 'medium' | 'large'
        """
        try:
            # Size mapping
            font_size = {'small': '16px', 'medium': '24px', 'large': '32px'}.get(size, '24px')
            
            # Repeat for visual impact
            if size == 'large':
                emoji_text = emoji * 3
            elif size == 'medium':
                emoji_text = emoji * 2
            else:
                emoji_text = emoji
            
            html_content = f'<p style="text-align: center; font-size: {font_size};">{emoji_text}</p>'
            
            if self._insert_html(html_content):
                logger.info(f"      ✅ Emoji: {emoji}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ insert_emoji failed: {e}")
            return False
    
    def insert_sticker(self, sticker_id):
        """
        스티커 대신 이모지 사용
        
        Args:
            sticker_id: 45 | 46
        """
        if sticker_id == 45:
            return self.insert_emoji('🐶💕', size='large')
        elif sticker_id == 46:
            return self.insert_emoji('🐶👍', size='large')
        else:
            return self.insert_emoji('🐶', size='large')
    
    def insert_link(self, url, text):
        """
        링크 삽입
        
        Args:
            url: URL
            text: 링크 텍스트
        """
        try:
            safe_url = html_lib.escape(url)
            safe_text = html_lib.escape(text)
            
            html_content = f'<p style="text-align: center;"><a href="{safe_url}">{safe_text}</a></p>'
            
            if self._insert_html(html_content):
                logger.info(f"      ✅ Link: {text} → {url}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ insert_link failed: {e}")
            return False
