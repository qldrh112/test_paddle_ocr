# 표 인식 시스템 문서

## 프로젝트 개요

금융거래조회서 이미지에서 표를 자동으로 추출하여 CSV, Excel, JSON 형식으로 저장하는 시스템입니다.

## 기술 스택

- **Python**: 3.10+
- **img2table**: OpenCV 기반 표 감지 라이브러리
- **Tesseract OCR**: 한국어/영어 텍스트 인식
- **Pandas**: 데이터 구조화 및 저장

---

## 설치 및 설정

### 1. Python 의존성 설치

이미 가상환경(`.venv`)에 필요한 패키지가 설치되어 있습니다:
- img2table
- pytesseract
- opencv-python
- Pillow
- pandas
- openpyxl

### 2. Tesseract OCR 설치 (필수!)

> [!IMPORTANT]
> Tesseract OCR이 설치되어 있지 않으면 표 추출이 작동하지 않습니다.

**설치 가이드**: [tesseract_installation_guide.md](file:///C:/Users/User/.gemini/antigravity/brain/fda01b32-acbe-4e64-8691-11613807e2a7/tesseract_installation_guide.md)

---

## 사용 방법

### 기본 사용법

#### 단일 이미지 처리

```powershell
.venv\Scripts\python.exe src/main.py --input test/image/bank_audit_letter-0003.jpg --output output
```

#### 디렉토리 전체 처리

```powershell
.venv\Scripts\python.exe src/main.py --input test/image --output output
```

#### OCR 언어 변경

```powershell
.venv\Scripts\python.exe src/main.py --input test/image --output output --lang kor+eng
```

### 명령줄 인자

| 인자 | 설명 | 필수 | 기본값 |
|------|------|------|--------|
| `--input`, `-i` | 입력 이미지 파일 또는 디렉토리 경로 | ✅ | - |
| `--output`, `-o` | 출력 디렉토리 경로 | ✅ | - |
| `--lang`, `-l` | Tesseract OCR 언어 설정 | ❌ | `kor+eng` |

---

## 출력 형식

각 표마다 3가지 형식으로 저장됩니다:

### 1. CSV 파일
```
bank_audit_letter-0003_table_0.csv
```
- 간단한 2D 표 형식
- Excel 등에서 바로 열기 가능
- UTF-8 인코딩 (한글 지원)

### 2. Excel 파일
```
bank_audit_letter-0003_table_0.xlsx
```
- 원본 표 구조 보존
- 셀 서식 유지
- 복잡한 표에 적합

### 3. JSON 파일
```
bank_audit_letter-0003_table_0.json
```
- 프로그래밍 방식 처리에 적합
- 계층 구조 유지
- API 연동 용이

---

## 프로젝트 구조

```
audit-inquiry-automation1/
├── src/
│   ├── table_extractor/
│   │   ├── __init__.py          # 패키지 초기화
│   │   └── extractor.py         # 표 추출 핵심 로직
│   └── main.py                  # CLI 메인 스크립트
├── test/
│   └── image/                   # 테스트 이미지 (11개)
├── output/                      # 추출 결과 저장 위치
├── .venv/                       # Python 가상환경
└── pyproject.toml               # 프로젝트 설정
```

---

## 주요 기능

### 1. 자동 표 감지

`img2table` 라이브러리를 사용하여:
- 테두리가 있는 표 감지
- 테두리가 없는 표도 감지 (암시적 행/열)
- 복잡한 표 구조 분석 (병합 셀 등)

### 2. 한국어 OCR

Tesseract OCR을 통해:
- 한국어 + 영어 동시 인식
- 높은 정확도의 텍스트 추출
- 로컬 환경에서 안전하게 처리

### 3. 다양한 출력 형식

하나의 표를 여러 형식으로 저장:
- CSV: 간단한 데이터 분석
- Excel: 원본 서식 유지
- JSON: 프로그래밍 용이

---

## 테스트 이미지

### 표가 있는 이미지 (6개)
- `bank_audit_letter-0003.jpg`
- `bank_audit_letter-0004.jpg`
- `bank_audit_letter-0005.jpg`
- `bank_audit_letter-0006.jpg`
- `bank_audit_letter-0008.jpg`
- `bank_audit_letter-0009.jpg`

### 표가 없는 이미지 (5개)
이 이미지들은 처리하지 않습니다 (표가 없으므로):
- `bank_audit_letter-0001.jpg`
- `bank_audit_letter-0002.jpg`
- `bank_audit_letter-0007.jpg`
- `bank_audit_letter-0010.jpg`
- `bank_audit_letter-0011.jpg`

---

## 문제 해결

### 1. "표를 찾지 못했습니다" 메시지

**원인**:
- Tesseract OCR이 설치되지 않음
- 이미지에 실제로 표가 없음
- 이미지 품질이 너무 낮음

**해결**:
1. Tesseract 설치 확인: `tesseract --version`
2. 이미지에 실제로 표가 있는지 육안 확인
3. 이미지 품질이 300 DPI 이상인지 확인

### 2. OCR 결과가 부정확함

**원인**:
- 이미지 해상도가 낮음
- 이미지가 흐리거나 기울어짐
- 한국어 언어 팩 미설치

**해결**:
1. 한국어 언어 팩 확인: `tesseract --list-langs` (kor 포함 확인)
2. 고해상도 이미지 사용 (최소 300 DPI)
3. 이미지 스캔 시 수평 정렬 확인

### 3. 메모리 부족 오류

**원인**:
- 이미지 파일이 너무 큼
- 여러 이미지 동시 처리

**해결**:
- 이미지를 적절한 크기로 리사이징
- 한 번에 하나씩 처리
- 메모리 용량 확인

---

## 성능 최적화 팁

1. **이미지 전처리**: 스캔 시 고품질 설정 사용 (300+ DPI)
2. **배치 처리**: 디렉토리 단위로 한 번에 처리
3. **결과 검증**: CSV 파일을 열어 수동으로 정확도 확인

---

## 향후 개선 사항

- [ ] 자동 이미지 회전/기울기 보정
- [ ] GUI 인터페이스 추가
- [ ] 표 데이터 검증 기능
- [ ] 데이터베이스 연동
- [ ] 일괄 처리 성능 최적화

---

## 라이선스

- **img2table**: MIT License
- **Tesseract OCR**: Apache License 2.0
- **프로젝트 코드**: MIT License (또는 조직 정책에 따름)

---

## 참고 자료

- [img2table 공식 문서](https://github.com/xavctn/img2table)
- [Tesseract OCR 공식 사이트](https://tesseract-ocr.github.io/)
- [Pandas 문서](https://pandas.pydata.org/)
