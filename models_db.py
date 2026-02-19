"""Motorcycle model database with Korean names and descriptions"""

MODELS = {
    "PCX125": {
        "manufacturer": "HONDA",
        "full_name": "PCX 125",
        "korean_names": ["PCX125", "PCX 125"],  # 검색용
        "category": "스쿠터",
        "engine": "125cc 단기통",
        "features": [
            "출퇴근과 배달에 최적화된 연비형 스쿠터",
            "가볍고 다루기 쉬운 차체로 초보자에게 인기",
            "넓은 수납공간과 편안한 시트"
        ],
        "keywords": ["출퇴근", "배달", "초보자추천", "연비좋은", "125cc"],
        "seo_keywords": ["PCX", "PCX125", "혼다PCX", "125cc스쿠터", "배달오토바이"]
    },
    "SuperCub110": {
        "manufacturer": "HONDA",
        "full_name": "Super Cub 110",
        "korean_names": ["슈퍼커브110", "슈퍼 커브 110", "커브110"],
        "category": "언더본",
        "engine": "110cc 단기통",
        "features": [
            "전 세계 1억대 판매를 돌파한 전설의 모델",
            "놀라운 연비와 내구성으로 업무용 최강자",
            "간편한 자동 클러치 시스템"
        ],
        "keywords": ["출퇴근", "배달", "연비최강", "내구성", "전설의바이크"],
        "seo_keywords": ["슈퍼커브", "SuperCub", "커브110", "혼다커브", "배달바이크"]
    },
    "NMAX125": {
        "manufacturer": "YAMAHA",
        "full_name": "NMAX 125",
        "korean_names": ["엔맥스125", "엔맥스 125", "NMAX"],
        "category": "스쿠터",
        "engine": "125cc 단기통",
        "features": [
            "스포티한 디자인과 우수한 핸들링",
            "VVA 가변 밸브 시스템으로 강력한 성능",
            "도심 주행에 최적화된 민첩성"
        ],
        "keywords": ["출퇴근", "배달", "스포티", "125cc", "야마하"],
        "seo_keywords": ["엔맥스", "NMAX", "NMAX125", "야마하엔맥스", "125cc스쿠터"]
    },
    "ADV350": {
        "manufacturer": "YAMAHA",
        "full_name": "ADV 350",
        "korean_names": ["어드밴스350", "어드밴스 350", "ADV350"],
        "category": "어드벤처 스쿠터",
        "engine": "350cc 단기통",
        "features": [
            "도심과 교외를 자유롭게 넘나드는 어드벤처 스쿠터",
            "큰 휠과 긴 서스펜션으로 험로 주행 가능",
            "넉넉한 적재공간과 편안한 라이딩 포지션"
        ],
        "keywords": ["배달", "투어링", "어드벤처", "350cc", "올라운더"],
        "seo_keywords": ["어드밴스", "ADV350", "야마하ADV", "어드벤처스쿠터", "350cc"]
    },
    "Forza350": {
        "manufacturer": "HONDA",
        "full_name": "Forza 350",
        "korean_names": ["포르자350", "포르자 350", "Forza350"],
        "category": "스쿠터",
        "engine": "330cc 단기통",
        "features": [
            "프리미엄 빅 스쿠터의 정수",
            "풍부한 토크와 안정적인 고속 주행",
            "첨단 편의사양과 넓은 수납공간"
        ],
        "keywords": ["배달", "투어링", "프리미엄", "빅스쿠터", "350cc"],
        "seo_keywords": ["포르자", "Forza", "Forza350", "혼다포르자", "빅스쿠터"]
    },
    "XMAX300": {
        "manufacturer": "YAMAHA",
        "full_name": "XMAX 300",
        "korean_names": ["엑스맥스300", "엑스맥스 300", "XMAX300"],
        "category": "스쿠터",
        "engine": "292cc 단기통",
        "features": [
            "역동적인 디자인과 강력한 성능",
            "트랙션 컨트롤 시스템(TCS) 탑재",
            "장거리 투어링에도 완벽한 편안함"
        ],
        "keywords": ["배달", "투어링", "스포츠", "300cc", "프리미엄"],
        "seo_keywords": ["엑스맥스", "XMAX", "XMAX300", "야마하XMAX", "300cc스쿠터"]
    },
    "TMAX560": {
        "manufacturer": "YAMAHA",
        "full_name": "TMAX 560",
        "korean_names": ["티맥스560", "티맥스 560", "TMAX560"],
        "category": "스쿠터",
        "engine": "560cc 병렬 2기통",
        "features": [
            "스쿠터의 왕, MAX 시리즈 최상위 모델",
            "강력한 병렬 2기통 엔진과 스포츠 주행 성능",
            "첨단 전자제어 장비 풀옵션"
        ],
        "keywords": ["투어링", "프리미엄", "하이엔드", "560cc", "최고급"],
        "seo_keywords": ["티맥스", "TMAX", "TMAX560", "야마하티맥스", "빅스쿠터"]
    },
    "Forza750": {
        "manufacturer": "HONDA",
        "full_name": "Forza 750",
        "korean_names": ["포르자750", "포르자 750", "Forza750"],
        "category": "스쿠터",
        "engine": "745cc 병렬 2기통",
        "features": [
            "혼다 빅 스쿠터의 플래그십 모델",
            "DCT(듀얼 클러치 트랜스미션) 탑재",
            "고속도로와 장거리 투어링의 완벽한 동반자"
        ],
        "keywords": ["투어링", "프리미엄", "하이엔드", "750cc", "DCT"],
        "seo_keywords": ["포르자", "Forza750", "혼다포르자", "750cc스쿠터", "DCT스쿠터"]
    },
    "C400GT": {
        "manufacturer": "BMW",
        "full_name": "C400GT",
        "korean_names": ["C400GT", "BMW C400GT"],  # 한글 표기 없음
        "category": "스쿠터",
        "engine": "350cc 단기통",
        "features": [
            "독일 프리미엄 브랜드 BMW의 스쿠터",
            "우수한 안정성과 첨단 전자제어",
            "그랜드 투어링에 최적화된 설계"
        ],
        "keywords": ["프리미엄", "투어링", "BMW", "수입바이크", "350cc"],
        "seo_keywords": ["BMW", "C400GT", "비엠더블유", "수입스쿠터", "프리미엄스쿠터"]
    }
}


def get_model_info(model_key: str) -> dict:
    """
    Get model information by key
    
    Args:
        model_key: Model key (e.g., "PCX125", "SuperCub110")
        
    Returns:
        dict: Model info or empty dict if not found
    """
    return MODELS.get(model_key, {})


def get_model_display_name(model_key: str) -> str:
    """
    Get model display name (manufacturer + full_name)
    
    Example: "HONDA - PCX 125"
    """
    info = get_model_info(model_key)
    if not info:
        return model_key
    
    return f"{info['manufacturer']} - {info['full_name']}"


def get_korean_name_variations(model_key: str) -> list[str]:
    """Get all Korean name variations for SEO"""
    info = get_model_info(model_key)
    return info.get('korean_names', [])


def get_seo_keywords(model_key: str) -> list[str]:
    """Get SEO keywords for model"""
    info = get_model_info(model_key)
    return info.get('seo_keywords', [])


# Model list for dropdown
MODEL_DROPDOWN_OPTIONS = [
    {"key": "PCX125", "display": "HONDA - PCX 125"},
    {"key": "SuperCub110", "display": "HONDA - Super Cub 110 (슈퍼 커브 110)"},
    {"key": "NMAX125", "display": "YAMAHA - NMAX 125 (엔맥스 125)"},
    {"key": "ADV350", "display": "YAMAHA - ADV 350 (어드밴스 350)"},
    {"key": "Forza350", "display": "HONDA - Forza 350 (포르자 350)"},
    {"key": "XMAX300", "display": "YAMAHA - XMAX 300 (엑스맥스 300)"},
    {"key": "TMAX560", "display": "YAMAHA - TMAX 560 (티맥스 560)"},
    {"key": "Forza750", "display": "HONDA - Forza 750 (포르자 750)"},
    {"key": "C400GT", "display": "BMW - C400GT"}
]
