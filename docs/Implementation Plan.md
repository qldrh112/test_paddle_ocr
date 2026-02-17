# 표 인식 시스템 구현 계획 (수정)
금융거래조회서 이미지에서 표를 정확하게 인식하고 표의 내용을 추출하는 시스템을 구현합니다.

## 문제 정의
### 현재 상황
- test/image 디렉토리에 11개의 금융거래조회서 이미지 존재
- 6개 이미지에만 표 포함: bank_audit_letter-0003.jpg, 0004.jpg, 0005.jpg, 0006.jpg, 0008.jpg, 0009.jpg
- 나머지 5개 이미지는 표가 없으므로 처리 대상이 아님
### 요구사항
1. 표 내용 추출: 표가 있는 이미지에서 표의 셀 데이터를 정확하게 추출하여 구조화된 형태로 저장
2. 로컬 환경: 보안상의 이유로 온프레미스 환경에서 동작 (클라우드 API 사용 불가)
3. 문서화: 모든 구현 과정과 결과를 .md 파일로 문서화
4. 테스트: poetry run python 명령어를 사용하여 테스트
5. 사용자 피드백 반영
> <span style="color:red">WARNING</span>  
PaddlePaddle 이슈: 이전에 PaddlePaddle을 사용했으나 잘 작동하지 않았습니다. 따라서 더 안정적인 대안을 사용합니다.

> <span style="color:purple">IMPORTANT</span>  
새로운 접근 방식: img2table 라이브러리와 Tesseract OCR을 사용합니다. img2table은 OpenCV 기반으로 표 구조를 감지하며, 여러 OCR 엔진을 지원합니다.

> <span style="color:purple">IMPORTANT</span>  
Poetry 의존성 관리: agent.md에 명시된 대로 Poetry를 사용하여 의존성을 관리합니다.

## 제안 변경사항
### 프로젝트 구조
```
audit-inquiry-automation1/
├── src/
│   ├── table_extractor/
│   │   ├── __init__.py
│   │   ├── detector.py          # 표 감지 모듈
│   │   ├── ocr_engine.py        # PaddleOCR 엔진
│   │   ├── table_parser.py      # 표 구조 분석 및 데이터 추출
│   │   └── utils.py             # 유틸리티 함수
│   └── main.py                  # 실행 스크립트
├── docs/
│   ├── 01_구현_계획.md
│   ├── 02_환경_설정.md
│   ├── 03_표_인식_구현.md
│   └── 04_테스트_결과.md
├── test/
│   └── image/                   # 기존 테스트 이미지
├── output/                      # 추출 결과 저장
└── pyproject.toml               # Poetry 설정
```
컴포넌트 1: 환경 설정
[MODIFY] 
pyproject.toml
Poetry 프로젝트를 초기화하고 필요한 의존성을 추가합니다:

img2table: 표 감지 및 구조 분석 (OpenCV 기반)
pytesseract: Tesseract OCR Python wrapper
python-tesseract-ocr: Tesseract OCR 엔진 (Windows용 바이너리 포함)
opencv-python: 이미지 전처리
Pillow: 이미지 로딩
pandas: 데이터 구조화 및 CSV 저장
openpyxl: Excel 파일 저장
컴포넌트 2: 표 추출 모듈
[NEW] 
table_extractor.py
img2table을 사용하여 이미지에서 표를 감지하고 추출합니다:

이미지 로드 및 전처리 (회전/기울기 보정)
img2table을 사용한 표 영역 감지
Tesseract OCR을 통한 셀 텍스트 추출
표 구조 분석 (행/열, 병합 셀 처리)
컴포넌트 3: 데이터 구조화 모듈
[NEW] 
data_formatter.py
추출된 표 데이터를 구조화하여 저장합니다:

DataFrame으로 변환
JSON 형식으로 저장 (계층 구조 유지)
CSV 형식으로 저장 (간단한 2D 표)
Excel 형식으로 저장 (원본 표 구조 보존)
컴포넌트 4: 유틸리티 모듈
[NEW] 
utils.py
공통 유틸리티 함수:

이미지 전처리 (노이즈 제거, 대비 향상)
한국어 텍스트 후처리 (공백 제거, 특수문자 정규화)
로깅 설정
파일 I/O 헬퍼 함수
컴포넌트 5: 실행 스크립트
[NEW] 
main.py
전체 파이프라인을 실행하는 메인 스크립트:

이미지 디렉토리 스캔
각 이미지에 대해 표 감지 및 추출 실행
결과를 output/ 디렉토리에 저장
처리 결과 요약 출력
검증 계획
자동화 테스트
1. 전체 이미지 처리 테스트
bash
# 프로젝트 루트에서 실행
poetry run python src/main.py --input test/image --output output
예상 결과:

표가 있는 6개 이미지: output/ 디렉토리에 JSON, CSV, Excel 파일 생성
각 파일명: {원본파일명}_table_{인덱스}.{확장자}
2. 개별 이미지 테스트
bash
# 특정 이미지만 처리
poetry run python src/main.py --input test/image/bank_audit_letter-0003.jpg --output output
검증 항목:

표 감지 정확도: img2table이 표를 정확하게 식별
텍스트 추출 정확도: OCR 결과와 실제 표 내용 비교
표 구조 정확도: 행/열 개수, 셀 병합 처리, 헤더 행 인식
한국어 인식: Tesseract의 한국어 언어 팩(kor) 정확도
수동 검증
1. 추출 결과 검토
사용자가 직접 다음을 확인합니다:

output/ 디렉토리의 JSON/CSV 파일을 열어 추출된 데이터 확인
원본 이미지와 비교하여 누락되거나 잘못 추출된 데이터 확인
한국어 텍스트 인식 정확도 확인
2. 에지 케이스 확인
복잡한 표 구조 (병합 셀, 중첩 표)
이미지 품질이 낮은 경우
표가 회전되거나 기울어진 경우
성능 측정
이미지당 평균 처리 시간
메모리 사용량
추출 정확도 (수동으로 레이블링한 데이터 기준)
문서화 계획
모든 문서는 docs/ 디렉토리에 한국어로 작성됩니다:

01_구현_계획.md: 이 문서의 복사본
02_환경_설정.md: Poetry 설정 및 의존성 설치 가이드
03_표_인식_구현.md: 각 모듈의 상세 구현 내용
04_테스트_결과.md: 테스트 결과 및 추출 정확도 분석