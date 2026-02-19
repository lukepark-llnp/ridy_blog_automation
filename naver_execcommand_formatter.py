"""네이버 에디터 execCommand 기반 포맷터"""
import time
import logging
import html

logger = logging.getLogger(__name__)


class NaverExecCommandFormatter:
    """
    document.execCommand('insertHTML') 사용한 직접 포맷팅
    - 이미 포맷된 HTML을 직접 삽입
    - 선택/포맷/선택해제 과정 없이 한 번에 처리
    """
    
    def __init__(self, driver):
        self.driver = driver
        
    def _insert_html(self, html_content):
        """HTML 직접 삽입"""
        try:
            # HTML escape 방지를 위해 JSON.stringify 사용
            script = f"""
            var htmlContent = {repr(html_content)};
            document.execCommand('insertHTML', false, htmlContent);
            """
            self.driver.execute_script(script)
            time.sleep(0.15)
            return True
        except Exception as e:
            logger.warning(f"    ⚠️ insertHTML failed: {e}")
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
            safe_text = html.escape(text).replace('\n', '<br>')
            
            # 태그 생성
            if bold:
                safe_text = f"<strong>{safe_text}</strong>"
            
            # 정렬 스타일
            if align == 'center':
                html_content = f'<p style="text-align: center;">{safe_text}</p>'
            elif align == 'right':
                html_content = f'<p style="text-align: right;">{safe_text}</p>'
            else:
                html_content = f'<p>{safe_text}</p>'
            
            # 삽입
            self._insert_html(html_content)
            
            logger.info(f"      ✅ Text inserted: {text[:50]}... [align={align}, bold={bold}]")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ type_text failed: {e}")
            return False
    
    def insert_divider(self):
        """구분선 삽입"""
        try:
            # HR 태그 또는 ─ 문자
            divider_html = '<p style="text-align: center;">──────────────────────────────</p>'
            
            self._insert_html(divider_html)
            
            logger.info("      ✅ Divider inserted")
            return True
        except Exception as e:
            logger.error(f"    ❌ insert_divider failed: {e}")
            return False
    
    def type_list(self, items):
        """리스트 입력 (• 불렛)"""
        try:
            # UL/LI 태그 사용
            list_html = "<ul>"
            for item in items:
                safe_item = html.escape(item)
                list_html += f"<li>{safe_item}</li>"
            list_html += "</ul>"
            
            self._insert_html(list_html)
            
            logger.info(f"      ✅ List inserted ({len(items)} items)")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ type_list failed: {e}")
            return False
    
    def insert_sticker(self, sticker_id):
        """스티커 대신 큰 이모지 (가운데 정렬)"""
        try:
            emoji = '🐶' if sticker_id == 45 else '🐶❤️'
            
            # 가운데 정렬 + 큰 폰트
            emoji_html = f'<p style="text-align: center; font-size: 32px;">{emoji}</p>'
            
            self._insert_html(emoji_html)
            
            logger.info(f"      ✅ Emoji inserted: {emoji}")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ insert_sticker failed: {e}")
            return False
    
    def insert_paragraph(self, text, align='left', bold=False, font_size=None):
        """
        일반 단락 삽입 (더 많은 옵션)
        
        Args:
            text: 텍스트
            align: 'left' | 'center' | 'right'
            bold: 볼드 여부
            font_size: 폰트 크기 (예: '18px', '24px')
        """
        try:
            safe_text = html.escape(text).replace('\n', '<br>')
            
            if bold:
                safe_text = f"<strong>{safe_text}</strong>"
            
            # 스타일 빌드
            styles = []
            if align != 'left':
                styles.append(f"text-align: {align}")
            if font_size:
                styles.append(f"font-size: {font_size}")
            
            style_attr = f' style="{"; ".join(styles)}"' if styles else ''
            
            html_content = f'<p{style_attr}>{safe_text}</p>'
            
            self._insert_html(html_content)
            
            logger.info(f"      ✅ Paragraph inserted: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ insert_paragraph failed: {e}")
            return False
