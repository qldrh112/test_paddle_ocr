실행은 `poetry run python {your_script}.py` 로 한다.
반드시 작업에 대한 문서화를 진행한다.

## 폴더 구조
- bank_audit_letter.pdf: 금융거래조회서(은행조회서의 원본)
- bank_audit_letter_1page.pdf: 금융거래조회서(은행조회서의 1페이지)
- bank_audit_letter_1page.png: 금융거래조회서(은행조회서의 1페이지를 이미지로 변환)
- label_bank_audit_letter.csv: bank_audit_letter_1page.png의 정답 레이블


bank_audit_letter-0003.jpg, bank_audit_letter-0004.jpg,bank_audit_letter-0005. jpg,bank_audit_letter-0006.jpg, bank_audit_letter-0008.jpg, bank_audit_letter-0009.jpg
에만 표가 있습니다. 나머지 이미지에서는 표를 인식하면 안 됩니다.
