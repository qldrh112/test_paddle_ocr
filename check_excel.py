"""
Excel 파일 내용 확인 스크립트
"""
import pandas as pd
import sys

if len(sys.argv) > 1:
    excel_file = sys.argv[1]
else:
    excel_file = "image/bank_audit_letter-0003.xlsx"

# Excel 파일 읽기
df = pd.read_excel(excel_file, sheet_name='금융상품_내역')

print("=" * 80)
print(f"Excel 파일 내용 확인: {excel_file}")
print("=" * 80)
print(f"\n총 행 수: {len(df)}")
print(f"총 열 수: {len(df.columns)}")
print(f"\n컬럼: {list(df.columns)}")
print("\n" + "=" * 80)
print("데이터 미리보기 (처음 5행):")
print("=" * 80)
print(df.head().to_string())

print("\n" + "=" * 80)
print("전체 데이터:")
print("=" * 80)
print(df.to_string())
