# 🚀 빠른 설정 가이드

## 1️⃣ 환경 변수 설정 (3분)

```bash
cd ~/agents/naverblog_automation
cp .env.example .env
nano .env  # 또는 code .env
```

**필수 입력:**
- `SLACK_BOT_TOKEN`: Slack 앱 토큰
- `SLACK_APP_TOKEN`: Socket Mode 토큰
- `SLACK_CHANNEL_ID`: 사용할 채널 ID (예: C1234567890)
- `NAVER_PW`: 네이버 비밀번호 (ID는 이미 설정됨)

## 2️⃣ Slack 앱 생성 (5분)

1. https://api.slack.com/apps 접속
2. "Create New App" → "From scratch"
3. 이름: `RIDY Blog Bot`, Workspace 선택
4. **OAuth & Permissions** → Scopes 추가:
   - `chat:write`
   - `files:read`
   - `channels:history`
   - `commands`
5. **Install to Workspace** → 토큰 복사 → `.env`에 붙여넣기
6. **Socket Mode** 활성화 → App Token 생성 → `.env`에 붙여넣기
7. Slack에서 채널에 봇 초대: `/invite @RIDY Blog Bot`

**채널 ID 찾기:**
```
Slack → 채널 우클릭 → "링크 복사" → 마지막 부분이 ID
예: https://app.slack.com/client/T.../C1468432535607316571
     → SLACK_CHANNEL_ID=C1468432535607316571
```

## 3️⃣ 패키지 설치 (2분)

```bash
cd ~/agents/naverblog_automation
pip3 install -r requirements.txt
```

## 4️⃣ 네이버 로그인 저장 (2분)

```bash
python3 naver_publisher.py
```

- Chrome 열림 → 네이버 로그인
- 터미널에서 Enter
- 세션 저장 완료!

## 5️⃣ 5090 PC에서 Ollama 실행

```bash
# SSH 접속
ssh luke@192.168.75.44

# Ollama 서버 시작
ollama serve --host 0.0.0.0:11434

# 새 터미널에서 모델 다운로드 (최초 1회)
ssh luke@192.168.75.44
ollama pull llama3.2:latest
```

**자동 시작 설정 (선택사항):**
```bash
# systemd 서비스 생성
sudo nano /etc/systemd/system/ollama.service
```

```ini
[Unit]
Description=Ollama LLM Server
After=network.target

[Service]
Type=simple
User=luke
ExecStart=/usr/local/bin/ollama serve --host 0.0.0.0:11434
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ollama
sudo systemctl start ollama
```

## 6️⃣ 봇 실행! 🎉

```bash
python3 bot.py
```

**백그라운드 실행:**
```bash
nohup python3 bot.py > bot.log 2>&1 &
```

## ✅ 테스트

Slack 채널에서:

```
/출고발행

모델: X-ADV750
색상: 펄 화이트
지역: 서울 강남구
출고장착: 안수성
장착옵션:
- 테스트 옵션

추가옵션: 테스트입니다

[이미지 4장 첨부]
```

봇이 처리 시작하면 성공! 🎊

## 🆘 문제 해결

**봇이 응답 안 함:**
```bash
# 로그 확인
tail -f bot.log

# 봇 재시작
pkill -f bot.py
python3 bot.py
```

**네이버 로그인 만료:**
```bash
python3 naver_publisher.py
```

**Ollama 연결 실패:**
```bash
# 5090 PC 확인
ssh luke@192.168.75.44 "curl http://localhost:11434/api/tags"
```

## 📞 문의

문제 발생 시 Luke에게 Slack DM!
