# PaddleOCR 금융거래조회서 표 추출 프로그램

> 전처리-OCR-후처리 3단계 파이프라인으로 인식률과 데이터 무결성을 향상시킨 금융거래조회서 표 추출 시스템

## 주요 기능

### 🔧 전처리 (Preprocessing)
- **이진화**: 적응형 가우시안 임계값으로 텍스트와 배경 분리
- **노이즈 제거**: 모폴로지 연산으로 스캔 노이즈 제거
- **Deskewing**: Hough Line Transform으로 문서 기울어짐 자동 보정
- **대비 향상**: CLAHE로 텍스트 선명도 개선

### 🤖 OCR 엔진
- **PaddleOCR**: 한국어 최적화 OCR 엔진
- **GPU 자동 감지**: CUDA 사용 가능 시 자동 GPU 모드
- **Confidence 보존**: 신뢰도 정보를 후처리 단계로 전달

### ✨ 후처리 (Postprocessing)
- **계좌번호 복원**: 분할된 토큰 병합 (예: `416-` `1241` `7568-` `9국` → `416-1241-7568-93`)
- **날짜 정규화**: `2412국` → `2024-12-31`
- **이자율 소수점 복원**: `360%` → `3.6%`
- **금액-통화 병합**: `602418268` `KRW` → `602,418,268 KRW`
- **통화 오인식 보정**: `KRV`, `U5` → `KRW`, `USD`
- **신뢰도 필터링**: 낮은 confidence 토큰에 검토 플래그

## 설치

### 1. 의존성 설치

```bash
poetry install
```

### 2. 환경 설정 (선택사항)

환경변수로 설정을 조정할 수 있습니다:

```bash
# .env 파일 생성 (또는 직접 설정)
OCR_CONFIDENCE_THRESHOLD=0.7      # 신뢰도 임계값
USE_GPU=True                       # GPU 사용 여부
ENABLE_DESKEWING=True              # Deskewing 활성화
DEBUG_MODE=False                   # 디버그 모드
```

## 사용 방법

### 전체 파이프라인 실행 (권장)

```bash
poetry run python main.py
```

이 방법은 다음 7단계를 자동으로 실행합니다:
1. 이미지 로드
2. OCR 추출 (전처리 자동 적용)
3. 후처리 (금액-통화 병합)
4. 신뢰도 필터링
5. 행 그룹화
6. 표 영역 분할
7. 엑셀 파일 생성

### OCR 테스트만 실행

```bash
poetry run python test_ocr.py
```

### Python 코드에서 사용

```python
from PIL import Image
from engine import get_engine
from postprocessor import FinancialPatternNormalizer, filter_low_confidence

# 1. 이미지 로드
img = Image.open("bank_audit_letter_1page.png")

# 2. OCR 추출
engine = get_engine()
tokens = engine.extract(img)  # [(y, x, text, confidence), ...]

# 3. 후처리: 금액-통화 병합
normalizer = FinancialPatternNormalizer()
merged = normalizer.merge_amount_currency(tokens,  page_height=img.size[1])

# 4. 신뢰도 필터링
filtered = filter_low_confidence(merged)  # [(y, x, text, needs_review), ...]
```

## 프로젝트 구조

```
audit-inquiry-automation1/
├── config.py              # 시스템 설정 중앙 관리
├── exceptions.py          # 예외 클래스 정의
├── preprocessor.py        # 이미지 전처리 모듈
├── engine.py              # PaddleOCR 래퍼 엔진
├── postprocessor.py       # 금융 패턴 정규화
├── line_builder.py        # 행 그룹화 (정규화된 좌표 기반)
├── table_schema.py        # 표 스키마 및 앵커 패턴 정의
├── chunker.py             # 표 영역 분할
├── excel_writer.py        # 엑셀 출력
├── main.py                # 전체 파이프라인 통합
├── test_ocr.py            # OCR 테스트 스크립트
├── pyproject.toml         # Poetry 의존성 관리
└── bank_audit_letter_1page.png  # 샘플 이미지
```

## 성능 최적화

### Deskewing 성능 개선
- 고해상도 이미지는 50% 축소하여 각도 계산 (`DESKEW_RESIZE_FACTOR`)
- 계산된 회전 행렬을 원본 이미지에 적용

### 좌표 정규화
- 모든 좌표를 0~1000으로 정규화하여 해상도 독립적 거리 측정
- 다양한 스캐너 환경에서 일관된 행 판단

## 설정 파라미터

`config.py`에서 다음 파라미터를 조정할 수 있습니다:

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `OCR_CONFIDENCE_THRESHOLD` | 0.7 | 신뢰도 임계값 |
| `NORMALIZED_PAGE_HEIGHT` | 1000.0 | 좌표 정규화 기준 |
| `ENABLE_DESKEWING` | True | Deskewing 활성화 |
| `DESKEW_ANGLE_THRESHOLD` | 0.5 | 보정 최소 각도(도) |
| `DESKEW_RESIZE_FACTOR` | 0.5 | 각도 계산용 축소 비율 |

## 주의사항

### 이자율 복원
- `normalize_interest_rate()`는 **이자율 필드**에서만 사용하세요
- 연체이자율 등에 잘못 적용되지 않도록 컨텍스트 확인 필요

### A1/A2 경로 분리
- 디지털 PDF(A2)와 스캔본(A1)을 엄격히 분리 처리
- 향후 이미지 객체 비율을 보조 지표로 사용 권장

## 문제 해결

### ModuleNotFoundError: No module named 'cv2'

```bash
poetry install  # 의존성 재설치
```

### GPU 관련 에러

```bash
# CPU 모드로 강제 실행
OCR_FORCE_CPU=True poetry run python test_ocr.py
```

### 디버그 모드 활성화

```python
# test_ocr.py 상단에 추가
Config.DEBUG_MODE = True
Config.SAVE_OCR_DEBUG_IMAGES = True
```

디버그 이미지는 `debug_output/` 폴더에 저장됩니다.

## 참고 자료

- [PaddleOCR 공식 문서](https://github.com/PaddlePaddle/PaddleOCR)
- [OpenCV Documentation](https://docs.opencv.org/)
- [구현 계획서](https://github.com/user/brain/.../implementation_plan.md)

## 라이선스

MIT License
