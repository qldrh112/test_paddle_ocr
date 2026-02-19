# 표 인식 시스템 상세 문서 가이드

이 디렉토리는 금융거래조회서 표 인식 프로젝트의 기술 문서, 벤치마크 분석 결과, 설치 가이드를 포함하고 있습니다.

## 📄 주요 문서 리스트

| 문서명 | 주요 내용 | 비고 |
|--------|-----------|------|
| **[Walkthrough.md](Walkthrough.md)** | **최종 벤치마크 성공 보고서**. 이미지별 정확도와 개선 성과 요약. | 추천 읽기 1순위 |
| **[project_structure.md](project_structure.md)** | 전체 폴더 구조, 가상환경, 이미지/레이블 매핑 정보 설명. | 구조 파악용 |
| **[ocr_framework_testing_guide.md](ocr_framework_testing_guide.md)** | Paddle, Easy, Tesseract 각 환경별 테스트 실행 방법 가이드. | 실무 운영용 |
| **[Ocr_Accuracy_Analysis.md](Ocr_Accuracy_Analysis.md)** | 정확도 측정 알고리즘(F1-Score, 유사도 매칭) 상세 설명. | 분석 기준용 |
| **[Tesseract_Installation_Guide.md](Tesseract_Installation_Guide.md)** | Tesseract 엔진 및 한국어 언어 팩 설치 가이드. | 환경 구축용 |

## 📁 주요 폴더 역할
- `scripts/`: 실제 OCR 실행 및 성능 분석 스크립트 모음.
- `test/assets/`: 정확도 비교를 위한 정답(Ground Truth) 데이터.
- `output/cropped/`: 전처리 과정을 통해 추출된 안정적인 표 이미지 저장소.

## 📊 현재 상태 요약
- **베스트 솔루션**: Layout Detection(Paddle) + 메인 분석(EasyOCR) 조합이 가장 우수한 성능을 보임.
- **정확도 성과**: 표 영역 크롭 적용 시 sheet1 기준 **F1 0.776** 달성.
