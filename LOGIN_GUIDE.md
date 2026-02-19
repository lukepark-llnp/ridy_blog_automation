# 🔐 로그인 문제 해결 가이드

## 자동 로그인 실패 시

Discord에서 다음과 같은 알림을 받으셨다면:

```
🔐 네이버 로그인이 필요합니다

**문제:** 자동 로그인 실패 (세션 만료)
```

---

## 해결 방법 (30초 소요)

### 방법 1: 전용 스크립트 사용 (권장) ✅

터미널에서 다음 명령어 실행:

```bash
cd ~/agents/naverblog_automation
source venv/bin/activate
python manual_login.py
```

그러면:
1. 크롬이 자동으로 열립니다
2. 네이버 로그인 화면이 나오면 로그인하세요
3. 로그인 완료 후 쿠키가 자동 저장됩니다
4. Enter 키를 눌러 종료하세요

---

### 방법 2: 수동 (대안)

```bash
cd ~/agents/naverblog_automation
source venv/bin/activate
python naver_publisher_selenium.py login
```

---

## 완료 후

다시 Discord에서 `/출고발행` 명령어를 사용하세요!

이제 자동 로그인이 됩니다. 🚀

---

## 왜 로그인이 풀리나요?

**정상적인 경우:**
- 네이버 보안 정책으로 인한 세션 만료 (보통 1~2주)
- 크롬 프로필 손상 (매우 드물음)

**비정상적인 경우:**
- 봇 강제 종료 시 쿠키 저장 실패
- 시스템 재시작

현재는 3중 백업 시스템으로 매우 안정적입니다:
1. 크롬 프로필 (`chrome_data`)
2. JSON 쿠키 백업 (`naver_cookies.json`)
3. 수동 로그인 시 + 발행 성공 시 자동 저장

---

## 문제가 계속 발생한다면?

Luke에게 연락하세요!
