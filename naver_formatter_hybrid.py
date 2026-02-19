"""네이버 에디터 하이브리드 포맷터 - 실용적 접근"""
import time
import logging
import pyperclip
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import platform

logger = logging.getLogger(__name__)


class NaverFormatterHybrid:
    """
    하이브리드 방식:
    - pyperclip으로 텍스트 붙여넣기 (Naver가 구조 자동 생성)
    - 간단한 포맷팅 (복잡한 selection 없이)
    - 실용성 우선 - 일단 작동하는 게 목표!
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.is_mac = platform.system() == "Darwin"
        self.cmd_or_ctrl = Keys.COMMAND if self.is_mac else Keys.CONTROL
    
    def _focus_editor(self):
        """에디터에 포커스"""
        try:
            script = """
            var editor = document.querySelector('div[contenteditable="true"]');
            if (editor) {
                editor.focus();
                return true;
            }
            return false;
            """
            return self.driver.execute_script(script)
        except Exception as e:
            logger.error(f"❌ Focus failed: {e}")
            return False
    
    def _paste_text(self, text):
        """클립보드로 텍스트 붙여넣기"""
        try:
            if not self._focus_editor():
                logger.warning("  ⚠️ Focus failed, trying anyway...")
            
            # 클립보드에 복사
            pyperclip.copy(text)
            time.sleep(0.15)
            
            # Cmd/Ctrl + V
            actions = ActionChains(self.driver)
            actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
            time.sleep(0.3)  # 더 긴 대기 - Naver가 처리할 시간
            
            return True
        except Exception as e:
            logger.error(f"❌ Paste failed: {e}")
            return False
    
    def _press_enter(self, count=1):
        """Enter 키 누르기 - JavaScript로 더 확실하게"""
        try:
            # Try keyboard first
            actions = ActionChains(self.driver)
            for _ in range(count):
                actions.send_keys(Keys.RETURN).perform()
                time.sleep(0.1)  # 더 긴 대기
            
            # Verify with JavaScript
            script = """
            var editor = document.querySelector('div[contenteditable="true"]');
            if (editor) {
                // Insert line break
                var br = document.createElement('br');
                var range = window.getSelection().getRangeAt(0);
                range.insertNode(br);
                range.setStartAfter(br);
                range.collapse(true);
                return true;
            }
            return false;
            """
            self.driver.execute_script(script)
            time.sleep(0.1)
            
            return True
        except Exception as e:
            logger.error(f"❌ Enter failed: {e}")
            return False
    
    def type_text(self, text, align='left', bold=False):
        """
        텍스트 입력
        
        Args:
            text: 텍스트 내용
            align: 'left' | 'center' | 'right' (현재 무시 - 나중에 구현)
            bold: True이면 **텍스트** 형태로 (나중에 수동 포맷)
        """
        try:
            # Bold는 일단 텍스트로만 (나중에 toolbar로 처리 가능)
            if bold:
                display_text = f"**{text}**"
            else:
                display_text = text
            
            # 줄바꿈 추가 (Naver가 단락으로 인식하도록)
            display_text_with_break = display_text + "\n"
            
            # 붙여넣기
            if not self._paste_text(display_text_with_break):
                return False
            
            # 추가 Enter로 단락 분리 확실히
            self._press_enter()
            
            logger.info(f"      ✅ Text: {text[:50]}... [bold={bold}]")
            return True
            
        except Exception as e:
            logger.error(f"❌ type_text failed: {e}")
            return False
    
    def insert_divider(self):
        """구분선 삽입"""
        try:
            divider = "─" * 30
            
            if not self._paste_text(divider):
                return False
            
            self._press_enter()
            
            logger.info("      ✅ Divider")
            return True
        except Exception as e:
            logger.error(f"❌ insert_divider failed: {e}")
            return False
    
    def type_list(self, items):
        """리스트 입력 (• 불렛)"""
        try:
            for item in items:
                bullet_text = f"• {item}"
                if not self._paste_text(bullet_text):
                    return False
                self._press_enter()
            
            logger.info(f"      ✅ List ({len(items)} items)")
            return True
            
        except Exception as e:
            logger.error(f"❌ type_list failed: {e}")
            return False
    
    def insert_emoji(self, emoji, size='large'):
        """
        이모지 삽입
        
        Args:
            emoji: 이모지 문자
            size: 'small' | 'medium' | 'large'
        """
        try:
            # Size는 반복으로 표현
            if size == 'large':
                emoji_text = emoji * 3
            elif size == 'medium':
                emoji_text = emoji * 2
            else:
                emoji_text = emoji
            
            if not self._paste_text(emoji_text):
                return False
            
            self._press_enter()
            
            logger.info(f"      ✅ Emoji: {emoji}")
            return True
            
        except Exception as e:
            logger.error(f"❌ insert_emoji failed: {e}")
            return False
    
    def insert_sticker(self, sticker_id):
        """스티커 = 이모지"""
        if sticker_id == 45:
            return self.insert_emoji('🐶💕', size='large')
        elif sticker_id == 46:
            return self.insert_emoji('🐶👍', size='large')
        else:
            return self.insert_emoji('🐶', size='large')
    
    def insert_link(self, url, text):
        """링크 삽입 (일단 텍스트로)"""
        try:
            link_text = f"{text} ({url})"
            
            if not self._paste_text(link_text):
                return False
            
            self._press_enter()
            
            logger.info(f"      ✅ Link: {text}")
            return True
            
        except Exception as e:
            logger.error(f"❌ insert_link failed: {e}")
            return False
    
    def apply_center_to_last_line(self):
        """
        마지막 줄에 가운데 정렬 적용 (선택적 사용)
        - 나중에 구현
        """
        pass
    
    def apply_bold_to_selection(self):
        """
        선택된 텍스트에 볼드 (선택적 사용)
        - 나중에 구현
        """
        pass
