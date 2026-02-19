# 🏍️ Naver Blog Automation - RIDY 출고 발행 봇

Slack에서 간편하게 네이버 블로그 출고 글을 자동 발행하는 시스템

## 🌟 주요 기능

- **Slack Modal Form**: 폼으로 깔끔하게 정보 입력 (제조사/모델/년식/색상/옵션 등)
- **실시간 진행상황**: 다운로드→최적화→워터마크→생성→발행 단계별 실시간 업데이트
- **이미지 자동 최적화**: 1200px 리사이징 + 85% 품질로 용량 감소 (평균 60% 절감)
- **워터마크 자동 추가**: 모든 이미지에 RIDY 로고 삽입 (우측 하단)
- **LLM 콘텐츠 생성**: 맥미니 로컬 Ollama로 매번 다른 제목/인사말 생성
- **작성자 멘션**: 완료/에러 시 작성자에게 멘션 알림
- **구조화된 로그**: JSON 형식으로 모든 발행 기록 저장
- **에러 처리**: 에러 발생 시 상세 로그 + 관리자 알림
- **네이버 자동 발행**: Selenium으로 완전 자동화

## 📁 프로젝트 구조

```
naverblog_automation/
├── bot.py                      # Slack 봇 메인
├── watermark.py                # 이미지 워터마크 처리
├── content_generator.py        # LLM 콘텐츠 생성
├── naver_publisher.py          # Selenium 네이버 발행
├── session_manager.py          # 네이버 로그인 세션 관리
├── progress_tracker.py         # 실시간 진행상황 업데이트
├── logger.py                   # 구조화된 JSON 로그
├── image_optimizer.py          # 이미지 자동 최적화
├── models_db.py                # 모델 DB (제조사, 한글명, 키워드)
├── seo_generator.py            # SEO 태그 자동 생성
├── footer_manager.py           # 고정 배너 이미지 관리
├── config.py                   # 설정 관리
├── templates/
│   └── blog_template.py        # HTML 템플릿
├── assets/
│   ├── ridy_logo.png           # 워터마크 로고
│   └── footer/                 # 고정 배너 이미지들
│       ├── benefits.png        # 고객 혜택 정리
│       ├── insurance_comparison.png  # 보험 비교표
│       └── benefits_combined.png     # 합쳐진 배너
├── output/                     # 생성된 파일들
├── logs/                       # 발행 로그 (자동 생성)
├── requirements.txt
├── .env                        # 환경 변수
├── .naver_cookies.pkl          # 네이버 세션 쿠키 (자동 생성)
├── README.md
├── SETUP.md                    # 빠른 설정 가이드
├── NAVER_LOGIN.md              # 로그인 안정화 가이드
└── SEO_GUIDE.md                # SEO 최적화 가이드
```

## 🚀 설치 및 설정

### 1. Python 환경 설정

```bash
cd ~/agents/naverblog_automation

# 가상환경 생성 (선택사항)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example`을 복사해서 `.env` 생성:

```bash
cp .env.example .env
```

`.env` 파일 수정:

```env
# Slack Bot (https://api.slack.com/apps 에서 생성)
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_CHANNEL_ID=C1234567890

# Naver
NAVER_ID=ridyservice
NAVER_PW=your-password-here
NAVER_BLOG_URL=https://blog.naver.com/ridyservice

# Ollama (5090 PC)
OLLAMA_HOST=http://192.168.75.44:11434
OLLAMA_MODEL=llama3.2:latest

# Paths
CHROME_PROFILE_PATH=/Users/goldglitplate.bot/.naver-chrome-profile
OUTPUT_DIR=./output
```

### 3. Slack 앱 생성

1. https://api.slack.com/apps 접속
2. "Create New App" → "From scratch"
3. App 이름: `RIDY Blog Bot`
4. Workspace 선택

**필요한 권한 (OAuth & Permissions):**
- `chat:write` - 메시지 전송
- `files:read` - 이미지 다운로드
- `channels:history` - 채널 메시지 읽기
- `commands` - 슬래시 커멘드

**Socket Mode 활성화:**
- Settings → Socket Mode → Enable
- App Token 생성 (connections:write 권한)

**봇을 채널에 초대:**
```
/invite @RIDY Blog Bot
```

### 4. 네이버 로그인 설정 (최초 1회)

```bash
python naver_publisher.py
```

- Chrome 창이 열리면 수동으로 네이버 로그인
- 로그인 후 터미널에서 Enter
- 세션이 저장되어 이후 자동 로그인

### 5. 5090 PC에서 Ollama 서버 실행

```bash
# 5090 PC (Ubuntu)에서
ollama serve --host 0.0.0.0:11434

# 모델 다운로드 (최초 1회)
ollama pull llama3.2:latest
```

## 📱 사용 방법

### 방법 1: Slack Modal Form (추천) ⭐

1. **#naver_blog_automation** 채널에서 `/출고발행` 입력
2. **팝업 폼이 뜨면 정보 입력:**
   - 제조사 선택 (HONDA/YAMAHA/SUZUKI 등)
   - 모델명, 년식, 색상
   - 출고 지역, 출고 장착
   - 기본 장착 옵션
   - 추가 옵션 문의
   - 특별 메시지 (선택)
3. **제출 클릭**
4. **확인 메시지가 뜨면 스레드에 이미지 첨부** (최소 4장, 권장 14장)
5. **자동 발행 시작!**

### 방법 2: 텍스트 입력 (레거시)

채널에서 다음 양식으로 메시지 작성 + 이미지 첨부:

```
/출고발행

제조사: HONDA
모델: X-ADV750
년식: 2024
색상: 펄 화이트
지역: 서울 강남구
출고장착: 안수성

[기본 장착 옵션]
- 스크린(폭 스크린, 미들 스크린)
- 사이드 스탠드(발판형)

[추가 옵션]
동등 추가로 컨시안은 음성이 있으면 문의
```

### 봇 처리 과정 (실시간 업데이트)

```
🤖 @김하나 출고 발행을 시작합니다! 📝

⏳ 이미지 다운로드 중... (14장)
✅ 다운로드 완료!

⏳ 이미지 최적화 중...
✅ 최적화 완료! (평균 400KB, 62% 감소)

⏳ 워터마크 추가 중...
✅ 워터마크 완료!

⏳ 블로그 글 생성 중... (LLM)
✅ 콘텐츠 생성 완료!

⏳ 네이버 블로그 발행 중...
✅ 발행 완료!

━━━━━━━━━━━━━━━━━━━━━━

🎉 @김하나 출고 발행이 완료되었습니다!

📝 제목: 서울 강남구 배달 오토바이 X-ADV750 출고
🔗 URL: https://blog.naver.com/ridyservice/224171131507
⏱️ 소요시간: 38초
📊 로그: logs/2024-02-04_12-30-15.json
```

## 🛠️ 개발자 가이드

### 봇 실행

```bash
python bot.py
```

### 로그 확인

기본적으로 콘솔에 출력됨. 파일 로깅 추가하려면:

```python
# bot.py 수정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
```

### 워터마크 커스터마이징

`watermark.py` 수정:
- 텍스트 대신 로고 이미지 사용
- 위치/크기/투명도 조정

### LLM 프롬프트 수정

`content_generator.py`에서 패턴 추가/수정:

```python
TITLE_PATTERNS = [
    "{region} {district} 배달 오토바이 {model} 출고",
    # 새 패턴 추가...
]
```

## 🔧 트러블슈팅

### 1. Slack 메시지 수신 안 됨

- 봇이 채널에 초대되었는지 확인: `/invite @RIDY Blog Bot`
- Socket Mode가 활성화되었는지 확인
- `SLACK_CHANNEL_ID`가 올바른지 확인

### 2. 이미지 다운로드 실패

- `SLACK_BOT_TOKEN`에 `files:read` 권한 있는지 확인
- 네트워크 연결 확인

### 3. 네이버 로그인 실패

```bash
# 세션 초기화 후 재로그인
rm -rf ~/.naver-chrome-profile
python naver_publisher.py
```

### 4. LLM 응답 없음

- 5090 PC의 Ollama 서버가 실행 중인지 확인:
  ```bash
  curl http://192.168.75.44:11434/api/tags
  ```
- 방화벽 확인

### 5. Selenium 에러

- ChromeDriver 자동 설치 실패 시 수동 설치:
  ```bash
  brew install chromedriver  # macOS
  ```

## 📊 성능

- **처리 시간**: 약 45초 (14장 기준)
  - 다운로드: 5초
  - 워터마크: 10초
  - LLM 생성: 5초
  - 네이버 발행: 25초

- **리소스 사용**:
  - 맥미니: 이미지 처리 + Slack 봇
  - 5090 PC: LLM 추론만 (GPU 활용)

## 🎯 TODO

- [ ] 고정 이미지 (RIDY 혜택 2장) 실제 파일로 교체
- [ ] RIDY 로고 이미지로 워터마크 업그레이드
- [ ] Discord 봇 추가 지원
- [ ] 발행 예약 기능 (특정 시간에 자동 발행)
- [ ] 발행 히스토리 DB 저장
- [ ] 이미지 리사이징 최적화 (네이버 권장 크기)

## 📝 라이선스

Internal use only - LLNP & YXS

## 🤝 기여

문의: Luke (goldplatter@discord)
