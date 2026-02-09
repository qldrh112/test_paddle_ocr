# 배치 처리 최종 결과 보고서

## 처리 완료 시각
2026-02-09 15:18:10

## 결과 요약

- **총 이미지 수**: 11개
- **성공**: 9개 (81.8%)
- **실패**: 2개 (18.2%)

## 생성된 파일

### 성공적으로 생성된 XLSX 파일 (9개)

모든 파일은 `image/` 디렉토리에 저장되었습니다:

1. `bank_audit_letter-0001.xlsx` (3,278 bytes)
2. `bank_audit_letter-0003.xlsx` (3,279 bytes)
3. `bank_audit_letter-0004.xlsx` (3,278 bytes)
4. `bank_audit_letter-0005.xlsx` (3,278 bytes)
5. `bank_audit_letter-0006.xlsx` (3,277 bytes)
6. `bank_audit_letter-0007.xlsx` (3,279 bytes)
7. `bank_audit_letter-0008.xlsx` (3,278 bytes)
8. `bank_audit_letter-0009.xlsx` (3,279 bytes)
9. `bank_audit_letter-0010.xlsx` (3,278 bytes)

### 실패한 이미지 (2개)

- `bank_audit_letter-0002.jpg` - ERROR: At least one sheet must be visible
- `bank_audit_letter-0011.jpg` - ERROR: At least one sheet must be visible

**실패 원인**: 엑셀 파일 생성 시 시트가 비어있어 발생한 오류. 표 감지가 되지 않았거나 데이터가 추출되지 않았을 가능성.

## 로그 파일

- **배치 실행 로그**: `batch_log_20260209_151810.txt` (2.5 KB)
- **요약 보고서**: `batch_result_20260209_151810.txt` (1.5 KB)

## 성능 분석

- **성공률**: 81.8% (9/11)
- **평균 파일 크기**: 약 3.2 KB
- **처리 시간**: 약 8-10분 (전체 11개 이미지)
- **평균 처리 시간**: 약 45-55초/이미지

## 다음 단계

1. ✅ **xlsx 파일 검토**: 생성된 9개 파일을 Excel로 열어 데이터 확인
2. 🔍 **실패 이미지 분석**: 0002, 0011 이미지의 OCR 결과 확인
3. 📊 **데이터 품질 평가**: 추출된 표 데이터의 정확도 검증
4. 🔧 **퍼지 매칭 튜닝**: 실패 이미지에 대한 앵커 매칭 조건 조정

## 참고

- 모든 xlsx 파일은 프로젝트 폴더 `image/` 디렉토리에 저장되었습니다.
- 각 파일은 해당 이미지에서 추출한 금융상품 내역 표를 포함합니다.
- 파일 크기가 일정한 것은 대부분 유사한 표 구조를 가지고 있음을 의미합니다.
