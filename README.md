# OCR 표 인식 벤치마크 프로젝트

이 프로젝트는 다양한 OCR 프레임워크(PaddleOCR, EasyOCR, Tesseract)를 활용하여 금융거래조회서와 같은 문서 내 **표(Table) 데이터를 추출**하고, 그 **정확도를 정밀하게 비교 분석**하는 시스템입니다.

## 🚀 주요 기능
- **다중 프레임워크 지원**: PaddleOCR(PP-StructureV2), EasyOCR, Tesseract 연동
- **표 영역 자동 크롭**: Layout Detection을 통한 표 영역 분리로 인식률 극대화
- **정확도 분석**: 정답 레이블(Ground Truth)과 비교하여 F1-Score 등 성능 지표 산출
- **종합 보고서 생성**: 벤치마크 결과를 바탕으로 한 시각화 및 분석 리포트 제공

## 📂 프로젝트 구조
- **`scripts/`**: 벤치마크 실행 및 모델 관리 스크립트
- **`public/label/`**: 정답 레이블(Ground Truth) 데이터셋
- **`public/image/`**: 테스트용 원본 이미지 샘플
- **`docs/`**: 상세 분석 리포트 (`Walkthrough.md`) 및 가이드

## 🛠️ 사용 방법

### 1. 전처리 (표 영역 크롭)
인식률 향상을 위해 표 영역만 먼저 추출합니다.
```powershell
.venv_paddle/Scripts/python scripts/preprocess_crops.py --inputs [이미지경로] --output_dir output/cropped
```

### 2. 벤치마크 실행 (PaddleOCR 예시)
```powershell
.venv_paddle/Scripts/python scripts/benchmark_paddle.py --inputs [이미지경로] --outputs output/result.csv
```

### 3. 정확도 비교 분석
추출된 결과물과 정답지를 비교하여 성능 수치를 확인합니다.
```powershell
python scripts/compare_results.py --gt public/label/sheet1_label.csv --paddle output/paddle_res.csv --easy output/easy_res.csv --tess output/tess_res.csv
```

## 📊 최신 테스트 결과
상세한 벤치마크 결과 및 프레임워크별 강점 분석은 아래 문서를 참고하세요.
- [👉 OCR 벤치마크 결과 상세 보고서 (Walkthrough.md)](docs/Walkthrough.md)
- [👉 프로젝트 상세 구조도 (project_structure.md)](docs/project_structure.md)

## 📌 참고 사항
- 각 OCR 엔진은 독립된 가상환경(`.venv_*`)에서 실행되어야 하며, `poetry`를 통해 의존성이 관리됩니다.
- Tesseract 사용을 위해서는 시스템에 Tesseract OCR 엔진이 별도로 설치되어 있어야 합니다.
