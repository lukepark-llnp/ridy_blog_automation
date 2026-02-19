"""네이버 에디터 execCommand 포맷터 v2 - 메뉴얼 기반 완전 구현"""
import time
import logging
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

logger = logging.getLogger(__name__)


class NaverExecCommandFormatterV2:
    """
    메뉴얼 기반 완전 구현
    - div[contenteditable="true"] 사용
    - document.execCommand() 활용
    - 텍스트 선택 → 포맷 적용 워크플로우
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)
        self.cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
    
    def _get_editable_div(self):
        """contenteditable DIV 찾기"""
        try:
            return self.driver.find_element(By.CSS_SELECTOR, 'div[contenteditable="true"]')
        except:
            logger.error("❌ contenteditable div not found!")
            return None
    
    def _focus_editor(self):
        """에디터에 포커스"""
        # contenteditable div는 직접 클릭 불가 (not interactable)
        # 대신 부모 컨테이너 (.se-component.se-text) 클릭
        try:
            text_comp = self.driver.find_element(By.CSS_SELECTOR, '.se-component.se-text')
            text_comp.click()
            time.sleep(0.3)
            
            # JavaScript로 직접 포커스 (fallback)
            editable = self._get_editable_div()
            if editable:
                self.driver.execute_script("arguments[0].focus();", editable)
                time.sleep(0.2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to focus editor: {e}")
            return False
    
    def _select_last_text(self, length):
        """방금 입력한 텍스트 선택 (Shift + Left Arrow)"""
        for _ in range(min(length, 500)):  # 최대 500자
            self.actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_LEFT).key_up(Keys.SHIFT).perform()
        time.sleep(0.1)
    
    def _deselect(self):
        """선택 해제 (End 키)"""
        self.actions.send_keys(Keys.END).perform()
        time.sleep(0.05)
    
    def _new_line(self):
        """줄바꿈"""
        self.actions.send_keys(Keys.RETURN).perform()
        time.sleep(0.1)
    
    def type_text(self, text, align='left', bold=False):
        """
        텍스트 입력 + 포맷 적용
        
        워크플로우:
        1. 포커스
        2. 텍스트 붙여넣기 (pyperclip)
        3. 텍스트 선택 (Shift + Left)
        4. 포맷 적용 (execCommand)
        5. 선택 해제 (End)
        6. 줄바꿈 (Enter)
        
        Args:
            text: 텍스트 내용
            align: 'left' | 'center' | 'right'
            bold: True | False
        """
        try:
            # 1. 포커스
            if not self._focus_editor():
                logger.error("Failed to focus editor")
                return False
            
            # 2. 텍스트 붙여넣기
            pyperclip.copy(text)
            self.actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
            time.sleep(0.3)
            
            # 3. 텍스트 선택
            self._select_last_text(len(text))
            
            # 4. 포맷 적용
            if bold:
                self.driver.execute_script("document.execCommand('bold');")
                time.sleep(0.1)
                logger.debug("      → Bold applied")
            
            if align == 'center':
                self.driver.execute_script("document.execCommand('justifyCenter');")
                time.sleep(0.1)
                logger.debug("      → Center align applied")
            elif align == 'right':
                self.driver.execute_script("document.execCommand('justifyRight');")
                time.sleep(0.1)
                logger.debug("      → Right align applied")
            
            # 5. 선택 해제
            self._deselect()
            
            # 6. 줄바꿈
            self._new_line()
            
            logger.info(f"      ✅ Text: {text[:50]}... [align={align}, bold={bold}]")
            return True
            
        except Exception as e:
            logger.error(f"❌ type_text failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def insert_divider(self):
        """구분선 삽입 (─ 문자 30개, 가운데 정렬)"""
        try:
            divider_text = "─" * 30
            return self.type_text(divider_text, align='center', bold=False)
        except Exception as e:
            logger.error(f"❌ insert_divider failed: {e}")
            return False
    
    def type_list(self, items):
        """
        리스트 입력 (• 불렛)
        
        Note: 각 항목은 plain text로 입력 (불렛 포함)
        """
        try:
            if not self._focus_editor():
                return False
            
            for item in items:
                text = f"• {item}"
                
                # 붙여넣기
                pyperclip.copy(text)
                self.actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
                time.sleep(0.2)
                
                # 줄바꿈
                self._new_line()
            
            # 빈 줄 추가
            self._new_line()
            
            logger.info(f"      ✅ List: {len(items)} items")
            return True
            
        except Exception as e:
            logger.error(f"❌ type_list failed: {e}")
            return False
    
    def insert_emoji(self, emoji, align='center'):
        """
        이모지 삽입 (큰 크기)
        
        Note: 폰트 크기는 execCommand('fontSize')로 조절
        """
        try:
            if not self._focus_editor():
                return False
            
            # 이모지 붙여넣기
            pyperclip.copy(emoji)
            self.actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
            time.sleep(0.2)
            
            # 선택
            self._select_last_text(len(emoji))
            
            # 가운데 정렬
            if align == 'center':
                self.driver.execute_script("document.execCommand('justifyCenter');")
                time.sleep(0.1)
            
            # 폰트 크기 (7 = 가장 큼)
            self.driver.execute_script("document.execCommand('fontSize', false, '7');")
            time.sleep(0.1)
            
            # 선택 해제 + 줄바꿈
            self._deselect()
            self._new_line()
            
            logger.info(f"      ✅ Emoji: {emoji} (large, {align})")
            return True
            
        except Exception as e:
            logger.error(f"❌ insert_emoji failed: {e}")
            return False
    
    def insert_sticker(self, sticker_id):
        """스티커 대신 이모지 사용"""
        emoji = '🐶' if sticker_id == 45 else '🐶❤️'
        return self.insert_emoji(emoji, align='center')
    
    def insert_link(self, url, text=None):
        """
        링크 삽입
        
        워크플로우:
        1. 텍스트 입력
        2. 텍스트 선택
        3. execCommand('createLink')
        """
        try:
            if not self._focus_editor():
                return False
            
            link_text = text or url
            
            # 텍스트 입력
            pyperclip.copy(link_text)
            self.actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
            time.sleep(0.2)
            
            # 선택
            self._select_last_text(len(link_text))
            
            # 링크 생성
            self.driver.execute_script(f"document.execCommand('createLink', false, '{url}');")
            time.sleep(0.1)
            
            # 가운데 정렬
            self.driver.execute_script("document.execCommand('justifyCenter');")
            time.sleep(0.1)
            
            # 선택 해제 + 줄바꿈
            self._deselect()
            self._new_line()
            
            logger.info(f"      ✅ Link: {text or url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ insert_link failed: {e}")
            return False
    
    def apply_color(self, text, color='#4a90e2', bg_color=None):
        """
        색상 텍스트
        
        Args:
            text: 텍스트
            color: 텍스트 색 (hex)
            bg_color: 배경색 (hex, optional)
        """
        try:
            if not self._focus_editor():
                return False
            
            # 텍스트 입력
            pyperclip.copy(text)
            self.actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
            time.sleep(0.2)
            
            # 선택
            self._select_last_text(len(text))
            
            # 텍스트 색
            if color:
                self.driver.execute_script(f"document.execCommand('foreColor', false, '{color}');")
                time.sleep(0.1)
            
            # 배경색
            if bg_color:
                self.driver.execute_script(f"document.execCommand('backColor', false, '{bg_color}');")
                time.sleep(0.1)
            
            # 선택 해제 + 줄바꿈
            self._deselect()
            self._new_line()
            
            logger.info(f"      ✅ Colored text: {text[:30]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ apply_color failed: {e}")
            return False
