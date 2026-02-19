# 표 인식 시스템 사용 가이드

금융거래조회서 이미지에서 표를 자동으로 추출하는 시스템입니다.

## 빠른 시작

### 전체 이미지 처리
```powershell
.venv\Scripts\python.exe src/main.py --input test/image --output output
```

### 단일 이미지 처리
```powershell
.venv\Scripts\python.exe src/main.py --input test/image/bank_audit_letter-0003.jpg --output output
```

## 출력 결과

각 표마다 3가지 형식으로 저장됩니다:
- **CSV**: 간단한 데이터 분석용
- **Excel**: 원본 표 구조 유지
- **JSON**: API 연동 및 프로그래밍 처리용

## 자세한 문서

- [전체 사용 가이드](file:///c:/gs/accountant_pwd/old/audit-inquiry-automation1/docs/README.md)
- [구현 완료 보고서](file:///C:/Users/User/.gemini/antigravity/brain/fda01b32-acbe-4e64-8691-11613807e2a7/walkthrough.md)
