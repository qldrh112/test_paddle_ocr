"""
파이프라인 디버그 분석 스크립트
각 단계별 토큰 수와 데이터를 추적하여 문제점 파악
"""

from pathlib import Path
from PIL import Image
from datetime import datetime

from config import Config
from engine import get_engine
from postprocessor import FinancialPatternNormalizer, filter_low_confidence
from line_builder import LineBuilder
from chunker import Chunker
from table_schema import BANK_INQUIRY_SCHEMAS

# 디버그 모드 활성화
Config.DEBUG_MODE = True

# 테스트 이미지 (Google Gemini가 성공한 이미지)
image_path = "image/bank_audit_letter-0003.jpg"

# 출력 파일
output_file = f"pipeline_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def log(msg, file=None):
    """화면과 파일에 동시 출력"""
    print(msg)
    if file:
        file.write(msg + "\n")

with open(output_file, "w", encoding="utf-8") as f:
    log("=" * 80, f)
    log("파이프라인 디버그 분석", f)
    log("=" * 80, f)
    log("", f)
    
    # 이미지 로드
    img = Image.open(image_path)
    page_height = img.size[1]
    log(f"이미지: {image_path}", f)
    log(f"크기: {img.size}, 페이지 높이: {page_height}", f)
    log("", f)
    
    # ========================================================================
    # Stage 1: OCR 추출
    # ========================================================================
    log("=" * 80, f)
    log("[Stage 1] OCR 추출", f)
    log("=" * 80, f)
    
    engine = get_engine()
    tokens = engine.extract(img)
    
    log(f"추출된 토큰 수: {len(tokens)}", f)
    log("", f)
    log("샘플 토큰 (처음 10개):", f)
    for idx, (y, x, text, conf) in enumerate(tokens[:10], 1):
        log(f"  {idx:2d}. [{conf:.3f}] {text:30s} (y={y:6.1f}, x={x:6.1f})", f)
    log("", f)
    
    # ========================================================================
    # Stage 2: 후처리 - 금액-통화 병합
    # ========================================================================
    log("=" * 80, f)
    log("[Stage 2] 후처리: 금액-통화 병합", f)
    log("=" * 80, f)
    
    normalizer = FinancialPatternNormalizer()
    merged_tokens = normalizer.merge_amount_currency(tokens, page_height)
    
    log(f"병합 후 토큰 수: {len(merged_tokens)}", f)
    log(f"토큰 수 변화: {len(tokens)} → {len(merged_tokens)} (감소: {len(tokens) - len(merged_tokens)})", f)
    log("", f)
    
    # ========================================================================
    # Stage 3: 신뢰도 필터링
    # ========================================================================
    log("=" * 80, f)
    log("[Stage 3] 신뢰도 필터링", f)
    log("=" * 80, f)
    
    filtered_tokens = filter_low_confidence(merged_tokens)
    low_conf_count = sum(1 for _, _, _, needs_review in filtered_tokens if needs_review)
    
    log(f"필터링 후 토큰 수: {len(filtered_tokens)}", f)
    log(f"검토 필요 토큰: {low_conf_count}/{len(filtered_tokens)}", f)
    log("", f)
    
    # ========================================================================
    # Stage 4: 행 그룹화
    # ========================================================================
    log("=" * 80, f)
    log("[Stage 4] 행 그룹화 (LineBuilder)", f)
    log("=" * 80, f)
    
    line_builder = LineBuilder(page_height=page_height)
    rows = line_builder.build_lines(filtered_tokens)
    
    log(f"그룹화된 행 수: {len(rows)}", f)
    log("", f)
    log("행별 토큰 수:", f)
    for idx, row in enumerate(rows[:20], 1):
        row_text = " ".join([token[2] for token in row])
        log(f"  행 {idx:2d}: {len(row):2d}개 토큰 - {row_text[:60]}", f)
    log("", f)
    
    # ========================================================================
    # Stage 5: 표 영역 분할 (Chunker)
    # ========================================================================
    log("=" * 80, f)
    log("[Stage 5] 표 영역 분할 (Chunker)", f)
    log("=" * 80, f)
    
    # 앵커 패턴 매칭 테스트
    log("앵커 패턴 매칭 테스트:", f)
    for idx, row in enumerate(rows[:30], 1):
        row_text = " ".join([token[2] for token in row])
        
        matched_schema = None
        for schema in BANK_INQUIRY_SCHEMAS:
            if schema.matches_anchor(row_text):
                matched_schema = schema
                break
        
        if matched_schema:
            log(f"  ⚓ 행 {idx:2d}: {row_text[:50]} → {matched_schema.table_name}", f)
    log("", f)
    
    chunker = Chunker()
    data_by_table = chunker.split_into_chunks(rows)
    
    log(f"감지된 표 수: {len(data_by_table)}", f)
    for table_name, table_rows in data_by_table.items():
        log(f"  - {table_name}: {len(table_rows)}행", f)
        log(f"    첫 행: {' '.join([t[2] for t in table_rows[0]])[:60] if table_rows else '없음'}", f)
    log("", f)
    
    # ========================================================================
    # 요약
    # ========================================================================
    log("=" * 80, f)
    log("파이프라인 요약", f)
    log("=" * 80, f)
    log(f"1. OCR 추출:        {len(tokens)}개 토큰", f)
    log(f"2. 금액-통화 병합:   {len(merged_tokens)}개 토큰", f)
    log(f"3. 신뢰도 필터링:    {len(filtered_tokens)}개 토큰 ({low_conf_count}개 검토 필요)", f)
    log(f"4. 행 그룹화:        {len(rows)}개 행", f)
    log(f"5. 표 영역 분할:     {len(data_by_table)}개 표", f)
    log("", f)
    
    if len(data_by_table) == 0:
        log("⚠️  문제: 표가 감지되지 않았습니다!", f)
        log("", f)
        log("가능한 원인:", f)
        log("  1. 앵커 패턴이 OCR 결과와 일치하지 않음", f)
        log("  2. 퍼지 매칭이 작동하지 않음", f)
        log("  3. 행 그룹화 과정에서 데이터 손실", f)
    
    log("=" * 80, f)
    log(f"분석 완료: {output_file}", f)
    log("=" * 80, f)

print(f"\n✅ 디버그 분석 완료: {output_file}")
