# 네이버 블로그 자동화 - 실패 분석 & 교훈

**목표**: 레퍼런스 글(https://blog.naver.com/ridyservice/224171131506)을 100% 똑같이 자동 복제
**핵심 문제**: 가운데 정렬 + 이미지 4장씩 그룹으로 묶기

---

## 네이버 스마트 에디터 ONE의 특성

### 구조
```
<iframe id="mainFrame">
  <div class="se-main-container">
    <div contenteditable="true">  ← 실제 편집 영역 (1개만 존재)
      <div class="se-component se-text">
        <p class="se-text-paragraph se-text-paragraph-align-center">
          <span>텍스트</span>
        </p>
      </div>
      <div class="se-component se-imageGroup se-l-collage">
        <div class="se-imageGroup-col-2">  ← 2x2 그리드
          <img />
          <img />
          <img />
          <img />
        </div>
      </div>
    </div>
  </div>
</iframe>
```

### 핵심 발견
1. **정렬은 클래스 기반**: `se-text-paragraph-align-center`
2. **이미지 그룹은 특수 구조**: `se-imageGroup` + `se-imageGroup-col-2`
3. **단순 텍스트 입력으로는 한계**: pyperclip + Cmd+V는 plain text만
4. **HTML 삽입도 제한적**: `innerHTML` 설정해도 네이버가 무시하거나 재구성

---

## 시도한 방법들 & 실패 이유

### ❌ 방법 1: pyperclip + JavaScript 클래스 추가 (`NaverFormatterSimple`)

**시도:**
```python
# 1. pyperclip으로 텍스트 붙여넣기
pyperclip.copy("안녕하세요 RIDY입니다!")
actions.key_down(cmd).send_keys('v').key_up(cmd).perform()

# 2. JavaScript로 정렬 클래스 추가
driver.execute_script("""
    var paragraphs = document.querySelectorAll('.se-text-paragraph');
    var lastP = paragraphs[paragraphs.length - 1];
    lastP.classList.add('se-text-paragraph-align-center');
""")
```

**결과:**
- ✅ 텍스트는 잘 입력됨
- ✅ 단락 분리도 잘됨 (`\n\n` 사용)
- ❌ **정렬 클래스 추가는 무시됨**
  - 클래스는 추가되지만 시각적으로 가운데 정렬 안됨
  - 네이버 에디터가 자체 렌더링 로직으로 무시하는 듯

**교훈:**
- pyperclip은 plain text만 가능
- 사후 JavaScript 수정은 네이버가 무시

---

### ❌ 방법 2: JavaScript로 정렬 후 텍스트 입력 (`NaverFormatterCenter`)

**시도:**
```python
# 1. 텍스트 입력
pyperclip.copy("안녕하세요 RIDY입니다!")
actions.key_down(cmd).send_keys('v').key_up(cmd).perform()

# 2. 바로 정렬 클래스 추가
driver.execute_script("""
    var lastP = document.querySelector('.se-text-paragraph:last-child');
    lastP.classList.add('se-text-paragraph-align-center');
""")

# 3. Enter로 다음 줄
actions.send_keys(Keys.RETURN).perform()
```

**결과:**
- ❌ **텍스트 3줄만 입력되고 중단**
  - 30개 요소 중 3개만 들어감
  - Enter 키 때문에 포커스가 이상한 곳으로 이동한 듯
- ❌ 정렬도 여전히 안됨

**교훈:**
- 각 요소마다 Enter를 누르면 포커스 제어 실패
- 정렬은 입력 시점이 아닌 다른 방법 필요

---

### ❌ 방법 3: document.execCommand() 사용 (`NaverFormatterV3`)

**시도:**
```python
# 1. 텍스트 입력
driver.execute_script("""
    var editor = document.querySelector('div[contenteditable="true"]');
    editor.focus();
    
    // 텍스트 삽입
    document.execCommand('insertText', false, '안녕하세요 RIDY입니다!');
    
    // 전체 선택
    document.execCommand('selectAll', false, null);
    
    // 가운데 정렬
    document.execCommand('justifyCenter', false, null);
""")
```

**결과:**
- ✅ `insertText`는 작동함
- ❌ **`selectAll`이 작동하지 않음**
  - Selection이 생성되지 않음
  - Range 객체가 제대로 설정 안됨
- ❌ `justifyCenter`도 당연히 실패

**교훈:**
- `document.execCommand()`는 일부만 지원
- Selection API가 제대로 작동하지 않음

---

### ❌ 방법 4: innerHTML로 HTML 직접 삽입 (`NaverFormatterV4`)

**시도:**
```python
html = """
<div class="se-component se-text">
    <p class="se-text-paragraph se-text-paragraph-align-center">
        <span>안녕하세요 RIDY입니다!</span>
    </p>
</div>
"""

driver.execute_script("""
    var editor = document.querySelector('div[contenteditable="true"]');
    editor.innerHTML = arguments[0];
""", html)
```

**결과:**
- ✅ HTML은 삽입됨 (개발자 도구에서 확인 가능)
- ❌ **네이버가 렌더링하지 않음**
  - 화면에는 빈 공간만 표시
  - 네이버 에디터가 자체 데이터 구조로 관리하는 듯
  - `<script type="text/data" class="__se_module_data">` 같은 메타데이터 필요한 듯

**교훈:**
- innerHTML 설정만으로는 부족
- 네이버 에디터가 별도 데이터 구조 관리

---

### ❌ 방법 5: 여러 번 paste (버퍼 분할) (`NaverFormatterHybrid`)

**시도:**
```python
# 각 텍스트를 개별로 paste
for text in ["안녕하세요 RIDY입니다!", "오늘은 X-ADV750이 출고되었어요!"]:
    pyperclip.copy(text)
    actions.key_down(cmd).send_keys('v').key_up(cmd).perform()
    time.sleep(0.3)
    # Enter 없이 계속 paste
```

**결과:**
- ❌ **모든 텍스트가 한 줄로 합쳐짐**
  - 단락 구분이 사라짐
  - 네이버가 연속된 입력을 하나로 병합

**교훈:**
- 여러 번 paste는 단락 구분 불가
- `\n\n`을 포함한 한 번 paste가 유일한 방법

---

### ❌ 방법 6: 이미지 파일 경로 `\n`으로 구분 (그룹 업로드)

**시도:**
```python
# 4개 이미지 경로를 \n으로 구분
file_paths = "\n".join([
    "/path/to/img1.jpg",
    "/path/to/img2.jpg",
    "/path/to/img3.jpg",
    "/path/to/img4.jpg"
])

file_input.send_keys(file_paths)
```

**결과:**
- ❌ **여전히 4개가 따로따로 업로드됨**
  - `se-imageGroup` 구조 생성 안됨
  - 각각 `se-component se-image`로 개별 삽입

**시도 2: multiple 속성 확인**
```python
file_input = driver.find_element(By.XPATH, "//input[@type='file']")
print(file_input.get_attribute('multiple'))  # None
```

**결과:**
- ❌ **file input에 `multiple` 속성 없음**
  - 한 번에 여러 파일 선택 불가능
  - OS 파일 선택 대화상자에서는 가능하지만 Selenium으로는 불가

**교훈:**
- file input의 `multiple` 속성이 없으면 진짜 그룹 업로드 불가
- 네이버가 4장을 그룹으로 인식하려면 **동시 선택** 필요

---

### ❌ 방법 7: 툴바 버튼 찾기 시도

**시도:**
```python
# 가운데 정렬 버튼 찾기
align_btn = driver.find_element(By.CSS_SELECTOR, 
    "button[title*='중앙'], button[aria-label*='중앙']")
```

**결과:**
- ❌ **버튼을 찾을 수 없음**
  - 툴바가 동적으로 생성되는 듯
  - 또는 iframe 밖에 있거나 숨겨져 있음

**시도 2: 모든 버튼 출력**
```python
buttons = driver.find_elements(By.TAG_NAME, "button")
for btn in buttons:
    print(btn.get_attribute('title'), btn.get_attribute('aria-label'))
```

**결과:**
- 많은 버튼이 있지만 정렬 버튼은 없음
- 또는 title/aria-label이 없어서 식별 불가

**교훈:**
- 툴바 버튼 자동 클릭도 쉽지 않음

---

## 작동하는 것들 (100% 성공)

### ✅ 1. 쿠키 기반 로그인
```python
# Playwright 쿠키 → Selenium에서 재사용
cookie_file = Path('.naver_cookies.pkl')
data = pickle.loads(cookie_file.read_bytes())
cookies = data.get('cookies', [])

for cookie in cookies:
    driver.add_cookie(cookie)
```
- 30일간 유효
- 재로그인 불필요

### ✅ 2. iframe 전환
```python
driver.switch_to.frame("mainFrame")
```
- 네이버 에디터는 iframe 안에 존재

### ✅ 3. 제목 입력
```python
title_span = driver.find_element(By.CSS_SELECTOR, 
    ".se-component.se-documentTitle span.__se-node")
title_span.click()
title_span.send_keys("제목 텍스트")
```
- 제목과 본문은 완전히 분리된 영역

### ✅ 4. 제목/본문 분리
```python
# 제목 입력 후
actions.send_keys(Keys.TAB).perform()  # 또는 Keys.RETURN

# 본문 영역 명시적 클릭
content_area = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
content_area.click()
```
- Tab 또는 Enter로 본문 이동
- 명시적 클릭이 더 확실함

### ✅ 5. 텍스트 입력 (pyperclip)
```python
# 여러 단락을 \n\n으로 구분
text = "안녕하세요 RIDY입니다!\n\n오늘은 X-ADV750이 출고되었어요!"
pyperclip.copy(text)

from selenium.webdriver.common.action_chains import ActionChains
actions = ActionChains(driver)
actions.key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
```
- `\n\n`이 단락 구분자로 인식됨
- 한 번에 붙여넣어야 함

### ✅ 6. 이미지 업로드 (개별)
```python
file_input = driver.find_element(By.XPATH, "//input[@type='file']")
abs_path = str(Path("image.jpg").absolute())
file_input.send_keys(abs_path)
time.sleep(4)  # 업로드 대기
```
- 절대 경로 필수
- 하나씩 업로드는 완벽하게 작동

### ✅ 7. 태그 입력
```python
# 발행 모달 열린 후
tag_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='태그']")

tags_text = "#태그1 #태그2 #태그3"
pyperclip.copy(tags_text)
actions.key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
```
- 최대 10개까지
- `#` 포함해서 입력

### ✅ 8. 이미지 업로드 확인
```python
images_in_editor = driver.find_elements(By.CSS_SELECTOR, ".se-component-content img")
print(f"Total images: {len(images_in_editor)}")
```
- 업로드된 이미지 개수 확인 가능

---

## 작동하지 않는 것들

### ❌ 1. 가운데 정렬
- pyperclip 후 클래스 추가 → 무시됨
- innerHTML 설정 → 렌더링 안됨
- execCommand('justifyCenter') → selection 실패
- 툴바 버튼 클릭 → 버튼을 찾을 수 없음

### ❌ 2. 이미지 그룹 (4장씩 묶기)
- 파일 경로 `\n` 구분 → 개별 업로드됨
- file input에 multiple 속성 없음
- se-imageGroup 구조를 수동으로 생성해도 렌더링 안됨

### ❌ 3. 볼드/색상/폰트 크기
- pyperclip으로는 plain text만
- HTML로 넣어도 무시됨

### ❌ 4. 리스트 (•) 자동 생성
- `• 항목1\n• 항목2`로 입력하면 텍스트로만 표시
- 실제 리스트 요소 (`<ul><li>`)로 변환 안됨

---

## 네이버 에디터의 내부 구조 (추정)

### 데이터 레이어
네이버 에디터는 **DOM과 별도로 데이터 구조를 관리**하는 것으로 추정:

```html
<div class="se-component se-text">
    <p>텍스트</p>
    <script type="text/data" class="__se_module_data" 
            data-module-v2='{"type": "v2_text", "id": "SE-xxx", "data": {...}}'>
    </script>
</div>
```

- 각 컴포넌트마다 `__se_module_data` 스크립트 태그 존재
- JSON 형태로 메타데이터 저장
- DOM을 직접 수정해도 이 데이터와 동기화 안되면 무시됨

### 렌더링 프로세스 (추정)
1. 사용자 입력 (pyperclip, 툴바 버튼 등)
2. 네이버 에디터 내부 로직이 이벤트 캐치
3. 내부 데이터 구조 업데이트
4. 데이터 → DOM 렌더링
5. `__se_module_data` 생성/업데이트

**결론**: DOM을 직접 조작해도 내부 데이터가 업데이트 안되면 무시됨

---

## 시도하지 않은 방법들

### 1. 네이버 에디터 API 직접 호출 ⭐⭐⭐
**개념:**
```javascript
// 예상되는 API (실제로는 분석 필요)
window.SE.insertComponent({
    type: 'text',
    content: '안녕하세요',
    align: 'center'
});

window.SE.insertImageGroup([
    'https://...img1.jpg',
    'https://...img2.jpg',
    'https://...img3.jpg',
    'https://...img4.jpg'
]);
```

**장점:**
- 네이버가 의도한 방식
- 정렬/그룹 모두 가능

**단점:**
- API가 공개되어 있지 않음
- 역공학 필요

**시도 방법:**
1. 브라우저 콘솔에서 `Object.keys(window)` 확인
2. 정렬 버튼 클릭 시 Network 탭에서 API 호출 확인
3. Event Listener Breakpoint로 함수 추적

**예상 작업 시간:** 1~2시간
**성공률:** 50% (API가 존재하고 접근 가능한 경우)

---

### 2. HTML 템플릿 + 이미지 URL 교체 ⭐⭐⭐
**개념:**
1. 레퍼런스 페이지의 HTML을 그대로 복사
2. 텍스트/이미지 URL을 변수로 치환
3. 이미지를 먼저 업로드해서 URL 획득
4. 템플릿에 URL 삽입 후 전체 DOM 교체

**장점:**
- 레퍼런스와 100% 동일한 구조
- 정렬/그룹 모두 포함
- `__se_module_data`도 함께 복사

**단점:**
- 이미지 업로드 후 URL 추출이 관건
- 네이버가 서버 측에서 검증할 수 있음

**구현 예시:**
```python
# 1. 레퍼런스 HTML 추출
reference_html = requests.get('https://blog.naver.com/ridyservice/224171131506').text
# .se-main-container 내부만 파싱

# 2. 템플릿화
template = reference_html.replace(
    'https://postfiles.pstatic.net/...img1.png', '{image1_url}',
    '서울 강남구', '{region}',
    'X-ADV750', '{model}',
    # ...
)

# 3. 이미지 업로드 → URL 추출
uploaded_urls = []
for img in images:
    file_input.send_keys(str(img.absolute()))
    time.sleep(4)
    
    # 업로드된 이미지 URL 추출
    last_img = driver.find_element(By.CSS_SELECTOR, ".se-component-content img:last-child")
    url = last_img.get_attribute('src')
    uploaded_urls.append(url)

# 4. 템플릿에 URL 삽입
final_html = template.format(
    image1_url=uploaded_urls[0],
    image2_url=uploaded_urls[1],
    # ...
    region='용산구',
    model='NMAX 155'
)

# 5. DOM 교체
driver.execute_script("""
    var editor = document.querySelector('div[contenteditable="true"]');
    editor.innerHTML = arguments[0];
""", final_html)
```

**예상 작업 시간:** 30분~1시간
**성공률:** 70~90%

---

### 3. Playwright CDP (Chrome DevTools Protocol) ⭐⭐
**개념:**
Playwright는 CDP로 네트워크 요청/응답을 intercept 가능:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
    # 이미지 업로드 응답 캡처
    def handle_response(response):
        if '/upload' in response.url:
            data = response.json()
            print(f"Uploaded image URL: {data['url']}")
    
    page.on('response', handle_response)
    
    # 파일 선택
    page.set_input_files('input[type="file"]', ['img1.jpg', 'img2.jpg'])
```

**장점:**
- 네트워크 레벨 제어
- 이미지 업로드 응답에서 URL 직접 추출

**단점:**
- 기존 Selenium 코드 전면 재작성 필요

**예상 작업 시간:** 2~3시간
**성공률:** 70%

---

### 4. 하이브리드 (반자동) ⭐
**개념:**
완전 자동화를 포기하고 수동 개입:
1. Selenium으로 이미지 업로드 + 기본 텍스트 입력
2. 브라우저를 **닫지 않고** 30초 대기
3. Luke가 수동으로 정렬 조정
4. 다시 Selenium이 발행 버튼 클릭

**장점:**
- 100% 확실
- 당장 사용 가능

**단점:**
- 완전 자동화 아님
- 매번 수동 작업 필요

**예상 작업 시간:** 10분 (구현) + 2분 (매번 수동)
**성공률:** 100%

---

## 레퍼런스 HTML 구조 분석

### 가운데 정렬된 텍스트
```html
<div class="se-component se-text se-l-default">
    <div class="se-component-content">
        <div class="se-section se-section-text se-l-default se-section-align-center">
            <div class="se-module se-module-text">
                <p class="se-text-paragraph se-text-paragraph-align-center" style="line-height:2.1;">
                    <span class="se-fs-fs24 se-ff-system se-weight-unset se-style-unset">
                        안녕하세요 RIDY입니다!
                    </span>
                </p>
            </div>
        </div>
    </div>
    <script type="text/data" class="__se_module_data" 
            data-module-v2='{"type": "v2_text", "id": "SE-xxx", "data": {"ctype": "text"}}'></script>
</div>
```

**핵심 클래스:**
- `se-section-align-center` (섹션 레벨)
- `se-text-paragraph-align-center` (단락 레벨)
- `se-fs-fs24` (폰트 크기 24px)

### 이미지 그룹 (2x2)
```html
<div class="se-component se-imageGroup se-l-collage">
    <div class="se-component-content se-component-content-extend">
        <div class="se-section se-section-imageGroup se-l-collage">
            <div class="se-imageGroup-viewer">
                <div class="se-imageGroup-container">
                    <div class="se-imageGroup-item se-imageGroup-col-2">
                        <div class="se-module se-module-image" style="width:50.19813974498491%;">
                            <a href="#" class="se-module-image-link">
                                <img src="https://postfiles.pstatic.net/.../img1.png" />
                            </a>
                        </div>
                        <div class="se-module se-module-image" style="width:49.80186025501509%;">
                            <a href="#" class="se-module-image-link">
                                <img src="https://postfiles.pstatic.net/.../img2.png" />
                            </a>
                        </div>
                    </div>
                    <div class="se-imageGroup-item se-imageGroup-col-2">
                        <div class="se-module se-module-image" style="width:50.25062656641604%;">
                            <a href="#" class="se-module-image-link">
                                <img src="https://postfiles.pstatic.net/.../img3.png" />
                            </a>
                        </div>
                        <div class="se-module se-module-image" style="width:49.74937343358396%;">
                            <a href="#" class="se-module-image-link">
                                <img src="https://postfiles.pstatic.net/.../img4.png" />
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script type="text/data" class="__se_module_data" 
            data-module-v2='{"type": "v2_imageGroup", "id": "SE-xxx", "data": {...}}'></script>
</div>
```

**핵심:**
- `se-imageGroup-col-2`: 2열 그리드
- width는 비율로 동적 계산됨 (50% 전후)
- 각 이미지가 `<a>` 링크로 감싸져 있음

---

## 최종 결론 & 추천 방법

### 현재 상황
- **80% 완성**: 이미지 업로드, 텍스트 입력, 태그 모두 작동
- **20% 남음**: 가운데 정렬 + 이미지 그룹

### 추천 순서

#### 1순위: HTML 템플릿 방식 ⭐⭐⭐
- 레퍼런스 HTML을 템플릿으로 사용
- 이미지 URL만 교체
- 성공률 70~90%
- 작업 시간 30분~1시간

**구현 포인트:**
1. curl로 레퍼런스 페이지 HTML 다운로드
2. `.se-main-container` 내부만 추출
3. `{image1_url}`, `{text1}` 등으로 변수화
4. 이미지 업로드 후 `img.src` 속성에서 URL 추출
5. `editor.innerHTML = final_html` 로 전체 교체

#### 2순위: 네이버 API 역공학 ⭐⭐
- `analyze_editor_api.py` 실행
- 브라우저 콘솔에서 `window.SE` 확인
- 정렬 버튼 클릭 시 호출되는 함수 추적
- 성공률 50%
- 작업 시간 1~2시간

#### 3순위: Playwright 전환 ⭐⭐
- CDP로 네트워크 intercept
- 이미지 업로드 응답에서 URL 추출
- 성공률 70%
- 작업 시간 2~3시간 (재작성 필요)

#### 최후: 하이브리드 (반자동) ⭐
- 기본은 자동, 정렬만 수동
- 성공률 100%
- 매번 2분 수동 작업

---

## 체크리스트 (다음 사람이 할 일)

### 사전 확인
- [ ] Python 3.11+ 설치
- [ ] Chrome 144 설치
- [ ] ChromeDriver 144 설치 (~/bin/)
- [ ] venv 생성: `python -m venv venv`
- [ ] 패키지 설치: `pip install selenium pyperclip Pillow requests beautifulsoup4`
- [ ] 쿠키 파일 존재: `.naver_cookies.pkl`

### 방법 1 (HTML 템플릿) 시도
- [ ] 레퍼런스 HTML 다운로드: `curl -o reference.html https://blog.naver.com/PostView.naver?blogId=ridyservice&logNo=224171131506`
- [ ] `.se-main-container` 내부 HTML 추출 (BeautifulSoup4 사용)
- [ ] 텍스트를 `{variable}` 형태로 변수화
- [ ] 이미지 src를 `{image1_url}` 형태로 변수화
- [ ] 이미지 업로드 후 URL 추출 로직 작성
- [ ] 템플릿에 변수 삽입 후 `innerHTML` 설정
- [ ] 테스트: 제목, 정렬, 이미지 그룹 확인

### 실패 시 방법 2 (API 역공학)
- [ ] `analyze_editor_api.py` 실행
- [ ] 브라우저 콘솔에서 `Object.keys(window)` 확인
- [ ] `window.SE` 또는 `window.__editor` 같은 객체 찾기
- [ ] 정렬 버튼 클릭 → Network 탭에서 API 호출 확인
- [ ] Event Listener Breakpoint로 함수 추적
- [ ] Python에서 JavaScript로 API 직접 호출

### 최후 수단
- [ ] 하이브리드 방식 구현 (30초 대기 + 수동 조정)

---

**마지막 업데이트**: 2026-02-05 12:05
**작성자**: Yoda (OpenClaw)
**다음 작업자**: ??? (Good luck! 🍀)
