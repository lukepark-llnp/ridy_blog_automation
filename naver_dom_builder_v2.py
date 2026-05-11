"""네이버 블로그 DOM 빌더 v2 - 샘플 구조 정확히 재현"""
import logging
from bs4 import BeautifulSoup
from pathlib import Path

logger = logging.getLogger(__name__)


class NaverDOMBuilderV2:
    """
    샘플 구조 100% 재현
    
    정렬, 볼드, 구분선, 리스트 모두 정확히 구현
    이모지는 텍스트 (나중에 이미지로 교체)
    """
    
    def __init__(self, html_content: str, data: dict):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.data = data
        self.elements = []
        
    def build(self) -> list[dict]:
        """
        샘플 순서:
        1. 인사 (가운데)
        2. 이모지 (가운데, 큼)
        3. 구분선
        4. 차량 소개 (가운데)
        5. [이미지 2x2] - placeholder
        6. 차량 정보 리스트 (왼쪽, •)
        7. 구분선
        8. 감사 인사 (가운데)
        9. 이모지 하트 (가운데)
        10. [이미지 2x3] - placeholder
        11. 구분선
        12. "장착 옵션" (가운데, 볼드)
        13. 옵션 리스트 (왼쪽, •)
        14. 구분선
        15. "추가 장착 옵션" (가운데, 볼드) - if exists
        16. 추가 옵션 리스트
        17. "문의 안내" (가운데)
        18. 구분선
        19. [이미지 2x2] - placeholder (옵션 상세)
        20. 구분선
        21. [푸터 이미지] - publisher가 추가
        22. [RIDY 로고] - publisher가 추가
        23. 연락처 (가운데)
        24. 카톡 링크들 (가운데, 파란색)
        25. 해시태그 (작게, 회색)
        """
        
        # 1. 인사말 (가운데)
        greeting = self._extract_greeting()
        if greeting:
            self.elements.append({
                'type': 'text',
                'content': greeting,
                'align': 'center',
                'size': 'normal',
                'bold': False
            })
        
        # 2. 네이버 스티커 45번 (가운데)
        self.elements.append({
            'type': 'sticker',
            'sticker_id': 45,
            'align': 'center'
        })
        
        # 3. 구분선
        self.elements.append({'type': 'divider'})
        
        # 4. 차량 소개 (가운데)
        intro = self._extract_intro()
        if intro:
            self.elements.append({
                'type': 'text',
                'content': intro,
                'align': 'center',
                'size': 'normal',
                'bold': False
            })
        
        # 5. [이미지 2x2 placeholder]
        self.elements.append({
            'type': 'image_placeholder',
            'group': 1,
            'layout': '2x2',
            'count': 4
        })
        
        # 6. 차량 정보 리스트 (왼쪽)
        vehicle_info = self._extract_vehicle_info()
        if vehicle_info:
            self.elements.append({
                'type': 'list',
                'items': vehicle_info,
                'align': 'left',
                'bullet': '•'
            })
        
        # 7. 구분선
        self.elements.append({'type': 'divider'})
        
        # 8. 감사 인사 (가운데)
        thanks = self._extract_thanks()
        if thanks:
            self.elements.append({
                'type': 'text',
                'content': thanks,
                'align': 'center',
                'size': 'normal',
                'bold': False
            })
        
        # 9. 네이버 스티커 46번 (가운데)
        self.elements.append({
            'type': 'sticker',
            'sticker_id': 46,
            'align': 'center'
        })
        
        # 10. [이미지 2x3 placeholder] - 옵션 상세 6장
        self.elements.append({
            'type': 'image_placeholder',
            'group': 2,
            'layout': '2x3',
            'count': 6
        })
        
        # 11. 구분선
        self.elements.append({'type': 'divider'})
        
        # 12. "장착 옵션" 헤더 (가운데, 볼드)
        self.elements.append({
            'type': 'text',
            'content': '장착 옵션',
            'align': 'center',
            'size': 'normal',
            'bold': True
        })
        
        # 13. 옵션 리스트
        options = self._extract_options()
        if options:
            self.elements.append({
                'type': 'list',
                'items': options,
                'align': 'left',
                'bullet': '•'
            })
        
        # 14. 구분선
        self.elements.append({'type': 'divider'})
        
        # 15-17. 추가 옵션 (있으면)
        extra_options = self._extract_extra_options()
        if extra_options:
            self.elements.append({
                'type': 'text',
                'content': '추가 장착 옵션',
                'align': 'center',
                'size': 'normal',
                'bold': True
            })
            
            self.elements.append({
                'type': 'list',
                'items': extra_options,
                'align': 'left',
                'bullet': '•'
            })
            
            # 문의 안내
            self.elements.append({
                'type': 'text',
                'content': '돈도 추가로 절약하는 옵션이 있으면 문의!',
                'align': 'center',
                'size': 'normal',
                'bold': False
            })
            
            # 구분선
            self.elements.append({'type': 'divider'})
        
        # 18. [이미지 2x2 placeholder] - 추가 옵션 상세
        self.elements.append({
            'type': 'image_placeholder',
            'group': 3,
            'layout': '2x2',
            'count': 4
        })
        
        # 19. 구분선
        self.elements.append({'type': 'divider'})
        
        # 20-21. 푸터 이미지 & 로고는 publisher가 직접 추가
        
        # 22. 연락처 (가운데)
        self.elements.append({
            'type': 'text',
            'content': '문의\n번호: 1555-6595',
            'align': 'center',
            'size': 'normal',
            'bold': False
        })

        # 23. 푸터 링크 (가운데, 파란색)
        footer_links = [
            ("카카오톡 채널", "https://pf.kakao.com/_xgxoxexen/chat"),
            ("RIDY 바로 가기", "https://www.ridy.co.kr/"),
            ("PAYOUT 바로 가기", "https://www.ridy.co.kr/service/payout"),
            ("서비스센터 가입 문의", "https://tally.so/r/mYLXOd"),
        ]

        for link_text, link_url in footer_links:
            self.elements.append({
                'type': 'link',
                'text': link_text,
                'url': link_url,
                'align': 'center',
                'color': 'blue'
            })
        
        # 24. 해시태그 (작게, 회색)
        tags = self._extract_tags()
        if tags:
            self.elements.append({
                'type': 'text',
                'content': ' '.join(f'#{tag}' for tag in tags),
                'align': 'left',
                'size': 'small',
                'bold': False,
                'color': 'gray'
            })
        
        return self.elements
    
    def _extract_greeting(self) -> str:
        """첫 인사말"""
        # HTML에서 첫 섹션의 첫 p 태그
        sections = self.soup.find_all('div', class_='section')
        if sections:
            first_p = sections[0].find('p')
            if first_p:
                lines = first_p.get_text(strip=True).split('\n')
                # 첫 줄만 (예: "안녕하세요~ RIDY입니다! 🏍️")
                return lines[0] if lines else ''
        return ''
    
    def _extract_intro(self) -> str:
        """차량 소개"""
        sections = self.soup.find_all('div', class_='section')
        if sections:
            first_p = sections[0].find('p')
            if first_p:
                lines = first_p.get_text(strip=True).split('\n')
                # 두 번째 줄부터 (차량명 소개)
                if len(lines) > 1:
                    return '\n'.join(lines[1:])
        return ''
    
    def _extract_vehicle_info(self) -> list[str]:
        """차량 정보 리스트 (data 딕셔너리 활용)"""
        # data 딕셔너리에 정보가 있으면 우선 사용
        if self.data and 'model_key' in self.data:
            from content_generator import content_gen
            return content_gen.generate_vehicle_info(self.data)
            
        # Fallback: HTML 파싱
        info_list = self.soup.find('ul', class_='info-list')
        if info_list:
            items = info_list.find_all('li')
            return [item.get_text(strip=True) for item in items]
        return []
    
    def _extract_thanks(self) -> str:
        """감사 인사"""
        for section in self.soup.find_all('div', class_='section'):
            text = section.get_text(strip=True)
            if 'RIDY' in text and ('감사' in text or '통해' in text):
                p = section.find('p')
                if p:
                    return p.get_text(strip=True)
        return ''
    
    def _extract_options(self) -> list[str]:
        """기본 옵션"""
        options_str = self.data.get('options', '')
        if options_str:
            return [opt.strip() for opt in options_str.replace(',', '\n').split('\n') if opt.strip()]
        return []
    
    def _extract_extra_options(self) -> list[str]:
        """추가 옵션"""
        extra_str = self.data.get('extra_options', '')
        if extra_str:
            return [opt.strip() for opt in extra_str.replace(',', '\n').split('\n') if opt.strip()]
        return []
    
    def _extract_tags(self) -> list[str]:
        """해시태그"""
        # HTML footer에서 추출
        footer = self.soup.find('div', class_='footer')
        if footer:
            tags_text = footer.get_text(strip=True)
            # #으로 시작하는 단어들
            import re
            tags = re.findall(r'#(\S+)', tags_text)
            return tags
        return []
    

def build_naver_dom_v2(html_content: str, data: dict) -> list[dict]:
    """
    v2: 샘플 구조 정확히 재현
    
    레퍼런스 복제 모드: data가 리스트이면 그대로 반환
    """
    # 레퍼런스 복제 모드: data가 리스트이면 구조화된 요소 리스트
    if isinstance(data, list):
        logger.info(f"  → Reference clone mode: {len(data)} elements")
        return data
    
    # 기존 로직: HTML 파싱
    builder = NaverDOMBuilderV2(html_content, data)
    return builder.build()
