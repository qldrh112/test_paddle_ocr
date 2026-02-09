"""
디버그용 스크립트: 앵커 매칭 테스트

앵커 패턴 변경으로 인한 매칭 실패를 디버깅
"""

from table_schema import BANK_INQUIRY_SCHEMAS

# 테스트 케이스: 실제 OCR 결과 (pipeline_debug 로그에서 가져옴)
test_cases = [
    # 원래 성공한 케이스
    "종류1계좌번호2능룡Yl야룡든호9르주록콩등7",
    # 공백 제거 버전
    "종류1 계좌번호2 금액",
    # 정상적인 헤더
    "금융상품의종류 계좌번호 금액 연이자율 만기일",
    # 키워드만
    "금융상품 종류 계좌번호 금액",
]

print("=" * 80)
print("앵커 매칭 테스트")
print("=" * 80)

for i, text in enumerate(test_cases, 1):
    print(f"\n[테스트 {i}] {text}")
    print("-" * 80)
    
    for schema in BANK_INQUIRY_SCHEMAS:
        result = schema.matches_anchor(text)
        print(f"  {schema.table_name}: {'✅ 매칭' if result else '❌ 실패'}")
