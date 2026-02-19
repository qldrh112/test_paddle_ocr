# OCR 프레임워크 벤치마크 실행 가이드

이 프로젝트는 PaddleOCR, EasyOCR, Tesseract의 성능을 독립된 환경에서 테스트할 수 있도록 구성되어 있습니다.

## 1. 사전 준비 (Virtual Environments)
각 프레임워크는 의존성 충돌을 방지하기 위해 별도의 가상환경을 사용합니다. 프로젝트 루트에 아래 이름으로 가상환경이 구축되어 있어야 합니다.

- **EasyOCR**: `.venv_easyocr`
- **PaddleOCR**: `.venv_paddle`
- **Tesseract**: `.venv_tesseract`

## 2. 테스트 데이터 준비
- 원본 이미지: `test/image/tables/` (0003, 0004, 0006, 0009.jpg)
- 정답 레이블: `test/assets/` (sheet1, 2, 5, 9_label.csv)

## 3. 실행 단계

### 단계 1: 이미지 전처리 (표 영역 크롭)
인식률 극대화를 위해 표 영역만 먼저 추출합니다.
```powershell
.venv_paddle/Scripts/python scripts/preprocess_crops.py --inputs [원본이미지경로] --output_dir output/cropped
```

### 단계 2: 프레임워크별 벤치마크 실행
각 환경의 Python 인터프리터를 사용하여 스크립트를 호출합니다.

**PaddleOCR 예시:**
```powershell
.venv_paddle/Scripts/python scripts/benchmark_paddle.py --inputs [이미지경로] --outputs [결과경로]
```

**EasyOCR 예시:**
```powershell
.venv_easyocr/Scripts/python scripts/benchmark_easyocr.py --inputs [이미지경로] --outputs [결과경로]
```

**Tesseract 예시:**
```powershell
.venv_tesseract/Scripts/python scripts/benchmark_tesseract.py --inputs [이미지경로] --outputs [결과경로]
```

### 단계 3: 정확도 비교 분석
추출된 결과물과 정답지를 대조하여 성능 분석 리포트를 확인합니다.
```powershell
# 이 스크립트는 베이스라인 환경 또는 모든 라이브러리가 설치된 환경에서 실행
python scripts/compare_results.py --gt [정답CSV] --paddle [결과1] --easy [결과2] --tess [결과3]
```

## 4. 문제 해결 (Troubleshooting)
- **Numpy/DLL 오류**: EasyOCR 실행 시 DLL 오류가 발생하면 CUDA 버전과 PyTorch 버전을 확인하세요.
- **Tesseract Not Found**: 시스템 PATH에 Tesseract 설치 경로가 포함되어 있는지 확인하세요.
- **표 감지 실패**: `preprocess_crops.py`가 표를 찾지 못할 경우, 원본 이미지의 해상도나 선명도를 확인하세요.
