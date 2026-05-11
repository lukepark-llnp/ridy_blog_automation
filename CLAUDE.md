# Naver Blog Automation

## 프로젝트 개요

RIDY 이륜차 리스 서비스의 네이버 블로그 자동 발행 시스템. Slack에서 `/출고발행` 명령 → 폼 입력 → 이미지 첨부 → 자동 블로그 발행.

## 기술 스택

- **Python 3.9.6** (Union/Optional 문법 사용, `str | Path` 불가)
- **Selenium + Chrome** (persistent profile: `chrome_data/`)
- **slack-bolt** (Socket Mode)
- **Anthropic Claude 3 Haiku** (제목/콘텐츠 생성)
- **Pillow** (이미지 최적화/워터마크)

## 실행 환경

- MacBook Pro M3 Pro (운영 서버)
- `nohup ./run_forever.sh > monitor.log 2>&1 &` 로 24/7 운영
- `run_forever.sh`가 bot.py 크래시 시 5초 후 자동 재시작
- **코드 변경 후 반드시 bot.py 프로세스 kill 필요**

## 핵심 파이프라인

/출고발행 (Slack) → 폼 제출 → 이미지 다운로드 → 최적화(1200px, 85%) → 워터마크(RIDY 로고 32%) → LLM 제목/구조 생성 → SEO 태그 생성 → Selenium으로 네이버 블로그 에디터 조작 → 발행 → Slack 알림

## 주요 파일

| 파일 | 역할 |
|---|---|
| `bot.py` | Slack 봇 메인, 오케스트레이션 |
| `naver_publisher_selenium.py` | 네이버 블로그 Selenium 퍼블리셔 (자가복구 포함) |
| `structure_generator.py` | 블로그 구조 요소 생성 |
| `content_generator.py` | Claude Haiku로 제목/인사말/본문 생성 |
| `config.py` | Pydantic Settings (.env 로딩) |
| `models_db.py` | 9개 이륜차 모델 DB (Honda/Yamaha/BMW) |
| `seo_generator.py` | SEO 태그 30개 생성 |
| `manual_login.py` | 네이버 수동 로그인 (세션 만료 시) |
| `run_forever.sh` | 봇 프로세스 감시/자동재시작 |

## 에러 처리 & 자가 복구

- Publisher 레벨: 최대 2회 자동 재시도, 에러 팝업 자동 감지/닫기, 이미지 업로드 3회 재시도
- Bot 레벨: 실패 시 5분 간격 최대 2회 새 세션 재시도, 로그인 에러는 수동 조치 안내

## 개발 컨벤션

- **언어**: 코드는 영어, 로그/주석/Slack 메시지는 한국어
- **Python 3.9 호환**: `Union[X, Y]` 사용 (`X | Y` 불가)
- **네이버 에디터**: iframe `mainFrame` 안에서 동작. `switch_to.frame("mainFrame")` 필수
- **이미지 업로드**: input type=file 찾기 → `send_keys()` → 팝업 감지/처리

## 주의사항

- `chrome_data/` 디렉토리는 네이버 로그인 세션 보관 — **절대 삭제 금지**
- 네이버 에디터는 예고 없이 DOM 구조 변경 가능 — XPath/CSS selector 유연하게 작성
- 레거시 파일 다수 존재 (`naver_publisher_v2~v6.py` 등) — 현재 사용 안 함

## 환경변수
환경변수: `.env` 참조

주요 키: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `ANTHROPIC_API_KEY`, `NAVER_USERNAME`, `NAVER_PASSWORD`

## 로그

- `bot.log`: 봇 애플리케이션 로그
- `bot_output.log`: stdout/stderr 누적
- `logs/`: 발행별 JSON 로그
- `output/post_*/`: 발행별 이미지

## AI 역할 분담 (전역 지침 상속)
- **DevOps/플래닝/아키텍처** → Claude Opus 4.7 (effort: very-high)
- **코딩/QA/코드 리뷰/테스트** → Codex (`codex` / `/codex:*`)
- **콘텐츠 생성/딥 리서치** → Gemini + Codex
- **RAG/사실 확인/대용량 문서** → NotebookLM (`notebooklm ask`)
세부 지침: `~/.claude/CLAUDE.md` (자동 로드).
