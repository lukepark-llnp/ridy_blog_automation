# TODO: Naver Blog Formatting Fix

## 문제 (Luke 피드백 - 2026-02-04 23:45)

1. ❌ 가운데 정렬 및 폰트 스타일링(볼드체, 글씨 크기 등) 전혀 반영 안됨
2. ❌ 이미지들이 글 과 글 사이에 들어가야 하는데(4개씩 묶여서), 글이 쭉~ 나오고 나서 밑에 사진들이 연속으로 들어가 있음

## 레퍼런스 분석

**URL:** https://blog.naver.com/ridyservice/224171131506

**구조:**
1. 인사말 (가운데 정렬)
2. 스티커/이모지 (가운데)
3. 구분선 (가운데)
4. 차량 소개 텍스트 (가운데)
5. **이미지 4장 (2x2 그리드)** ← 여기!
6. 차량 정보 리스트 (가운데 정렬)
7. 구분선
8. 감사 메시지 (가운데)
9. 스티커 (가운데)
10. **이미지 4장 (2x2)** ← 여기!
11. 구분선
12. **"장착 옵션" (볼드 + 가운데)**
13. 옵션 리스트 (가운데)
14. 구분선
15. **"추가 장착 옵션" (볼드 + 가운데)**
16. 추가 옵션 리스트 (가운데)
17. 메시지 (가운데)
18. 구분선
19. **이미지 4장 (2x2)** ← 여기!
20. 구분선
21. **푸터 이미지 2장 (큰 사이즈)**
22. RIDY 로고 (가운데, 크게)
23. 연락처 정보 (가운데)
24. 링크들 (가운데)

## 해결 방안

### 1. DOM Builder 수정 (naver_dom_builder_v2.py)
- 이미지 placeholder를 정확한 위치에 배치
- 현재: 모든 텍스트 → 모든 이미지
- 수정: 텍스트-이미지-텍스트-이미지 순서

### 2. Toolbar 버튼 클릭으로 실제 포맷 적용
- 가운데 정렬: toolbar에서 가운데 정렬 버튼 찾아서 클릭
- 볼드: toolbar에서 볼드 버튼 찾아서 클릭
- `**텍스트**` 형태 제거 → 실제 볼드 적용

### 3. 새 Formatter: NaverFormatterInteractive
- 실제 사용자처럼 단계별 입력
- `type_text()`:
  1. pyperclip 붙여넣기
  2. 텍스트 선택 (Shift+Home)
  3. toolbar 버튼 클릭 (가운데/볼드)
  4. 끝으로 이동
- `upload_image()`:
  1. 현재 위치에서 바로 이미지 업로드
  2. 다음 요소로 이동

### 4. Publisher 로직 변경
- 현재: 텍스트 전체 flush → 이미지 업로드
- 수정: elements를 순서대로 하나씩 처리
  - text → type_text()
  - image_placeholder → upload_image()
  - divider → insert_divider()
  - ...

## 구현 순서

1. [ ] Toolbar 버튼 selector 찾기
   - 가운데 정렬 버튼
   - 볼드 버튼
2. [ ] NaverFormatterInteractive 구현
3. [ ] DOM builder에서 image_placeholder 위치 수정
4. [ ] Publisher에서 순차 처리 로직 구현
5. [ ] 테스트
6. [ ] Luke님께 보고

## 타임라인

- 2026-02-04 23:47: 분석 완료
- 2026-02-05: 구현 + 테스트
- 완료 후 Discord 보고

## 참고

- 스크린샷 5장 저장됨
- 레퍼런스 URL: https://blog.naver.com/ridyservice/224171131506
- Luke: "얼마가 걸리든 상관없어~"
