# 네이버 블로그 자동화 진행 상황

**프로젝트**: 네이버 블로그 출고 현황 자동 발행
**날짜**: 2026-02-05
**작업 시간**: 약 10시간

---

## ✅ 완료된 기능

### 1. 이미지 처리 (100% 완료)
- ✅ URL에서 이미지 다운로드
- ✅ 이미지 최적화 (1200px, 85% quality)
- ✅ RIDY 로고 워터마크 추가 (8% size, bottom-right)
- ✅ 압축률 평균 89.2% (22.8MB → 2.3MB)

### 2. 텍스트 입력 (80% 완료)
- ✅ 제목 입력
- ✅ 본문 텍스트 입력 (단락 분리 작동)
- ✅ 이모지 텍스트 입력
- ✅ 구분선 입력
- ✅ 리스트 입력
- ❌ **가운데 정렬 미작동** (핵심 문제)

### 3. 이미지 업로드 (70% 완료)
- ✅ 단일 이미지 업로드
- ✅ 12장 모두 업로드 확인됨
- ❌ **4장씩 그룹으로 묶기 실패**
- ❌ 푸터 배너 이미지 추가 안됨

### 4. 태그 입력 (100% 완료)
- ✅ SEO 태그 자동 생성 (최대 20개)
- ✅ 발행 모달에서 태그 입력 (pyperclip + Cmd+V)

### 5. Slack 연동 (100% 완료)
- ✅ Modal Form으로 데이터 수집
- ✅ 실시간 진행 상황 업데이트 (멘션 포함)
- ✅ 채널: C0ACV4A27EE (#2c-ridy-naver_blog_blog)

### 6. 발행 기능 (보류)
- ⏸️ 2단계 발행 로직 구현됨
- ⏸️ URL 변경 확인 로직 추가됨
- ⏸️ 레퍼런스 복제 완성 후 테스트 예정

---

## ❌ 미완료 기능

### 1. 가운데 정렬 (핵심 문제)
**증상:**
- pyperclip으로 붙여넣은 텍스트는 모두 왼쪽 정렬
- JavaScript로 `se-text-paragraph-align-center` 클래스 추가 시도했으나 실패
- Center 포맷터 작성했으나 텍스트 3줄만 입력되고 중단

**시도한 방법:**
1. `NaverFormatterSimple` - 정렬 무시
2. `NaverFormatterCenter` - 클래스 추가 실패
3. `NaverFormatterHybrid` - 여러 paste 시 한 줄로 합쳐짐
4. `NaverFormatterV3` - execCommand selection 실패
5. `NaverFormatterV4` - insertHTML 렌더링 안됨

**근본 원인:**
- 네이버 에디터는 단순 텍스트 입력만으로는 정렬 불가
- 툴바 버튼 클릭 또는 내부 API 호출 필요

### 2. 이미지 그룹 (4장씩 묶기)
**증상:**
- 이미지가 하나씩 따로 업로드됨
- 레퍼런스는 `se-imageGroup se-l-collage` 구조

**시도한 방법:**
1. `as_group=True` 파라미터 추가
2. 파일 경로를 `\n`으로 구분해서 한 번에 전달
3. 실제로는 여전히 개별 이미지로 표시됨

**근본 원인:**
- file input의 multiple 속성 활용 방법 불명확
- 네이버가 여러 파일을 한 번에 받아야 자동으로 그룹 생성

### 3. 푸터 이미지 & RIDY 로고
- 구현 시도 안함 (정렬 문제 해결이 우선)

---

## 📁 주요 파일

### Python 모듈
- `bot.py` - Slack 봇 (PID: 25771)
- `naver_publisher_selenium.py` - 발행 로직
- `naver_formatter_simple.py` - Simple 포맷터 (작동, 정렬 X)
- `naver_formatter_center.py` - Center 포맷터 (실패)
- `naver_dom_builder_v2.py` - DOM 빌더
- `image_optimizer.py` - 이미지 최적화
- `image_watermark.py` - 워터마크 추가
- `content_generator.py` - 텍스트 생성 (336+ 조합)
- `test_reference_clone.py` - 레퍼런스 복제 테스트

### 레퍼런스
- `REFERENCE_CLONE.md` - 레퍼런스 구조 분석
- 레퍼런스 URL: https://blog.naver.com/ridyservice/224171131506

### 설정
- `.env` - Slack 토큰
- `.naver_cookies.pkl` - Playwright 쿠키 (fallback)
- `assets/emoji_45.png` - 좋아요 이모지
- `assets/emoji_46.png` - 따봉 이모지
- `assets/footer/` - 푸터 배너 2장
- `assets/ridy_logo.png` - RIDY 로고

### 테스트 결과
- `output/test_complete_1770213639/` - 성공 케이스
  - 제목/본문 분리 O
  - 텍스트 단락 분리 O
  - 이미지 12장 O
  - 정렬 X, 그룹 X

---

## 🔍 발견 사항

### 네이버 에디터 구조
1. **iframe**: `#mainFrame` 안에 에디터 존재
2. **편집 영역**: `div[contenteditable="true"]` (1개만 존재)
3. **제목**: `.se-component.se-documentTitle span.__se-node`
4. **본문**: `.se-component.se-text` (텍스트 블록)
5. **이미지 그룹**: `.se-component.se-imageGroup.se-l-collage`
   - `.se-imageGroup-col-2` = 2열 그리드 (2x2)
6. **정렬**: `se-text-paragraph-align-center` 클래스

### Selenium 제약사항
1. `pyperclip` + `Cmd+V`는 텍스트만 가능
2. 정렬/볼드/색상은 HTML로 삽입해도 네이버가 무시
3. `document.execCommand()` 지원하지만 selection 실패
4. file input에 여러 경로 전달해도 그룹 안됨

### 작동하는 것들
- ✅ 쿠키 기반 로그인 (30일)
- ✅ Tab + Enter로 제목/본문 분리
- ✅ pyperclip으로 텍스트 입력
- ✅ `\n\n`으로 단락 분리
- ✅ file input.send_keys()로 이미지 업로드
- ✅ JavaScript로 태그 input 접근

---

## 🐛 알려진 버그

1. **제목/본문 섞임** → 수정됨 (Tab + click)
2. **텍스트 한 줄로 합쳐짐** → 수정됨 (`\n\n` 분리)
3. **이미지 1장만 표시** → 수정됨 (12장 확인)
4. **가운데 정렬 안됨** → 미해결 (핵심 문제)
5. **이미지 그룹 안됨** → 미해결

---

## 📊 성능

### 이미지 최적화
- 입력: 평균 2.3MB/장 (10장 = 22.8MB)
- 출력: 평균 0.23MB/장 (10장 = 2.3MB)
- 압축률: 89.2%
- 처리 시간: ~15초/10장

### 전체 프로세스
- 이미지 다운로드: ~10초
- 최적화: ~15초
- 워터마크: ~5초
- 업로드: ~80초 (12장)
- **총 소요 시간**: ~2분

---

## 💡 교훈

1. **네이버 에디터는 복잡함**: 단순 텍스트 입력으로는 한계
2. **정렬은 API 필요**: 툴바 버튼 클릭 또는 내부 API 호출 필수
3. **Selenium 한계**: 브라우저 UI 자동화는 가능하지만 에디터 내부 제어는 어려움
4. **pyperclip은 제한적**: 텍스트만 가능, 포맷은 불가
5. **레퍼런스 분석 중요**: HTML 구조 정확히 파악해야 함

---

**마지막 업데이트**: 2026-02-05 00:24
**다음 작업**: NEXT_STEPS.md 참조
