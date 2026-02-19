"""SEO keyword and tag generation"""
import logging
from models_db import get_model_info, get_seo_keywords

logger = logging.getLogger(__name__)


def generate_seo_tags(data: dict) -> list[str]:
    """
    Generate SEO tags for blog post (최대 30개)
    
    Args:
        data: Blog data with model_key, region, acquisition_type, etc.
        
    Returns:
        list[str]: SEO hashtags (without # prefix)
    """
    tags = []
    
    # === 기본 태그 (항상 포함) ===
    base_tags = [
        "오토바이리스",
        "오토바이렌탈",
        "무신용리스",
        "렌탈",
        "리스",
        "rental",
        "라이디렌트",
        "라이디렌탈",
        "라이디리스",
        "RIDY",
        "RIDY렌탈"
    ]
    tags.extend(base_tags)
    
    # === 인수형/반납형 태그 ===
    acquisition_type = data.get('acquisition_type', '')
    if '인수' in acquisition_type:
        tags.append("인수형리스")
        tags.append("인수형")
    elif '반납' in acquisition_type:
        tags.append("반납형렌탈")
        tags.append("반납형")
    
    # === 모델 정보 기반 태그 ===
    model_key = data.get('model_key', data.get('model', 'UNKNOWN'))
    model_info = get_model_info(model_key)
    
    # 모델명 (예: X-ADV750 → Xadv750)
    full_name = model_info.get('full_name', model_key)
    model_tag = full_name.replace('-', '').replace(' ', '')
    tags.append(model_tag)
    
    # 배기량 (예: 750cc)
    cc = model_info.get('cc', 0)
    if cc > 0:
        tags.append(f"{cc}cc")
        
        # 배기량 등급
        if cc <= 125:
            tags.extend(["125cc급", "스쿠터"])
        elif cc <= 300:
            tags.extend(["쿼터급", "쿼터급바이크", "쿼터급오토바이"])
        elif cc <= 600:
            tags.extend(["미들급", "미들급바이크"])
        else:
            tags.extend(["빅스쿠터", "대형바이크"])
    
    # 제조사 (예: HONDA → honda, 혼다오토바이)
    manufacturer = model_info.get('manufacturer', '').upper()
    if manufacturer:
        tags.append(manufacturer.lower())
        
        # 제조사별 한글 태그
        manufacturer_kr = {
            'HONDA': '혼다오토바이',
            'YAMAHA': '야마하오토바이',
            'SUZUKI': '스즈키오토바이',
            'KAWASAKI': '가와사키오토바이',
            'BMW': 'BMW오토바이',
            'KTM': 'KTM오토바이',
            'SYM': 'SYM오토바이',
            'KYMCO': '킴코오토바이'
        }.get(manufacturer)
        
        if manufacturer_kr:
            tags.append(manufacturer_kr)
    
    # 카테고리 (예: 스쿠터, 네이키드 등)
    category = model_info.get('category', '')
    if category:
        tags.append(category)
    
    # SEO 키워드 (models_db에서 가져옴)
    seo_keywords = get_seo_keywords(model_key)
    for keyword in seo_keywords[:5]:
        clean_keyword = keyword.replace(' ', '')
        tags.append(clean_keyword)
    
    # === 지역 태그 ===
    region = data.get('region', '').replace(' ', '')
    if region:
        tags.append(f"{region}출고")
        tags.append(f"{region}오토바이")
    
    # === 연식 태그 ===
    year = data.get('year', '')
    if year:
        tags.append(f"{year}년식")
    
    # === 중복 제거 & 최대 30개 제한 ===
    tags = list(dict.fromkeys(tags))  # 중복 제거, 순서 유지
    tags = tags[:30]  # 최대 30개
    
    logger.info(f"Generated {len(tags)} SEO tags")
    return tags


def generate_meta_description(data: dict, title: str) -> str:
    """
    Generate meta description for SEO
    
    Args:
        data: Blog data
        title: Generated title
        
    Returns:
        str: Meta description (150-160 chars)
    """
    model_key = data.get('model_key', data.get('model', 'UNKNOWN'))
    model_info = get_model_info(model_key)
    
    model_name = model_info.get('full_name', model_key)
    region = data.get('region', '')
    color = data.get('color', '')
    
    description = (
        f"{region} {model_name} {color} 출고 완료! "
        f"RIDY 렌탈로 합리적인 가격에 바이크를 이용하세요. "
        f"무료 탁송, 신분보험 지원, 사고파지 포함."
    )
    
    return description[:160]  # Limit to 160 chars
