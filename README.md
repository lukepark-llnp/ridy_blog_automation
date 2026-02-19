# 🏍️ Naver Blog Automation - RIDY 출고 발행 봇

Slack에서 간편하게 네이버 블로그 출고 글을 자동 발행하는 시스템입니다.

## 🌟 주요 기능

- **Slack Modal Form**: `/출고발행` 명령어로 모달 폼 열기 (9개 모델 지원)
- **실시간 진행상황**: 다운로드→최적화→워터마크→생성→발행 단계별 업데이트
- **이미지 자동 최적화**: 1200px 리사이징 + 85% 품질 압축 (평균 60% 용량 절감)
- **워터마크 자동 추가**: RIDY 로고 투명 배경 (32% 크기, 우측 하단)
- **AI 콘텐츠 생성**: Claude 3 Haiku로 다채로운 제목/인사말/특별 메시지 생성
- **SEO 최적화**: 30개 해시태그 자동 생성 (모델/지역/배기량/카테고리 기반)
- **구조화된 에디터**: 가운데 정렬, 볼드, 폰트 크기, 4장씩 콜라주 지원
- **로그인 세션 관리**: JSON 쿠키 + Chrome 프로필 이중 백업
- **자동 재시작**: `run_forever.sh` 모니터링 + crontab 재부팅 시 자동 시작
- **완전 자동화**: Selenium + Chrome으로 네이버 블로그 자동 발행

## 🖥️ 운영 환경

- **서버**: MacBook Pro M3 Pro (Ridy Agent Node)
- **위치**: `/Users/llnpbot/ridy/naver_blog_automation`
- **Python**: 3.9.6
- **LLM**: Anthropic Claude 3 Haiku (API)
- **브라우저**: Chrome 144 + ChromeDriver
- **상시 가동**: `run_forever.sh` (무한 루프 모니터링)

## 📋 지원 모델 (9종)

| 제조사 | 모델 | 배기량 | 카테고리 |
|--------|------|--------|----------|
| HONDA | PCX 125 | 125cc | 스쿠터 |
| HONDA | Super Cub 110 | 110cc | 언더본 |
| YAMAHA | NMAX 125 | 125cc | 스쿠터 |
| YAMAHA | ADV 350 | 350cc | 어드벤처 |
| HONDA | Forza 350 | 330cc | 스쿠터 |
| YAMAHA | XMAX 300 | 292cc | 스쿠터 |
| YAMAHA | TMAX 560 | 560cc | 스쿠터 |
| HONDA | Forza 750 | 745cc | 스쿠터 |
| BMW | C400GT | 350cc | 스쿠터 |

## 🚀 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/lukepark-llnp/ridy_blog_automation.git
cd ridy_blog_automation
```

### 2. Python 가상환경 생성

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일 생성:

```env
# Slack Bot
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_CHANNEL_ID=C0ACV4A27EE

# Naver
NAVER_ID=ridyservice
NAVER_PW=your-password
NAVER_BLOG_URL=https://blog.naver.com/ridyservice

# Anthropic (Claude 3 Haiku)
ANTHROPIC_API_KEY=sk-ant-api03-your-key

# Paths
CHROME_PROFILE_PATH=./chrome_data
OUTPUT_DIR=./output
```

### 4. 네이버 로그인 (최초 1회)

```bash
python manual_login.py
```

크롬 창이 열리면 네이버 블로그에 로그인하고 **Enter** 키를 누릅니다.
쿠키가 `naver_cookies.json`에 저장됩니다.

### 5. 봇 실행

```bash
# 일반 실행 (테스트)
python bot.py

# 백그라운드 상시 가동
chmod +x run_forever.sh
nohup ./run_forever.sh > monitor.log 2>&1 &
```

### 6. Slack에서 테스트

Slack 채널에서 `/출고발행` 명령어 입력!

## 📁 주요 파일

| 파일 | 설명 |
|------|------|
| `bot.py` | Slack 봇 메인 (모달 폼 + 워크플로우) |
| `naver_publisher_selenium.py` | Selenium 네이버 발행 엔진 |
| `content_generator.py` | Claude 3 Haiku 콘텐츠 생성 |
| `structure_generator.py` | 동적 인덱스 계산 (이모지/푸터) |
| `naver_formatter_center.py` | 에디터 포매터 (정렬/볼드/폰트/링크) |
| `watermark.py` | 이미지 워터마크 (RIDY 로고) |
| `image_optimizer.py` | 이미지 최적화 (1200px, 85%) |
| `seo_generator.py` | SEO 태그 생성 (최대 30개) |
| `models_db.py` | 9개 모델 데이터베이스 |
| `footer_manager.py` | 고정 푸터 이미지 (보험/혜택) |
| `config.py` | 환경 변수 관리 |
| `manual_login.py` | 네이버 로그인 (쿠키 저장) |
| `retry_last_failed.py` | 실패한 발행 재시도 |
| `run_forever.sh` | 무한 루프 모니터링 (자동 재시작) |

## 🔧 시스템 요구사항

- **OS**: macOS (테스트 환경: macOS Sequoia 15.2)
- **Python**: 3.9+ (3.9.6에서 테스트됨)
- **Chrome**: 최신 버전
- **메모리**: 최소 4GB RAM
- **네트워크**: 안정적인 인터넷 연결

## 🎨 기능 세부사항

### 이미지 처리

1. **다운로드**: Slack 첨부 이미지 자동 다운로드
2. **최적화**: 1200px 리사이징 + 85% JPEG 품질
3. **워터마크**: RIDY 로고 (32% 크기, 투명 배경, 우측 하단)
4. **콜라주**: 4장씩 그룹 (2x2 배치)

### 콘텐츠 생성

- **제목**: `{모델명} {색상} 출고 | {지역}` (고정 패턴)
- **인사말**: Claude 3 Haiku 랜덤 생성 (336+ 조합)
- **특별 메시지**: 키워드 → Claude로 문장 확장
- **SEO 태그**: 모델/지역/배기량/제조사 기반 (최대 30개)

### 블로그 구조

1. 인사말 (가운데, 폰트 19px)
2. 이모지 1 (emoji_46)
3. 구분선
4. 차량 소개
5. [이미지 그룹 1] (0~3번)
6. 차량 정보 리스트
7. 구분선
8. 감사 인사
9. [이미지 그룹 2] (4~7번)
10. 옵션 리스트
11. 구분선
12. [이미지 그룹 3] (8번~, 동적)
13. 추가 옵션 (있는 경우)
14. 이모지 2 (emoji_45)
15. 맺음말 + 특별 메시지
16. [푸터 이미지] (보험/혜택 배너)
17. 연락처 + 링크

## 🛠️ 트러블슈팅

### 로그인 실패

```bash
# 쿠키 재생성
rm naver_cookies.json
python manual_login.py
```

### 봇이 멈춤

```bash
# 프로세스 확인
ps aux | grep bot.py

# 재시작
pkill -f bot.py
nohup ./run_forever.sh > monitor.log 2>&1 &
```

### 이미지 업로드 실패

- Chrome 프로필 삭제: `rm -rf chrome_data`
- 다시 로그인: `python manual_login.py`

## 📊 로그 구조

발행 로그는 `logs/` 폴더에 JSON 형식으로 저장됩니다:

```json
{
  "timestamp": "2026-02-19T19:30:00+09:00",
  "user_id": "U061UL4K0HL",
  "status": "success",
  "blog_url": "https://blog.naver.com/ridyservice/224180353327",
  "input_data": { ... },
  "images_processed": 10,
  "duration_seconds": 45.2
}
```

## 🔐 보안

- `.env` 파일은 `.gitignore`에 포함
- `naver_cookies.json`도 Git 추적 제외
- Slack 토큰/API 키는 환경 변수로 관리

## 📝 라이선스

Private - LLNP & YXS

## 👨‍💻 개발자

- **Luke Park** (LLNP)
- **Yoda** (AI Agent)

---

**문의**: #naver_blog_automation (Slack)
