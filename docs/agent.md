의존성 관리는 poetry로 한다.
반드시 작업에 대한 문서화를 진행한다.
주석은 한국어로 작성하며, 구현 과정에 대한 산출물은 *.md 파일로 하고, 내용은 한국어로 한다.

## 폴더 구조 및 테스트 대상
- 표가 있는 이미지: `public/image/bank_audit_letter-0003, 0004, 0005, 0006, 0008, 0009.jpg`
- 벤치마크 핵심 타겟: `0003(sheet1), 0004(sheet2), 0006(sheet5), 0009(sheet9)`
- 정답 레이블 위치: `public/label/`
- 나머지 이미지에서는 표 추출을 최소화하거나 무시해야 함.

## 금융거래조회서 데이터 추출 자동화(Audit-OCR) 프로젝트 문제 정의
1. **데이터 신뢰성 및 무결성 결여 (Reliability Gap)**: 수동 입력 시 발생하는 휴먼 에러 차단 및 자동 검증 체계 구축 필요.
2. **비정형 서식의 파편화 (Template Complexity)**: 은행별/시점별로 다른 양식에 대응 가능한 유연한 추출 로직 필요.
3. **엄격한 보안 및 규제 준수 (Security Constraints)**: 외부 클라우드 API(Google Vision 등) 사용 금지, 100% 로컬 환경 구동 필수.
4. **업무 효율성 증대**: 반복적인 타이핑 업무를 자동화하여 회계 인력의 고부가가치 판단 시간 확보.

### 주요 벤치마크 대상
- PaddleOCR (PP-StructureV2)
- EasyOCR (PyTorch 기반)
- Tesseract OCR (Baseline)

### 표 헤더 가이드 (정답 데이터 기준)
- **표1**: 금융상품의 종류, 계좌번호, 금액, 연이자율, 최종이자지급일, 만기일, 인출제한 등
- **표2**: 대출 종류, 약정한도액, 대출금액, 대출일, 최종만기일, 연이자율, 최종이자지급일, 상환방법, 담보 보증 및 관련 약정
- **표5**: 내용, 연대보증 등을 제공받은 회사(개인), 연대 보증 등의 대상 여신, 연대보증 등의 한도, 담보 제공한 자산
- **표9**: 구분, 담보 보증의 내용, 소유자(제공자), 감정금액, 설정금액, 설정순위, 선순위 설정 금액

### 의존성 실행 방법 (가상환경)
- **Tesseract**: `.\.venv_tesseract\Scripts\activate`
- **EasyOCR**: `.\.venv_easyocr\Scripts\activate`
- **PaddleOCR**: `.\.venv_paddle\Scripts\activate`

### 완료된 작업 (Milestones)
- [x] 모든 프레임워크에 대한 이미지-레이블 매핑 기반 벤치마크 수행
- [x] `scripts/compare_results.py`를 통한 F1-Score 정밀 측정 및 분석
- [x] 표 영역 크롭(Preprocessing)을 통한 성능 개선 검증
- [x] 종합 결과 보고서(`Walkthrough.md`) 및 가이드 최신화