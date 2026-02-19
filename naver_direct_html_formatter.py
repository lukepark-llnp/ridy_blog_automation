"""네이버 에디터 직접 HTML 삽입 포맷터"""
import time
import logging
import html

logger = logging.getLogger(__name__)


class NaverDirectHTMLFormatter:
    """
    document.querySelector로 에디터 영역 찾아서 직접 innerHTML 삽입
    - 가장 확실한 방법
    - 포맷팅이 이미 적용된 HTML을 한 번에 삽입
    """
    
    def __init__(self, driver):
        self.driver = driver
        
    def _get_editor_element(self):
        """에디터 contenteditable 영역 찾기"""
        script = """
        // 네이버 스마트에디터의 contenteditable 영역 찾기
        var editor = document.querySelector('.se-main-container .se-component.se-text.__se-component');
        if (!editor) {
            editor = document.querySelector('[contenteditable="true"]');
        }
        return editor;
        """
        return self.driver.execute_script(script)
    
    def insert_html_batch(self, html_content: str):
        """HTML 콘텐츠를 한 번에 삽입"""
        try:
            script = f"""
            var editor = document.querySelector('.se-main-container');
            if (!editor) {{
                return false;
            }}
            
            // HTML 삽입
            var htmlContent = {repr(html_content)};
            editor.innerHTML += htmlContent;
            
            return true;
            """
            
            result = self.driver.execute_script(script)
            
            if result:
                logger.info("  ✅ HTML inserted successfully")
                return True
            else:
                logger.warning("  ⚠️ Editor not found")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ HTML insertion failed: {e}")
            return False
    
    def format_content_elements(self, elements: list) -> str:
        """
        DOM elements를 HTML string으로 변환
        
        Args:
            elements: DOM builder v2의 elements 리스트
        
        Returns:
            HTML string (네이버 에디터 형식)
        """
        html_parts = []
        
        for elem in elements:
            elem_type = elem.get('type')
            
            if elem_type == 'text':
                # 텍스트
                content = html.escape(elem.get('content', ''))
                align = elem.get('align', 'left')
                bold = elem.get('bold', False)
                
                # 스타일 빌드
                styles = []
                if align == 'center':
                    styles.append('text-align: center')
                elif align == 'right':
                    styles.append('text-align: right')
                
                style_attr = f' style="{"; ".join(styles)}"' if styles else ''
                
                # 태그
                if bold:
                    content = f'<strong>{content}</strong>'
                
                html_parts.append(f'<p{style_attr}>{content}</p>')
            
            elif elem_type == 'sticker':
                # 이모지 (스티커 대신)
                sticker_id = elem.get('sticker_id', 45)
                emoji = '🐶' if sticker_id == 45 else '🐶❤️'
                
                html_parts.append(
                    f'<p style="text-align: center; font-size: 48px;">{emoji}</p>'
                )
            
            elif elem_type == 'divider':
                # 구분선
                html_parts.append(
                    '<p style="text-align: center;">──────────────────────────────</p>'
                )
            
            elif elem_type == 'list':
                # 리스트
                items = elem.get('items', [])
                list_html = '<ul style="list-style: none; padding-left: 0;">'
                for item in items:
                    safe_item = html.escape(str(item))
                    list_html += f'<li style="margin: 8px 0;">• {safe_item}</li>'
                list_html += '</ul>'
                html_parts.append(list_html)
            
            elif elem_type == 'link':
                # 링크
                url = elem.get('url', '')
                text = html.escape(elem.get('text', url))
                html_parts.append(
                    f'<p style="text-align: center;"><a href="{url}" style="color: #4a90e2; text-decoration: none;">{text}</a></p>'
                )
            
            elif elem_type == 'image_placeholder':
                # 이미지는 나중에 별도 업로드
                pass
        
        return '\n'.join(html_parts)
    
    def type_text(self, text, align='left', bold=False):
        """단일 텍스트 요소 삽입 (호환성)"""
        elem = {
            'type': 'text',
            'content': text,
            'align': align,
            'bold': bold
        }
        html_content = self.format_content_elements([elem])
        return self.insert_html_batch(html_content)
    
    def insert_divider(self):
        """구분선 삽입"""
        elem = {'type': 'divider'}
        html_content = self.format_content_elements([elem])
        return self.insert_html_batch(html_content)
    
    def type_list(self, items):
        """리스트 삽입"""
        elem = {
            'type': 'list',
            'items': items
        }
        html_content = self.format_content_elements([elem])
        return self.insert_html_batch(html_content)
    
    def insert_sticker(self, sticker_id):
        """이모지 삽입"""
        elem = {
            'type': 'sticker',
            'sticker_id': sticker_id
        }
        html_content = self.format_content_elements([elem])
        return self.insert_html_batch(html_content)
