"""LLM-based content generation with variation using Anthropic Claude 3 Haiku"""
import random
import logging
from anthropic import Anthropic
from config import settings
from models_db import get_model_info, get_model_display_name, get_korean_name_variations, get_seo_keywords

logger = logging.getLogger(__name__)


class ContentGenerator:
    """Generate varied blog content using Anthropic Claude 3 Haiku"""
    
    # Title patterns (8 variations - 영문/한글 혼용, 심플한 형식)
    # 룰: 모든 제목은 반드시 "출고"로 끝나야 한다.
    # 라이디 홈페이지(www.ridy.co.kr/story) 네이버 블로그 수집 로직이
    # `제목 마지막 == "출고"` 기준으로 출고 게시물을 인식하고, KST 09:00 윈도당 1건만 노출함.
    # 변형 추가 시에도 이 룰(끝이 "출고")을 반드시 지킬 것 — 어기면 도배 사고 재발.
    # 상세: ~/Ridy/www.ridy.co.kr/server.js의 isDeliveryPost() 정규식 /출고\s*$/
    TITLE_PATTERNS = [
        "{region} {district} 배달 오토바이 {model_eng} 출고",
        "{region} {district} {model_kor} {color} 출고",
        "{region} {district} | {model_eng} {color} 출고",
        "{region} {model_kor} {color} 신차 출고",
        "{district} {model_eng} {color} 바이크 리스 출고",
        "{region} {district} {color} {model_kor} 출고",
        "{region} {model_eng} {color} 출고",
        "{region} {district} {model_eng} {color} 신규 출고",
    ]
    
    # Greeting patterns (8 variations)
    GREETINGS = [
        "안녕하세요! 🐶",
        "안녕하세요 여러분! 😊",
        "안녕하세요~ RIDY입니다! 🏍️",
        "여러분 안녕하세요! ✨",
        "반갑습니다! 🐶",
        "안녕하세요 RIDY 가족 여러분! 💨",
        "좋은 하루 보내고 계신가요? 🌟",
        "안녕하세요 RIDY입니다!! 🐶",
    ]
    
    # Intro patterns (10 variations - 영문/한글 혼용)
    INTROS = [
        "오늘은 {model_eng}를 소개하겠습니다!",
        "오늘은 {model_kor} {color} 출고 소식을 전해드립니다!",
        "이번에는 {model_eng} ({model_kor})을 출고하게 되었습니다! 🎉",
        "{model_kor} {color} 출고 완료했습니다!",
        "오늘 소개할 차량은 {model_eng}입니다! ⚡",
        "{model_kor} 출고 완료! 자세한 내용 확인해보세요 👇",
        "{model_eng}, 일명 {model_kor} 출고 소식입니다! 💨",
        "이번 출고 모델은 {model_kor}({model_eng})입니다! ✨",
        "{model_eng} 출고했습니다! 국내에서는 {model_kor}로도 불리는 모델이죠 🏍️",
        "{model_kor} 출고 완료! {model_eng} 차량 자세히 보시죠 👀"
    ]
    
    # Thank you patterns (7 variations)
    THANKS = [
        "RIDY RENTAL을 통해 만족하셨던 소중한 말씀해주셔서 감사합니다 🐶❤️",
        "RIDY를 믿고 선택해주셔서 감사합니다! 💙",
        "소중한 출고 기회 주셔서 감사드립니다! 🙏",
        "RIDY와 함께해주셔서 진심으로 감사합니다! ✨",
        "고객님의 만족이 RIDY의 보람입니다! 감사합니다 🐶",
        "RIDY RENTAL을 선택해주셔서 감사합니다! 🏍️💨",
        "믿음과 신뢰에 감사드립니다! 🐶❤️",
    ]
    
    # Option intro patterns (5 variations)
    OPTION_INTROS = [
        "장착 옵션",
        "추가 장착 옵션",
        "이번 출고 장착 옵션",
        "고객님이 선택하신 장착 옵션",
        "이번 차량 장착 옵션 📋",
    ]
    
    # Extra option patterns (4 variations)
    EXTRA_OPTION_INTROS = [
        "등등 추가로 원하시는 옵션이 있으면 문의 주세요!!",
        "추가 옵션 문의는 언제든지 연락주세요! 💬",
        "궁금하신 추가 옵션은 편하게 문의해주세요!",
        "더 많은 옵션이 궁금하시다면 문의 주세요! 📞",
    ]
    
    def __init__(self):
        try:
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            self.model = settings.anthropic_model
            logger.info(f"✅ Anthropic initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic: {e}")
            self.client = None
    
    def generate_title(self, data: dict) -> str:
        """Generate varied title with Korean/English mix"""
        pattern = random.choice(self.TITLE_PATTERNS)
        
        # Get model info
        model_key = data.get('model_key', data.get('model', 'UNKNOWN'))
        model_info = get_model_info(model_key)
        
        # Get English and Korean names
        model_eng = model_info.get('full_name', model_key)
        korean_names = get_korean_name_variations(model_key)
        model_kor = korean_names[0] if korean_names else model_eng
        
        # Parse region
        region_parts = data['region'].split()
        region = region_parts[0] if region_parts else data['region']
        district = ' '.join(region_parts[1:]) if len(region_parts) > 1 else ''
        
        title = pattern.format(
            region=region,
            district=district,
            model_eng=model_eng,
            model_kor=model_kor,
            color=data['color']
        )
        
        return title
    
    def generate_greeting_intro(self, data: dict) -> str:
        """Generate varied greeting + intro with Korean/English mix"""
        greeting = random.choice(self.GREETINGS)
        
        # Get model info
        model_key = data.get('model_key', data.get('model', 'UNKNOWN'))
        model_info = get_model_info(model_key)
        
        # Get English and Korean names
        model_eng = model_info.get('full_name', model_key)
        korean_names = get_korean_name_variations(model_key)
        model_kor = korean_names[0] if korean_names else model_eng
        
        intro = random.choice(self.INTROS).format(
            model_eng=model_eng,
            model_kor=model_kor,
            color=data['color']
        )
        
        # Add model description if available
        features = model_info.get('features', [])
        if features:
            feature = random.choice(features)
            intro += f"\n\n{feature} 💨"
        
        return f"{greeting}\n\n{intro}"
    
    def generate_thank_you(self) -> str:
        """Generate varied thank you message"""
        return random.choice(self.THANKS)
        
    def generate_vehicle_info(self, data: dict) -> list[str]:
        """Generate vehicle info list"""
        model_key = data.get('model_key', 'UNKNOWN')
        model_info = get_model_info(model_key)
        
        manufacturer = model_info.get('manufacturer', 'HONDA')
        model_display = get_model_display_name(model_key)
        color = data.get('color', '')
        acquisition_type = data.get('acquisition_type', '인수형')
        region = data.get('region', '')
        
        return [
            f"제조사 : {manufacturer}",
            f"모델명 : {model_display}",
            f"색상 : {color}",
            f"출고 형태 : {acquisition_type}",
            f"출고 지역 : {region}"
        ]

    def generate_intro_with_special_message(self, data: dict, base_intro: str) -> str:
        """
        Expand special message using Anthropic (Claude 3 Haiku)
        """
        special_msg = data.get('special_message', '')
        if not special_msg:
            return base_intro
            
        if not self.client:
            logger.warning("Anthropic client not initialized, using raw message")
            return f"{base_intro}\n\n{special_msg}"
            
        prompt = f"""당신은 친근하고 전문적인 오토바이 리스 회사 'RIDY'의 블로거입니다.
다음 키워드나 문장을 바탕으로, 블로그 도입부에 들어갈 자연스럽고 감성적인 인사말 1~2문장을 작성해주세요.

입력 키워드: "{special_msg}"

작성 가이드:
1. 계절감, 시즈널 이슈(명절, 기념일, 날씨 등)를 자연스럽게 녹여내세요.
2. 라이더들의 안전운전을 기원하는 따뜻한 멘트를 포함하세요.
3. 이모지를 적절히 활용하여 생동감을 주세요. (🌸, ☀️, ❄️, 🏍️, 🍫, 🎁 등)
4. "{special_msg}"라는 단어를 기계적으로 넣지 말고, 문맥에 맞게 풀어서 작성하세요.
5. 존댓말(~해요, ~네요)을 사용하세요.
6. 너무 길지 않게(150자 이내), 하지만 성의 있게 작성하세요.

예시:
입력: 발렌타인 데이
출력: 이제 곧 발렌타인 데이네요! 🍫 우리 라이더 분들도 오늘만큼은 달콤한 하루 보내시고, 초콜릿처럼 기분 좋은 라이딩 하시길 바랄게요~ 🥰 안전운전은 필수인 거 아시죠?

작성된 문장만 출력하세요:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            expanded_msg = message.content[0].text.strip()
            # 따옴표 제거
            expanded_msg = expanded_msg.replace('"', '').replace("'", "")
            
            logger.info(f"Claude expanded: {special_msg} -> {expanded_msg}")
            
            # 기존 인트로에 추가
            return f"{base_intro}\n\n{expanded_msg}"
            
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            return f"{base_intro}\n\n{special_msg}"

    def enhance_with_llm(self, base_text: str, context: dict) -> str:
        """Deprecated"""
        return base_text


# Global instance
content_gen = ContentGenerator()
