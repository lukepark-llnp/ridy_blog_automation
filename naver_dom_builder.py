"""네이버 블로그 DOM 빌더 - HTML을 네이버 에디터 구조로 변환"""
import logging
from bs4 import BeautifulSoup
from pathlib import Path

logger = logging.getLogger(__name__)


class NaverDOMBuilder:
    """
    샘플 구조 그대로 재현
    
    순서:
    1. 큰 이모지 (가운데)
    2. 인사말 텍스트 (가운데, 작은 글씨)
    3. 구분선
    4. 이미지 2x2 (4장)
    5. 차량 정보 리스트
    6. 구분선
    7. 감사 인사 (가운데)
    8. 큰 이모지
    9. 이미지 2x3 (6장) - 옵션별
    10. 구분선
    11. 옵션 헤더 (가운데, 볼드)
    12. 옵션 리스트
    13. 구분선
    14. 추가 옵션 헤더
    15. 추가 옵션 리스트
    16. 안내 문구 (가운데)
    17. 구분선
    18. 이미지 2x2 (4장) - 추가
    19. 구분선
    20. 푸터 이미지 2개 (좌우)
    21. RIDY 로고
    22. 연락처 + 카톡 링크
    23. 해시태그
    """
    
    def __init__(self, html_content: str, data: dict):
        """
        Args:
            html_content: content_generator.py가 생성한 HTML
            data: 원본 입력 데이터
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.data = data
        self.elements = []
        
    def build(self) -> list[dict]:
        """
        네이버 에디터 삽입용 요소 리스트 반환
        
        Returns:
            [
                {'type': 'text', 'content': '...', 'align': 'center', 'bold': True},
                {'type': 'emoji', 'char': '🐶', 'size': 80},
                {'type': 'divider'},
                {'type': 'images', 'paths': [...], 'layout': '2x2'},
                ...
            ]
        """
        # 1. 큰 이모지 (샘플 참고)
        emoji = self._extract_emoji()
        if emoji:
            self.elements.append({
                'type': 'emoji',
                'char': emoji,
                'size': 80
            })
        
        # 2. 인사말 + 차량 소개
        greeting = self._extract_greeting()
        if greeting:
            self.elements.append({
                'type': 'text',
                'content': greeting,
                'align': 'center',
                'size': 'normal'
            })
        
        # 3. 구분선
        self.elements.append({'type': 'divider'})
        
        # 4. 첫 번째 이미지 그룹 (2x2)
        # NOTE: 이미지는 나중에 publisher가 추가
        self.elements.append({
            'type': 'image_placeholder',
            'group': 1,
            'layout': '2x2',
            'count': 4
        })
        
        # 5. 차량 정보
        vehicle_info = self._extract_vehicle_info()
        if vehicle_info:
            self.elements.append({
                'type': 'list',
                'items': vehicle_info,
                'align': 'left'
            })
        
        # 6. 구분선
        self.elements.append({'type': 'divider'})
        
        # 7. 감사 인사
        thanks = self._extract_thanks()
        if thanks:
            self.elements.append({
                'type': 'text',
                'content': thanks,
                'align': 'center',
                'size': 'normal'
            })
        
        # 8. 큰 이모지 (하트)
        self.elements.append({
            'type': 'emoji',
            'char': '🐶❤️',
            'size': 60
        })
        
        # 9. 두 번째 이미지 그룹 (2x3, 6장 - 있으면)
        self.elements.append({
            'type': 'image_placeholder',
            'group': 2,
            'layout': '2x3',
            'count': 6
        })
        
        # 10. 구분선
        self.elements.append({'type': 'divider'})
        
        # 11. 옵션 헤더
        self.elements.append({
            'type': 'text',
            'content': '장착 옵션',
            'align': 'center',
            'bold': True,
            'size': 'large'
        })
        
        # 12. 옵션 리스트
        options = self._extract_options()
        if options:
            self.elements.append({
                'type': 'list',
                'items': options,
                'align': 'left'
            })
        
        # 13. 구분선
        self.elements.append({'type': 'divider'})
        
        # 14. 추가 옵션 헤더
        extra_options = self._extract_extra_options()
        if extra_options:
            self.elements.append({
                'type': 'text',
                'content': '추가 장착 옵션',
                'align': 'center',
                'bold': True,
                'size': 'large'
            })
            
            # 15. 추가 옵션 리스트
            self.elements.append({
                'type': 'list',
                'items': extra_options,
                'align': 'left'
            })
        
        # 16. 안내 문구
        self.elements.append({
            'type': 'text',
            'content': '돈도 추가로 절약하는 옵션이 있으면 문의!',
            'align': 'center',
            'size': 'normal'
        })
        
        # 17. 구분선
        self.elements.append({'type': 'divider'})
        
        # 18. 세 번째 이미지 그룹 (2x2, 4장 - 옵션 상세)
        self.elements.append({
            'type': 'image_placeholder',
            'group': 3,
            'layout': '2x2',
            'count': 4
        })
        
        # 19. 구분선
        self.elements.append({'type': 'divider'})
        
        # 20-23. 푸터는 이미지로 처리 (별도 추가)
        
        return self.elements
    
    def _extract_emoji(self) -> str:
        """HTML에서 이모지 추출"""
        emoji_div = self.soup.find('div', class_='char-emoji')
        if emoji_div:
            return emoji_div.get_text(strip=True)
        return '🐶'
    
    def _extract_greeting(self) -> str:
        """인사말 + 차량 소개 추출"""
        # body 첫 번째 섹션의 p 태그들
        sections = self.soup.find_all('div', class_='section')
        if sections:
            first_section = sections[0]
            paragraphs = first_section.find_all('p')
            if paragraphs:
                return '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
        return ''
    
    def _extract_vehicle_info(self) -> list[str]:
        """차량 정보 리스트 추출"""
        info_list = self.soup.find('ul', class_='info-list')
        if info_list:
            items = info_list.find_all('li')
            return [item.get_text(strip=True) for item in items]
        return []
    
    def _extract_thanks(self) -> str:
        """감사 인사 추출"""
        # "RIDY RENTALS" 또는 "RIDY" 포함된 섹션
        for section in self.soup.find_all('div', class_='section'):
            text = section.get_text(strip=True)
            if 'RIDY' in text and ('감사' in text or '통해' in text):
                # p 태그만 추출
                p = section.find('p')
                if p:
                    return p.get_text(strip=True)
        return ''
    
    def _extract_options(self) -> list[str]:
        """기본 옵션 리스트 추출"""
        # data에서 직접 가져오기
        options_str = self.data.get('options', '')
        if options_str:
            # 쉼표 또는 줄바꿈으로 구분
            return [opt.strip() for opt in options_str.replace(',', '\n').split('\n') if opt.strip()]
        return []
    
    def _extract_extra_options(self) -> list[str]:
        """추가 옵션 리스트 추출"""
        extra_str = self.data.get('extra_options', '')
        if extra_str:
            return [opt.strip() for opt in extra_str.replace(',', '\n').split('\n') if opt.strip()]
        return []


def build_naver_dom(html_content: str, data: dict) -> list[dict]:
    """
    편의 함수: HTML → 네이버 DOM 요소 리스트
    
    Args:
        html_content: content_generator.py 결과
        data: 원본 입력 데이터
        
    Returns:
        네이버 에디터 삽입용 요소 리스트
    """
    builder = NaverDOMBuilder(html_content, data)
    return builder.build()
