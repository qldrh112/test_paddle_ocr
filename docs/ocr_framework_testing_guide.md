# 다른 OCR 프레임워크 테스트 가이드

**작성일**: 2026-02-17

---

## 개요

다른 OCR 프레임워크(EasyOCR, PaddleOCR 등)는 의존성 충돌이 발생할 수 있으므로, 별도의 Poetry 가상 환경에서 테스트하는 것을 권장합니다.

---

## 방법 1: 별도 Poetry 프로젝트 생성

### 1. 새 프로젝트 디렉토리 생성

```powershell
mkdir ocr_comparison_test
cd ocr_comparison_test
```

### 2. Poetry 초기화

```powershell
poetry init
# Python 버전: 3.10
# 기본 의존성: 건너뛰기
```

### 3. 테스트할 OCR 프레임워크 설치

#### EasyOCR 테스트

```powershell
poetry add easyocr torch torchvision
poetry add opencv-python pillow
```

#### PaddleOCR 테스트

```powershell
poetry add paddlepaddle paddleocr
poetry add opencv-python pillow
```

### 4. 테스트 스크립트 작성

```python
# test_ocr.py
import easyocr  # 또는 from paddleocr import PaddleOCR
import time

def test_easyocr(image_path):
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    start = time.time()
    results = reader.readtext(image_path)
    elapsed = time.time() - start
    
    print(f"처리 시간: {elapsed:.2f}초")
    print(f"추출된 텍스트 영역: {len(results)}개")
    
    for bbox, text, confidence in results[:10]:
        print(f"{confidence:.3f}: {text}")

if __name__ == "__main__":
    test_easyocr("path/to/test/image.jpg")
```

### 5. 실행

```powershell
poetry run python test_ocr.py
```

---

## 방법 2: Docker 컨테이너 사용

### Dockerfile 예시

```dockerfile
FROM python:3.10-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install poetry

WORKDIR /app

# 의존성 설치
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# 애플리케이션 복사
COPY . .

CMD ["poetry", "run", "python", "test_ocr.py"]
```

### 빌드 및 실행

```powershell
docker build -t ocr-test .
docker run -v ${PWD}/test_images:/app/images ocr-test
```

---

## 방법 3: Conda 환경 사용

### 1. Conda 환경 생성

```powershell
conda create -n ocr_test python=3.10
conda activate ocr_test
```

### 2. 패키지 설치

```powershell
pip install easyocr torch torchvision
# 또는
pip install paddlepaddle paddleocr
```

### 3. 테스트

```powershell
python test_ocr.py
```

---

## 권장 테스트 항목

### 1. 성능 측정

- **초기화 시간**: OCR Reader 생성 시간
- **처리 시간**: 이미지당 추출 시간
- **메모리 사용량**: 프로세스 메모리

### 2. 정확도 측정

- **한국어 인식률**: 한글 텍스트 정확도
- **숫자 인식률**: 금액, 계좌번호 등
- **특수문자 인식**: %, ·, - 등

### 3. 표 구조 인식

- **표 감지율**: 표를 찾는 비율
- **셀 분리 정확도**: 셀 경계 인식
- **헤더 인식**: 첫 행 인식 품질

---

## 비교 기준표

| 항목 | Tesseract OCR | EasyOCR | PaddleOCR |
|------|---------------|---------|-----------|
| **초기화 시간** | < 1초 | 5-10초 | 3-5초 |
| **처리 시간** | 5초/이미지 | ? | ? |
| **한국어 정확도** | 85-90% | ? | ? |
| **표 구조 인식** | ✓ (img2table) | ? | ✓ (내장) |
| **설치 난이도** | 쉬움 | 어려움 | 보통 |
| **의존성** | 적음 | 많음 (PyTorch) | 많음 |
| **GPU 지원** | ❌ | ✓ | ✓ |

---

## 현재 상황 요약

### ✅ Tesseract OCR (현재 사용 중)

**장점**:
- 안정적이고 가볍다
- 한국어 지원 양호 (85-90%)
- 설치 및 관리 용이
- img2table과 잘 통합됨

**단점**:
- GPU 가속 없음
- 복잡한 레이아웃에서 정확도 낮을 수 있음

### ⚠️ EasyOCR

**상태**: 설치 성공, 실행 실패 (DLL 오류)

**문제**:
- PyTorch 의존성 복잡
- Windows에서 DLL 문제
- 초기화 시간 오래 걸림

### 🔍 PaddleOCR

**상태**: 미테스트

**예상**:
- 표 인식에 특화된 모델 제공
- 한국어 지원 양호
- 의존성 중간 정도

---

## 최종 권장사항

### 현재 시스템 유지

**Tesseract OCR + 표 헤더 고정** 조합으로 실용적인 수준의 성능을 달성했으므로, 별도의 OCR 프레임워크 테스트는 **선택사항**입니다.

### 추가 테스트가 필요한 경우

1. **별도 Poetry 프로젝트** 생성 (의존성 격리)
2. **소규모 테스트** 스크립트 작성
3. **성능 비교** 후 필요시 통합
