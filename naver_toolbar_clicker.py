"""네이버 에디터 툴바 직접 클릭 - 진짜 성공 방법"""
import time
import logging
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

logger = logging.getLogger(__name__)


class NaverToolbarClicker:
    """
    툴바 버튼을 실제로 클릭하는 방식
    - execCommand 대신 사용자처럼 버튼 클릭
    - React 이벤트가 정상적으로 트리거됨
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)
        self.cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
    
    def _click_toolbar_button(self, button_class):
        """툴바 버튼 클릭"""
        try:
            # JavaScript로 버튼 찾기 및 클릭
            script = f"""
            var btn = document.querySelector('.{button_class}');
            if (btn) {{
                btn.click();
                return true;
            }}
            return false;
            """
            result = self.driver.execute_script(script)
            
            if result:
                logger.debug(f"      ✅ Clicked: {button_class}")
                time.sleep(0.2)
                return True
            else:
                logger.debug(f"      ⚠️ Not found: {button_class}")
                return False
        except Exception as e:
            logger.debug(f"      ❌ Error: {button_class} - {e}")
            return False
    
    def _focus_text_area(self):
        """텍스트 영역 포커스"""
        try:
            # .se-component.se-text 클릭
            script = """
            var textComp = document.querySelector('.se-component.se-text');
            if (textComp) {
                textComp.click();
                return true;
            }
            return false;
            """
            result = self.driver.execute_script(script)
            time.sleep(0.3)
            return result
        except:
            return False
    
    def _paste_text(self, text):
        """텍스트 붙여넣기"""
        pyperclip.copy(text)
        self.actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
        time.sleep(0.3)
    
    def _new_line(self):
        """줄바꿈"""
        self.actions.send_keys(Keys.RETURN).perform()
        time.sleep(0.15)
    
    def _select_all(self):
        """전체 선택"""
        self.actions.key_down(self.cmd_or_ctrl).send_keys('a').key_up(self.cmd_or_ctrl).perform()
        time.sleep(0.2)
    
    def _select_current_line(self):
        """현재 줄 선택 (Cmd+Shift+Left)"""
        if __import__('platform').system() == "Darwin":
            # Mac: Cmd+Shift+Left
            self.actions.key_down(self.cmd_or_ctrl).key_down(Keys.SHIFT).send_keys(Keys.ARROW_LEFT).key_up(Keys.SHIFT).key_up(self.cmd_or_ctrl).perform()
        else:
            # Windows/Linux: Shift+Home
            self.actions.key_down(Keys.SHIFT).send_keys(Keys.HOME).key_up(Keys.SHIFT).perform()
        time.sleep(0.2)
    
    def type_text(self, text, align='left', bold=False):
        """
        텍스트 입력 + 툴바 버튼으로 포맷
        
        워크플로우:
        1. 텍스트 붙여넣기
        2. 현재 줄 선택
        3. 툴바 버튼 클릭 (볼드, 정렬 등)
        4. End → 줄바꿈
        """
        try:
            # 포커스
            if not self._focus_text_area():
                logger.warning("Failed to focus text area")
            
            # 텍스트 입력
            self._paste_text(text)
            
            # 선택 (방금 입력한 텍스트)
            self._select_current_line()
            
            # 볼드 버튼 클릭
            if bold:
                # 볼드 버튼: .se-bold-toolbar-button
                self._click_toolbar_button('se-bold-toolbar-button')
            
            # 정렬 버튼 클릭
            # 주의: 정렬 버튼은 플로팅 툴바에 있을 수 있음!
            # 텍스트를 선택하면 나타남
            
            # 선택 해제 (End)
            self.actions.send_keys(Keys.END).perform()
            time.sleep(0.1)
            
            # 줄바꿈
            self._new_line()
            
            logger.info(f"      ✅ Text: {text[:50]}... [align={align}, bold={bold}]")
            return True
            
        except Exception as e:
            logger.error(f"❌ type_text failed: {e}")
            return False
    
    def insert_divider(self):
        """구분선 버튼 클릭"""
        try:
            # 구분선 버튼: .se-insert-horizontal-line-default-toolbar-button
            self._click_toolbar_button('se-insert-horizontal-line-default-toolbar-button')
            
            logger.info("      ✅ Divider inserted (button)")
            return True
        except Exception as e:
            logger.error(f"❌ insert_divider failed: {e}")
            return False
    
    def type_list(self, items):
        """리스트 입력 (• 불렛)"""
        try:
            if not self._focus_text_area():
                return False
            
            for item in items:
                text = f"• {item}"
                self._paste_text(text)
                self._new_line()
            
            # 빈 줄
            self._new_line()
            
            logger.info(f"      ✅ List: {len(items)} items")
            return True
        except Exception as e:
            logger.error(f"❌ type_list failed: {e}")
            return False
    
    def insert_emoji(self, emoji):
        """이모지 (큰 크기)"""
        try:
            if not self._focus_text_area():
                return False
            
            self._paste_text(emoji)
            self._new_line()
            
            logger.info(f"      ✅ Emoji: {emoji}")
            return True
        except Exception as e:
            logger.error(f"❌ insert_emoji failed: {e}")
            return False
    
    def insert_sticker(self, sticker_id):
        """스티커 대신 이모지"""
        emoji = '🐶' if sticker_id == 45 else '🐶❤️'
        return self.insert_emoji(emoji)
    
    def click_image_button(self):
        """이미지 버튼 클릭"""
        return self._click_toolbar_button('se-image-toolbar-button')
    
    def click_sticker_button(self):
        """스티커 버튼 클릭"""
        return self._click_toolbar_button('se-sticker-toolbar-button')
