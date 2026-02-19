# 프로젝트 구조 및 코드 설명

이 문서는 프로젝트의 전체 폴더 구조와 주요 파일의 역할을 설명합니다.

## 1. 폴더 구조 (Project Tree)

```text
D:\WORKSPACE\TEST_PADDLE_OCR
├── .venv_easyocr/           # EasyOCR 실행을 위한 가상환경 (PyTorch CUDA 지원)
├── .venv_paddle/            # PaddleOCR(PP-StructureV2) 전용 가상환경
├── .venv_paddle_vl/         # PaddleOCR Vision-Language 모델 테스트용 가상환경
├── .venv_tesseract/         # Tesseract OCR 실행을 위한 가상환경
├── docs/                    # 벤치마크 보고서 및 각종 가이드 문서 (.md)
│   ├── Walkthrough.md       # [중요] 최신 OCR 성능 비교 및 분석 보고서
│   ├── project_structure.md # 본 문서
│   └── Tesseract_Installation_Guide.md # Tesseract 환경 구축 가이드
├── models/                  # PaddleOCR 추론에 필요한 로컬 모델 (det, rec, 구조 분석 등)
├── scripts/                 # OCR 벤치마크 및 유틸리티 스크립트
│   ├── benchmark_paddle.py      # PaddleOCR 표 추출 실행
│   ├── benchmark_easyocr.py     # EasyOCR 텍스트 추출 및 표 재구성
│   ├── benchmark_tesseract.py   # Tesseract 텍스트 추출 및 표 재구성
│   ├── compare_results.py       # 예측 결과와 정답지(GT) 비교 및 정확도 산출
│   ├── preprocess_crops.py      # 표 영역 감지 및 이미지 크롭 전처리
│   └── download_models.py       # PaddleOCR 모델 다운로드 도구
├── src/                     # 구버전 Tesseract 기반 표 추출 엔진 (Baseline)
│   ├── main.py                  # 기존 시스템 진입점
│   └── table_extractor/         # 기존 추출 로직 패키지
├── public/                  # 공용 데이터 및 테스트 자산
│   ├── image/                   # 원본 및 테스트용 이미지 저장소
│   │   └── tables/              # 벤치마크 대상 핵심 이미지 (3, 4, 6, 9번)
│   ├── label/                   # 정답 레이블 (sheet1, 2, 5, 9_label.csv)
│   └── template.xlsx            # 기본 템플릿 파일
├── output/                  # OCR 수행 결과물
│   └── cropped/                 # preprocess_crops.py로 생성된 표 크롭 이미지
├── pyproject.toml           # Poetry 의존성 관리 파일
└── README.md                # 프로젝트 메인 가이드
```

## 2. 주요 구성 요소 설명

### 벤치마크 시스템 (`scripts/`)
현재 프로젝트의 주력 기능으로, 각 OCR 프레임워크의 성능을 객관적으로 비교합니다.
*   **프레임워크별 스크립트**: 각 엔진의 특성에 맞춰 표 데이터를 CSV 형태로 추출합니다.
*   **`compare_results.py`**: 추출된 CSV와 `public/label/`의 정답지를 대조하여 성능 지표를 산출합니다.

### 데이터셋 및 자산 (`public/`)
*   **image**: 금융거래조회서 등 실제 표가 포함된 이미지 샘플입니다.
*   **label**: 각 이미지에 대한 정답(Ground Truth) 데이터가 CSV 형식으로 준비되어 있습니다.

## 3. 실행 환경
각 OCR 엔진은 독립된 가상환경(`.venv_*`)에서 구동됩니다. 실행 시 대응하는 가상환경의 Python 인터프리터를 사용하여 호출해야 합니다.
