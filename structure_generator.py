"""Structure Generator - Generate structured blog elements directly from data"""
import random
from config import settings
from models_db import get_model_info, get_model_display_name
from content_generator import content_gen

class StructureGenerator:
    """Generate structured blog elements (list of dicts) directly"""
    
    def generate_elements(self, data: dict, image_count: int = 10) -> list[dict]:
        """
        Build the exact structure used in test_reference_clone.py
        but with dynamic data and dynamic image indices.
        """
        elements = []
        
        # 인덱스 계산 (0-based)
        # 바이크 이미지: 0 ~ image_count-1
        # 이모지 1 (emoji_45): image_count
        # 이모지 2 (emoji_46): image_count + 1
        # 푸터 1: image_count + 2
        # 푸터 2: image_count + 3
        
        emoji1_idx = image_count
        emoji2_idx = image_count + 1
        footer1_idx = image_count + 2
        footer2_idx = image_count + 3
        
        # 바이크 이미지 분배 (최대 image_count)
        # 그룹 1: 0~3 (4장)
        # 그룹 2: 4~7 (4장)
        # 그룹 3: 8~ (나머지 전체)
        
        group1_indices = [i for i in range(0, min(4, image_count))]
        group2_indices = [i for i in range(4, min(8, image_count))] if image_count > 4 else []
        group3_indices = [i for i in range(8, image_count)] if image_count > 8 else []
        
        # 1. 인사말 (가운데, 폰트 19px)
        # LLM 사용: 특별 메시지가 있으면 인트로 확장
        base_intro = content_gen.generate_greeting_intro(data)
        if data.get('special_message'):
            intro_text = content_gen.generate_intro_with_special_message(data, base_intro)
        else:
            intro_text = base_intro
            
        elements.append({
            'type': 'text',
            'content': intro_text,
            'align': 'center',
            'size': 'large', # 폰트 크게
            'bold': False
        })
        
        # 2. 이모지 이미지 1 위치 (요청: 1, 2 위치 변경 -> 여기 emoji2 넣음)
        elements.append({
            'type': 'image_group',
            'count': 1,
            'indices': [emoji2_idx] # emoji_46 (순서 변경됨)
        })
        
        # 3. 구분선
        elements.append({'type': 'divider'})
        
        # 4. 차량 소개 (가운데, 폰트 19px)
        model_display = get_model_display_name(data.get('model_key', 'UNKNOWN'))
        elements.append({
            'type': 'text',
            'content': f"오늘은 {model_display} 출고 소식입니다!",
            'align': 'center',
            'size': 'large',
            'bold': False
        })
        
        # 5. [이미지 그룹 1] (최대 4장)
        if group1_indices:
            elements.append({
                'type': 'image_group',
                'count': len(group1_indices),
                'indices': group1_indices
            })
        
        # 6. 차량 정보 리스트 (가운데 정렬, 폰트 16px)
        vehicle_info = content_gen.generate_vehicle_info(data)
        elements.append({
            'type': 'list',
            'items': vehicle_info,
            'align': 'center',
            'bullet': '•'
        })
        
        # 7. 구분선
        elements.append({'type': 'divider'})
        
        # 8. 감사 인사 (문구 수정)
        thanks = content_gen.generate_thank_you().replace("RENTALS", "RENTAL")
        elements.append({
            'type': 'text',
            'content': f"RIDY RENTAL을 통해 리스 출고를 진행하신 라이더님\n{thanks}",
            'align': 'center',
            'size': 'large',
            'bold': False
        })
        
        # 9. 이모지 이미지 2 위치 (요청: 1, 2 위치 변경 -> 여기 emoji1 넣음)
        elements.append({
            'type': 'image_group',
            'count': 1,
            'indices': [emoji1_idx] # emoji_45 (순서 변경됨)
        })
        
        # 10. [이미지 그룹 2] (나머지 이미지 중 최대 4장)
        if group2_indices:
            elements.append({
                'type': 'image_group',
                'count': len(group2_indices),
                'indices': group2_indices
            })
        
        # 11. 구분선
        elements.append({'type': 'divider'})
        
        # 12. 장착 옵션 헤더 (폰트 24px, 볼드)
        elements.append({
            'type': 'text',
            'content': '장착 옵션',
            'align': 'center',
            'size': 'xlarge',
            'bold': True
        })
        
        # 13. 옵션 리스트
        options_str = data.get('options', '')
        if options_str:
            options = [opt.strip() for opt in options_str.split('\n') if opt.strip()]
            elements.append({
                'type': 'list',
                'items': options,
                'align': 'center'
            })
            
        # 14. 구분선
        elements.append({'type': 'divider'})
        
        # 14-1. [이미지 그룹 3] (나머지 이미지)
        if group3_indices:
            elements.append({
                'type': 'image_group',
                'count': len(group3_indices),
                'indices': group3_indices
            })
        
        # 15. 추가 옵션
        extra_str = data.get('extra_options', '')
        if extra_str:
            elements.append({
                'type': 'text',
                'content': '추가 장착 옵션',
                'align': 'center',
                'size': 'xlarge',
                'bold': True
            })
            
            # 멀티라인 처리
            extra_lines = [opt.strip() for opt in extra_str.split('\n') if opt.strip()]
            elements.append({
                'type': 'list',
                'items': extra_lines,
                'align': 'center'
            })
            
            elements.append({
                'type': 'text',
                'content': '등등 추가로 원하시는 옵션이 있으면 문의 주세요!',
                'align': 'center',
                'bold': False
            })
            
            elements.append({'type': 'divider'})
            
        # 16. 구분선 하나 더
        elements.append({'type': 'divider'})
        
        # 17. [푸터 이미지 그룹] (2장) - 동적 인덱스 적용
        # 보험설명사진, 혜택사진
        elements.append({
            'type': 'image_group',
            'count': 2,
            'indices': [footer1_idx, footer2_idx]
        })
        
        # 18. 문의 정보 (카카오톡 채널 텍스트 삭제 - 중복 방지)
        elements.append({
            'type': 'text',
            'content': f"문의\n번호: {settings.phone}", # 카카오톡 채널 삭제
            'align': 'center',
            'size': 'large',
            'bold': False
        })
        
        # 19. 링크
        links = [
            ("카카오톡 채널", settings.kakao_link_1),
            ("RIDY 바로 가기", "https://www.ridy.co.kr/"),
            ("PAY OUT 바로 가기", "https://www.ridy.co.kr/payout"),
            ("지사 도입 문의하기", "https://www.ridy.co.kr/inquiry#%EC%A7%80%EC%82%AC%EB%8F%84%EC%9E%85%EB%AC%B8%EC%9D%98%ED%95%98%EA%B8%B0")
        ]
        
        for text, url in links:
            elements.append({
                'type': 'link',
                'text': text,
                'url': url,
                'align': 'center',
                'color': 'blue'
            })
            
        return elements

structure_gen = StructureGenerator()
