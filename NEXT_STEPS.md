# 다음 시도할 방법들

**목표**: 레퍼런스 글 100% 복제
**핵심 문제**: 가운데 정렬 + 이미지 그룹

---

## 방법 1: HTML 직접 주입 (추천 ⭐⭐⭐)

### 개념
레퍼런스 글의 HTML 구조를 그대로 복사해서 에디터 DOM에 직접 삽입

### 장점
- 가장 확실한 방법
- 네이버가 렌더링하는 HTML을 그대로 사용
- 정렬/그룹/모든 포맷 그대로 재현

### 단점
- 이미지 URL이 하드코딩됨 → 업로드 후 URL 교체 필요
- 네이버 서버 측 검증 통과 불확실

### 구현 단계
1. 레퍼런스 HTML 추출
   ```python
   # 레퍼런스 페이지에서 .se-main-container 내부 HTML 복사
   reference_html = driver.execute_script("""
       var container = document.querySelector('.se-main-container');
       return container ? container.innerHTML : '';
   """)
   ```

2. 템플릿화
   ```python
   # 텍스트 부분만 변수로 치환
   template = reference_html.replace(
       '서울 강남구', '{region}',
       'X-ADV750', '{model}',
       # ...
   )
   ```

3. 이미지 업로드 → URL 추출 → 템플릿에 삽입
   ```python
   # 이미지 먼저 업로드
   uploaded_urls = upload_images(images)
   
   # HTML에 URL 삽입
   final_html = template.format(
       region=data['region'],
       model=data['model'],
       image1_url=uploaded_urls[0],
       # ...
   )
   ```

4. DOM에 주입
   ```python
   driver.execute_script("""
       var editor = document.querySelector('div[contenteditable="true"]');
       if (editor) {
           editor.innerHTML = arguments[0];
       }
   """, final_html)
   ```

### 예상 성공률: **90%**
### 예상 작업 시간: **30분 ~ 1시간**

---

## 방법 2: 네이버 에디터 API 역공학

### 개념
네이버 스마트 에디터의 내부 JavaScript API를 찾아서 직접 호출

### 단계
1. **API 찾기**
   ```javascript
   // 브라우저 콘솔에서
   Object.keys(window).filter(k => k.includes('editor') || k.includes('SE'))
   
   // 가능한 객체들
   window.SE
   window.smartEditor
   window.__editor
   ```

2. **정렬 함수 찾기**
   ```javascript
   // 가운데 정렬 버튼 클릭 시 호출되는 함수 추적
   // Chrome DevTools > Sources > Event Listener Breakpoints
   ```

3. **직접 호출**
   ```python
   driver.execute_script("""
       // 예시 (실제 API는 분석 필요)
       window.SE.align('center');
       window.SE.insertImageGroup([url1, url2, url3, url4]);
   """)
   ```

### 도구
- `analyze_editor_api.py` 작성 완료
- 브라우저 개발자 도구 + 수동 테스트 필요

### 예상 성공률: **50%** (API가 존재하고 접근 가능한 경우)
### 예상 작업 시간: **1 ~ 2시간**

---

## 방법 3: 툴바 버튼 자동 클릭

### 개념
Selenium으로 툴바의 정렬 버튼을 직접 클릭

### 단계
1. **버튼 찾기**
   ```python
   # 가운데 정렬 버튼
   align_btn = driver.find_element(By.CSS_SELECTOR, 
       "button[title*='중앙'], button[aria-label*='중앙']")
   ```

2. **텍스트 선택 → 버튼 클릭**
   ```python
   # 1. 텍스트 입력
   pyperclip.copy("안녕하세요 RIDY입니다!")
   actions.key_down(cmd).send_keys('v').key_up(cmd).perform()
   
   # 2. 전체 선택
   actions.key_down(cmd).send_keys('a').key_up(cmd).perform()
   
   # 3. 정렬 버튼 클릭
   align_btn.click()
   ```

### 문제점
- 텍스트 선택이 제대로 안될 수 있음
- 버튼이 숨겨져 있거나 접근 불가능할 수 있음

### 예상 성공률: **60%**
### 예상 작업 시간: **30분**

---

## 방법 4: Playwright로 전환

### 개념
Selenium 대신 Playwright 사용 → CDP (Chrome DevTools Protocol) 제어

### 장점
- CDP로 더 깊은 브라우저 제어 가능
- 네트워크 요청/응답 intercept 가능
- 이미지 업로드 후 서버 응답 URL 캡처 가능

### 단점
- 기존 코드 대부분 재작성 필요
- Playwright 학습 시간 필요

### 예상 성공률: **70%**
### 예상 작업 시간: **2 ~ 3시간**

---

## 방법 5: 하이브리드 접근

### 개념
수동 + 자동 조합

### 단계
1. Selenium으로 이미지 업로드 + 기본 텍스트 입력
2. 브라우저를 **닫지 않고** 유지
3. Luke가 **수동으로** 정렬 조정
4. 발행 버튼만 Selenium으로 클릭

### 장점
- 100% 확실
- 당장 사용 가능

### 단점
- 완전 자동화 아님

### 예상 성공률: **100%**
### 예상 작업 시간: **10분 (자동) + 2분 (수동)**

---

## 추천 순서

### 1단계: **방법 1 (HTML 직접 주입)** 시도
- 가장 빠르고 확실
- 실패해도 30분~1시간 손실

### 2단계: 실패 시 **방법 3 (툴바 버튼 클릭)** 시도
- 구현 간단
- 30분 추가

### 3단계: 여전히 실패 시 **방법 2 (API 역공학)** 시도
- `analyze_editor_api.py` 실행
- 브라우저 콘솔에서 수동 테스트
- 1~2시간

### 최후 수단: **방법 5 (하이브리드)**
- 완전 자동화 포기
- 반자동으로 운영

---

## 이미지 그룹 해결 방법

### A. HTML 주입 방식 (방법 1과 함께)
- 레퍼런스 HTML에 이미 그룹 구조 포함
- 이미지 URL만 교체하면 그룹 유지

### B. 이미지 업로드 API 찾기
```python
# 네이버 이미지 업로드 API 직접 호출 (추정)
response = requests.post(
    'https://blog.naver.com/api/uploadImage',
    files={'file': open(image, 'rb')},
    cookies=cookies
)
image_url = response.json()['url']
```

### C. 수동 그룹 생성
- 이미지 4장 업로드 후
- JavaScript로 `se-imageGroup` 구조 생성

---

## 파일 구조 제안

### 새로 작성할 파일
```
naver_publisher_html_inject.py  # 방법 1: HTML 주입
naver_publisher_toolbar.py      # 방법 3: 툴바 클릭
naver_api_client.py             # 방법 2: API 클라이언트
reference_template.html          # 레퍼런스 HTML 템플릿
```

### 수정할 파일
```
naver_publisher_selenium.py     # 기존 코드 백업 후 통합
test_reference_clone.py         # 새 방법 테스트
```

---

## 체크리스트

### 방법 1 시도 전
- [ ] 레퍼런스 HTML 추출 (`curl` 또는 브라우저 소스보기)
- [ ] `.se-main-container` 내부 HTML 파싱
- [ ] 변수화할 부분 식별 (제목, 본문, 이미지 URL)
- [ ] 템플릿 파일 작성

### 방법 1 구현 중
- [ ] 이미지 업로드 → URL 추출 로직
- [ ] HTML 템플릿에 URL 삽입
- [ ] JavaScript로 DOM에 주입
- [ ] 네이버 에디터가 인식하는지 확인

### 테스트
- [ ] 제목 표시 확인
- [ ] 가운데 정렬 확인
- [ ] 이미지 4장 그룹 확인
- [ ] 리스트 정렬 확인
- [ ] 구분선 확인
- [ ] 이모지 이미지 확인
- [ ] 푸터 배너 확인
- [ ] 발행 테스트

---

**다음 작업 시작 시:**
1. `PROGRESS.md` 읽기
2. `NEXT_STEPS.md` (이 파일) 읽기
3. 방법 1부터 시도
4. 결과 기록

**마지막 업데이트**: 2026-02-05 00:24
