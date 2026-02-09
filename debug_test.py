"""
audit-inquiry-automation1/debug_test.py

디버그 모드로 OCR 결과 확인
"""

from pathlib import Path
from PIL import Image

from config import Config
from engine import get_engine
from postprocessor import FinancialPatternNormalizer, filter_low_confidence
from line_builder import LineBuilder
from chunker import Chunker

# 디버그 모드 활성화
Config.DEBUG_MODE = True
Config.SAVE_OCR_DEBUG_IMAGES = True

# 샘플 이미지
image_path = "image/bank_audit_letter-0001.jpg"

print("=" * 80)
print("디버그 모드 OCR 테스트")
print("=" * 80)
print()

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
print(f"병합 후 토큰 수: {len(merged_tokens)}")
print()

# 4. 신뢰도 필터링
filtered_tokens = filter_low_confidence(merged_tokens)
print(f"필터링 후 토큰 수: {len(filtered_tokens)}")
print()

# 5. 행 그룹화
line_builder = LineBuilder(page_height=page_height)
rows = line_builder.build_lines(filtered_tokens)
print(f"그룹화된 행 수: {len(rows)}")
print()

# 6. 첫 10개 행 내용 출력
print("첫 10개 행 내용:")
print("-" * 80)
for idx, row in enumerate(rows[:10], 1):
    row_text = " ".join([token[2] for token in row])
    print(f"{idx:2d}. {row_text}")
print()

# 7. 표 영역 분할
chunker = Chunker()
data_by_table = chunker.split_into_chunks(rows)
print(f"감지된 표 수: {len(data_by_table)}")
for table_name, table_rows in data_by_table.items():
    print(f"  - {table_name}: {len(table_rows)}행")
print()

print("=" * 80)
print("디버그 완료")
print("=" * 80)
