"""네이버 에디터 Simple 포맷터 - 모든 텍스트 한 번에 붙여넣기"""
import time
import logging
import pyperclip
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import platform

logger = logging.getLogger(__name__)


class NaverFormatterSimple:
    """
    Simple 방식:
    - 모든 텍스트를 미리 조합
    - 단락은 빈 줄(\\n\\n)로 구분
    - 한 번에 붙여넣기
    - 가장 안정적!
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.is_mac = platform.system() == "Darwin"
        self.cmd_or_ctrl = Keys.COMMAND if self.is_mac else Keys.CONTROL
        self.content_buffer = []  # 텍스트 버퍼
    
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
    
    def _flush_buffer(self):
        """버퍼 내용을 한 번에 붙여넣기"""
        if not self.content_buffer:
            return True
        
        try:
            if not self._focus_editor():
                logger.warning("  ⚠️ Focus failed, trying anyway...")
            
            # 모든 내용을 빈 줄로 구분해서 합치기
            full_text = "\n\n".join(self.content_buffer)
            
            # 클립보드에 복사
            pyperclip.copy(full_text)
            time.sleep(0.2)
            
            # Cmd/Ctrl + V
            actions = ActionChains(self.driver)
            actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
            time.sleep(0.5)  # Naver 처리 대기
            
            logger.info(f"      ✅ Flushed {len(self.content_buffer)} items ({len(full_text)} chars)")
            
            # 버퍼 초기화
            self.content_buffer = []
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Flush failed: {e}")
            return False
    
    def type_text(self, text, align='left', bold=False):
        """텍스트를 버퍼에 추가"""
        try:
            # Bold는 별표로
            if bold:
                display_text = f"**{text}**"
            else:
                display_text = text
            
            # 버퍼에 추가
            self.content_buffer.append(display_text)
            
            logger.info(f"      ✅ Buffered text: {text[:50]}... [bold={bold}]")
            return True
            
        except Exception as e:
            logger.error(f"❌ type_text failed: {e}")
            return False
    
    def insert_divider(self):
        """구분선을 버퍼에 추가"""
        try:
            divider = "─" * 30
            self.content_buffer.append(divider)
            
            logger.info("      ✅ Buffered divider")
            return True
        except Exception as e:
            logger.error(f"❌ insert_divider failed: {e}")
            return False
    
    def type_list(self, items):
        """리스트를 버퍼에 추가"""
        try:
            for item in items:
                bullet_text = f"• {item}"
                self.content_buffer.append(bullet_text)
            
            logger.info(f"      ✅ Buffered list ({len(items)} items)")
            return True
            
        except Exception as e:
            logger.error(f"❌ type_list failed: {e}")
            return False
    
    def insert_emoji(self, emoji, size='large'):
        """이모지를 버퍼에 추가"""
        try:
            # Size는 반복으로
            if size == 'large':
                emoji_text = emoji * 3
            elif size == 'medium':
                emoji_text = emoji * 2
            else:
                emoji_text = emoji
            
            self.content_buffer.append(emoji_text)
            
            logger.info(f"      ✅ Buffered emoji: {emoji}")
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
        """링크를 버퍼에 추가"""
        try:
            link_text = f"{text} ({url})"
            self.content_buffer.append(link_text)
            
            logger.info(f"      ✅ Buffered link: {text}")
            return True
            
        except Exception as e:
            logger.error(f"❌ insert_link failed: {e}")
            return False
    
    def finalize(self):
        """
        모든 버퍼 내용을 실제로 붙여넣기
        - 중요: 이미지 업로드 전에 호출해야 함!
        """
        logger.info("📤 Finalizing content (flushing buffer)...")
        return self._flush_buffer()
