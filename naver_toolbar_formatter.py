"""네이버 에디터 툴바 활용 포맷터"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip

logger = logging.getLogger(__name__)


class NaverToolbarFormatter:
    """
    네이버 스마트에디터 툴바를 사용한 포맷팅
    
    샘플 구조 재현:
    - 가운데 정렬
    - 볼드
    - 구분선
    - 리스트 (불렛)
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)
        
    def click_toolbar_button(self, button_text=None, button_class=None, button_aria=None):
        """툴바 버튼 클릭"""
        try:
            if button_aria:
                # aria-label로 찾기
                btn = self.driver.find_element(By.CSS_SELECTOR, f"button[aria-label*='{button_aria}']")
                btn.click()
                return True
            elif button_class:
                # class로 찾기
                btn = self.driver.find_element(By.CLASS_NAME, button_class)
                btn.click()
                return True
            elif button_text:
                # 텍스트로 찾기
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if button_text in btn.text:
                        btn.click()
                        return True
            return False
        except Exception as e:
            logger.warning(f"    ⚠️ Toolbar button not found: {e}")
            return False
    
    def set_align_center(self):
        """가운데 정렬 (키보드 단축키 사용)"""
        # Cmd+E (Mac) 또는 Ctrl+E (Windows)
        cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
        
        self.actions.key_down(cmd_or_ctrl).send_keys('e').key_up(cmd_or_ctrl).perform()
        time.sleep(0.2)
        
        logger.info("      ✅ Align center (Cmd+E)")
        return True
    
    def set_bold(self):
        """볼드 (키보드 단축키 사용)"""
        # Cmd+B (Mac) 또는 Ctrl+B (Windows)
        cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
        
        self.actions.key_down(cmd_or_ctrl).send_keys('b').key_up(cmd_or_ctrl).perform()
        time.sleep(0.2)
        
        logger.info("      ✅ Bold (Cmd+B)")
        return True
    
    def insert_divider(self):
        """구분선 삽입 (텍스트로 대체)"""
        # 구분선 문자 (유니코드)
        divider_text = "─" * 30
        
        # 가운데 정렬
        cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
        self.actions.key_down(cmd_or_ctrl).send_keys('e').key_up(cmd_or_ctrl).perform()
        time.sleep(0.2)
        
        # 구분선 타이핑
        pyperclip.copy(divider_text)
        self.actions.key_down(cmd_or_ctrl).send_keys('v').key_up(cmd_or_ctrl).perform()
        time.sleep(0.2)
        
        # Enter
        self.actions.send_keys(Keys.RETURN).perform()
        time.sleep(0.2)
        
        # 왼쪽 정렬로 복귀
        self.actions.key_down(cmd_or_ctrl).send_keys('l').key_up(cmd_or_ctrl).perform()
        time.sleep(0.2)
        
        logger.info("      ✅ Divider inserted (text)")
        return True
    
    def type_text(self, text, align='left', bold=False, size='normal'):
        """
        텍스트 타이핑 (포맷 적용)
        
        Args:
            text: 텍스트 내용
            align: 'left' | 'center' | 'right'
            bold: True | False
            size: 'normal' | 'large' | 'xlarge'
        """
        cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
        
        # 1. 정렬 설정
        if align == 'center':
            self.actions.key_down(cmd_or_ctrl).send_keys('e').key_up(cmd_or_ctrl).perform()
            time.sleep(0.1)
        elif align == 'right':
            self.actions.key_down(cmd_or_ctrl).send_keys('r').key_up(cmd_or_ctrl).perform()
            time.sleep(0.1)
        # left는 기본값이므로 생략
        
        # 2. 볼드 설정
        if bold:
            self.actions.key_down(cmd_or_ctrl).send_keys('b').key_up(cmd_or_ctrl).perform()
            time.sleep(0.1)
        
        # 3. 텍스트 입력 (pyperclip 사용)
        pyperclip.copy(text)
        self.actions.key_down(cmd_or_ctrl).send_keys('v').key_up(cmd_or_ctrl).perform()
        time.sleep(0.2)
        
        # 4. Enter로 줄바꿈
        self.actions.send_keys(Keys.RETURN).perform()
        time.sleep(0.1)
        
        # 5. 포맷 초기화 (다음 줄에 영향 안 가도록)
        if bold:
            self.actions.key_down(cmd_or_ctrl).send_keys('b').key_up(cmd_or_ctrl).perform()
            time.sleep(0.1)
        
        if align != 'left':
            self.actions.key_down(cmd_or_ctrl).send_keys('l').key_up(cmd_or_ctrl).perform()
            time.sleep(0.1)
        
        logger.info(f"      ✅ Text typed: {text[:50]} [align={align}, bold={bold}]")
    
    def type_list(self, items):
        """리스트 타이핑 (• 불렛)"""
        for item in items:
            # • 불렛 + 텍스트
            text = f"• {item}"
            pyperclip.copy(text)
            
            cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
            self.actions.key_down(cmd_or_ctrl).send_keys('v').key_up(cmd_or_ctrl).perform()
            time.sleep(0.2)
            
            self.actions.send_keys(Keys.RETURN).perform()
            time.sleep(0.1)
        
        # 빈 줄
        self.actions.send_keys(Keys.RETURN).perform()
        time.sleep(0.2)
        
        logger.info(f"      ✅ List typed ({len(items)} items)")
    
    def insert_sticker(self, sticker_id):
        """
        스티커 삽입 (네이버 스티커 버튼 클릭)
        
        TODO: 스티커 패널 열고 선택하는 로직 필요
        일단 fallback으로 큰 이모지 타이핑
        """
        # Fallback: 큰 이모지
        emoji = '🐶' if sticker_id == 45 else '🐶❤️'
        
        # 가운데 정렬
        self.set_align_center()
        
        # 이모지 타이핑 (크게 보이도록 여러 번)
        pyperclip.copy(emoji)
        
        cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
        self.actions.key_down(cmd_or_ctrl).send_keys('v').key_up(cmd_or_ctrl).perform()
        time.sleep(0.3)
        
        self.actions.send_keys(Keys.RETURN).perform()
        time.sleep(0.2)
        
        logger.info(f"      ✅ Sticker/Emoji inserted: {emoji}")
