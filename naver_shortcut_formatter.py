"""네이버 에디터 키보드 단축키 기반 포맷터 (개선 버전)"""
import time
import logging
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

logger = logging.getLogger(__name__)


class NaverShortcutFormatter:
    """
    키보드 단축키를 사용한 안정적인 포맷팅
    - 텍스트 입력 → 전체 선택 → 포맷 적용 → 선택 해제
    - execCommand나 DOM 조작 없이 사용자처럼 동작
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
        
    def type_text(self, text, align='left', bold=False):
        """
        텍스트 입력 + 포맷 적용
        
        전략:
        1. 텍스트 붙여넣기 (Cmd+V)
        2. 현재 줄/문단 전체 선택 (Cmd+Shift+Up 또는 여러 번 Shift+Up)
        3. 포맷 적용 (Cmd+B, Cmd+E 등)
        4. End 키로 선택 해제
        5. Enter로 다음 줄
        
        Args:
            text: 텍스트 내용
            align: 'left' | 'center' | 'right'
            bold: True | False
        """
        try:
            actions = ActionChains(self.driver)
            
            # 1. 텍스트 붙여넣기
            pyperclip.copy(text)
            actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
            time.sleep(0.3)
            
            # 2. 현재 줄 전체 선택
            #    전략: Cmd+A를 사용하면 전체 문서가 선택되므로,
            #    대신 Shift+Home으로 줄 시작까지 선택 (Mac: Cmd+Shift+Left)
            if __import__('platform').system() == "Darwin":
                # Mac: Cmd+Shift+Left (줄 시작까지 선택)
                actions.key_down(self.cmd_or_ctrl).key_down(Keys.SHIFT).send_keys(Keys.ARROW_LEFT).key_up(Keys.SHIFT).key_up(self.cmd_or_ctrl).perform()
            else:
                # Windows/Linux: Shift+Home
                actions.key_down(Keys.SHIFT).send_keys(Keys.HOME).key_up(Keys.SHIFT).perform()
            
            time.sleep(0.2)
            
            # 3. 포맷 적용
            if bold:
                actions.key_down(self.cmd_or_ctrl).send_keys('b').key_up(self.cmd_or_ctrl).perform()
                time.sleep(0.2)
                logger.info("      → Bold applied")
            
            if align == 'center':
                actions.key_down(self.cmd_or_ctrl).send_keys('e').key_up(self.cmd_or_ctrl).perform()
                time.sleep(0.2)
                logger.info("      → Center align applied")
            elif align == 'right':
                actions.key_down(self.cmd_or_ctrl).send_keys('r').key_up(self.cmd_or_ctrl).perform()
                time.sleep(0.2)
                logger.info("      → Right align applied")
            
            # 4. 선택 해제 (End 키로 커서 맨 뒤로)
            actions.send_keys(Keys.END).perform()
            time.sleep(0.1)
            
            # 5. 줄바꿈
            actions.send_keys(Keys.RETURN).perform()
            time.sleep(0.2)
            
            logger.info(f"      ✅ Text: {text[:50]}... [align={align}, bold={bold}]")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ type_text failed: {e}")
            return False
    
    def insert_divider(self):
        """구분선 삽입"""
        try:
            divider_text = "──────────────────────────────"
            
            # 가운데 정렬으로 입력
            self.type_text(divider_text, align='center', bold=False)
            
            logger.info("      ✅ Divider inserted")
            return True
        except Exception as e:
            logger.error(f"    ❌ insert_divider failed: {e}")
            return False
    
    def type_list(self, items):
        """리스트 입력 (• 불렛)"""
        try:
            actions = ActionChains(self.driver)
            
            for item in items:
                text = f"• {item}"
                
                # 왼쪽 정렬으로 입력 (리스트는 보통 왼쪽)
                pyperclip.copy(text)
                actions.key_down(self.cmd_or_ctrl).send_keys('v').key_up(self.cmd_or_ctrl).perform()
                time.sleep(0.2)
                
                actions.send_keys(Keys.RETURN).perform()
                time.sleep(0.15)
            
            # 빈 줄
            actions.send_keys(Keys.RETURN).perform()
            time.sleep(0.2)
            
            logger.info(f"      ✅ List ({len(items)} items)")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ type_list failed: {e}")
            return False
    
    def insert_sticker(self, sticker_id):
        """스티커 대신 큰 이모지 (가운데 정렬)"""
        try:
            emoji = '🐶' if sticker_id == 45 else '🐶❤️'
            
            # 가운데 정렬으로 입력
            self.type_text(emoji, align='center', bold=False)
            
            logger.info(f"      ✅ Emoji: {emoji}")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ insert_sticker failed: {e}")
            return False
