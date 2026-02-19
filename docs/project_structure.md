# 프로젝트 구조 및 코드 설명

이 문서는 프로젝트의 폴더 구조와 주요 코드 파일에 대한 설명을 담고 있습니다.

## 1. 폴더 구조 (Directory Structure)

```
project_root/
├── .venv_easyocr_fix/      # EasyOCR 실행을 위한 가상환경 (Python 3.10, PyTorch CUDA 12.1)
├── .venv_paddle_fix/       # PaddleOCR 실행을 위한 가상환경 (Python 3.10, PaddlePaddle 2.6.2 CPU)
├── .venv_tesseract_fix/    # Tesseract 실행을 위한 가상환경
├── docs/                   # 프로젝트 문서 및 산출물 (.md)
├── output/                 # OCR 결과 및 로그 저장소
│   ├── easyocr_results/    # EasyOCR 배치 테스트 결과 (.json)
│   ├── paddleocr_results/  # PaddleOCR 배치 테스트 결과 (.json)
│   ├── tesseract_results/  # Tesseract 배치 테스트 결과 (.json)
│   └── comparison/         # 프레임워크 비교 결과 (.csv)
├── src/                    # 메인 애플리케이션 소스 코드
│   ├── main.py             # 표 추출기 실행 메인 스크립트
│   └── table_extractor/    # 표 추출 로직 모듈 (OpenCV/Tesseract 기반)
└── test/                   # 테스트 스크립트 및 디버깅 도구
    ├── assets/             # 테스트용 정답 레이블 (sheet1_label.csv 등)
    ├── image/              # 테스트용 이미지 파일
    ├── test_easyocr_batch.py    # EasyOCR 배치 성능 테스트
    ├── test_paddleocr_batch.py  # PaddleOCR 배치 성능 테스트
    ├── test_tesseract_batch.py  # Tesseract 배치 성능 테스트
    ├── compare_all_frameworks.py # 3개 프레임워크 성능 비교 스크립트
    ├── debug_paddle.py          # PaddleOCR 디버깅용 스크립트
    └── check_paddle_gpu.py      # Paddle GPU 설정 확인 스크립트
```

## 2. 주요 코드 설명 (Key Files)

### `src/main.py`
- **역할**: 이미지에서 표를 추출하고 CSV, Excel, JSON 형식으로 저장하는 메인 프로그램입니다.
- **기능**:
    - `table_extractor` 패키지를 사용하여 이미지 내의 표 영역을 감지하고 텍스트를 인식합니다.
    - 단일 파일 또는 디렉토리 단위 처리를 지원합니다.
    - 실행 인자로 입력 경로(`--input`)와 출력 경로(`--output`)를 받습니다.

### `test/test_paddleocr_batch.py`
- **역할**: PaddleOCR을 사용하여 테스트 이미지를 일괄 처리하고 성능을 측정합니다.
- **주요 로직**:
    - `test/image` 폴더의 모든 이미지를 읽어 OCR을 수행합니다.
    - 각 이미지의 처리 시간, 감지된 텍스트 영역 수, 평균 신뢰도(Confidence)를 계산합니다.
    - 결과는 `output/paddleocr_results/paddleocr_summary.json`에 저장됩니다.
    - **설정**: 안정성을 위해 현재 CPU 모드(`paddlepaddle==2.6.2`)와 `PP-OCRv3` 모델을 사용합니다.

### `test/test_easyocr_batch.py`
- **역할**: EasyOCR을 사용하여 테스트 이미지를 일괄 처리합니다.
- **설정**: GPU 가속(`CUDA 12.x`)을 활성화하여 빠른 속도(~1.7s/장)를 보여줍니다.

### `test/compare_all_frameworks.py`
- **역할**: PaddleOCR, EasyOCR, Tesseract의 배치 테스트 결과(JSON)를 읽어 비교 분석합니다.
- **출력**: `output/comparison/comparison_3_frameworks.csv` 파일로 통합된 성능 지표를 저장합니다.

### `test/compare_with_labels.py` (신규)
- **역할**: OCR 결과(JSON)와 정답 레이블(CSV)을 비교하여 정확도를 측정합니다.
- **로직**:
    - `test/assets/sheet1_label.csv`의 데이터(계좌번호, 금액 등)가 OCR 결과에 포함되어 있는지 확인합니다.
    - 문자열 유사도 또는 포함 여부를 기반으로 Recall(재현율)을 계산합니다.
