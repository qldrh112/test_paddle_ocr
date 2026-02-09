"""
audit-inquiry-automation1/test_improved.py

개선된 파이프라인 테스트
- 전처리 설정 완화 (이진화 비활성화)
- 퍼지 앵커 매칭 활성화
"""

from pathlib import Path
from PIL import Image

from config import Config
from engine import get_engine
from postprocessor import FinancialPatternNormalizer, filter_low_confidence
from line_builder import LineBuilder
from chunker import Chunker
from table_schema import BANK_INQUIRY_SCHEMAS

# 설정 확인
print("=" * 80)
print("개선된 파이프라인 테스트")
print("=" * 80)
print()
print("적용된 설정:")
print(f"  - 이진화: {Config.ENABLE_BINARIZATION}")
print(f"  - Deskewing: {Config.ENABLE_DESKEWING}")
print(f"  - 퍼지 앵커 매칭: {Config.ENABLE_FUZZY_ANCHOR_MATCHING}")
print(f"  - 퍼지 매칭 임계값: {Config.FUZZY_MATCH_THRESHOLD}")
print()

# 샘플 이미지
image_path = "image/bank_audit_letter-0001.jpg"

# 1. 이미지 로드
img = Image.open(image_path)
page_height = img.size[1]
print(f"이미지 크기: {img.size}")
print()

# 2. OCR 추출
print("OCR 추출 중...")
engine = get_engine()
tokens = engine.extract(img)
print(f"추출된 토큰 수: {len(tokens)}")
print()

# 3. 후처리
normalizer = FinancialPatternNormalizer()
merged_tokens = normalizer.merge_amount_currency(tokens, page_height)
filtered_tokens = filter_low_confidence(merged_tokens)
print(f"후처리 완료: {len(filtered_tokens)}개 토큰")
print()

# 4. 행 그룹화
line_builder = LineBuilder(page_height=page_height)
rows = line_builder.build_lines(filtered_tokens)
print(f"그룹화된 행 수: {len(rows)}")
print()

# 5. 첫 20개 행 출력 (퍼지 매칭 확인용)
print("첫 20개 행 내용:")
print("-" * 80)
for idx, row in enumerate(rows[:20], 1):
    row_text = " ".join([token[2] for token in row])
    
    # 퍼지 매칭 테스트
    fuzzy_match_result = ""
    for schema in BANK_INQUIRY_SCHEMAS:
        if schema.matches_anchor(row_text):
            fuzzy_match_result = f" ⚓ → {schema.table_name}"
            break
    
    print(f"{idx:2d}. {row_text[:70]}{fuzzy_match_result}")
print()

# 6. 표 영역 분할
chunker = Chunker()
data_by_table = chunker.split_into_chunks(rows)
print("=" * 80)
print(f"✅ 감지된 표 수: {len(data_by_table)}")
for table_name, table_rows in data_by_table.items():
    print(f"   - {table_name}: {len(table_rows)}행")
print("=" * 80)
