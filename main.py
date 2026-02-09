"""
audit-inquiry-automation1/main.py

전체 파이프라인 통합
PDF/이미지 → OCR → 파싱 → 엑셀 출력
"""

from pathlib import Path
from PIL import Image

from config import Config
from engine import get_engine
from postprocessor import FinancialPatternNormalizer, filter_low_confidence
from line_builder import LineBuilder
from chunker import Chunker
from table_schema import BANK_INQUIRY_SCHEMAS
from excel_writer import write_tables_to_excel


def process_image_to_excel(
    image_path: str,
    output_excel_path: str = None
) -> dict:
    """
    이미지를 OCR 처리하여 엑셀로 변환
    
    Args:
        image_path: 입력 이미지 경로
        output_excel_path: 출력 엑셀 경로 (None이면 자동 생성)
    
    Returns:
        처리 결과 정보
    """
    image_path = Path(image_path)
    
    if not image_path.exists():
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
    
    # 출력 경로 자동 생성
    if output_excel_path is None:
        output_excel_path = image_path.with_suffix('.xlsx')
    
    print("=" * 80)
    print("금융거래조회서 표 추출 파이프라인")
    print("=" * 80)
    print()
    
    # Stage 1: 이미지 로드
    print(f"[1/7] 이미지 로드: {image_path.name}")
    img = Image.open(image_path)
    page_height = img.size[1]
    print(f"      크기: {img.size}")
    print()
    
    # Stage 2: OCR 추출 (전처리 포함)
    print("[2/6] OCR 추출 (전처리 자동 적용)")
    engine = get_engine()    # OCR 실행
    tokens = engine.extract(img)
    print(f"      추출된 토큰 수: {len(tokens)}")
    
    # ⭐ 순수 OCR 접근: 후처리 최소화
    # [3/7] 신뢰도만 체크 (삭제하지 않고 플래그만 설정)
    print("\n[3/7] 신뢰도 체크")
    filtered_tokens = filter_low_confidence(tokens)
    # filter_low_confidence는 (bbox, confidence, text, needs_review) 튜플 반환
    low_conf_count = sum(1 for t in filtered_tokens if t[3])  # index 3이 needs_review
    print(f"      검토 필요 토큰: {low_conf_count}/{len(filtered_tokens)}")
    print()
    
    # [4/7] 행 그룹화 (LineBuilder)
    print("\n[4/7] 행 그룹화 (LineBuilder)")
    line_builder = LineBuilder(page_height=page_height)
    rows = line_builder.build_lines(filtered_tokens)
    print(f"      그룹화된 행 수: {len(rows)}")
    
    # [5/7] 표 영역 분할 (Chunker)
    print("\n[5/7] 표 영역 분할 (Chunker)")
    chunker = Chunker()
    tables = chunker.split_into_chunks(rows)
    print(f"      감지된 표 수: {len(tables)}")
    for table_name, table_rows in tables.items():
        print(f"        - {table_name}: {len(table_rows)}행")
    
    # [6/7] 엑셀 파일 생성
    print("\n[6/7] 엑셀 파일 생성")
    
    # 헤더 정보 준비
    headers_by_table = {}
    for schema in BANK_INQUIRY_SCHEMAS:
        if schema.table_name in tables:
            headers_by_table[schema.table_name] = schema.headers
    
    sheet_count = write_tables_to_excel(
        tables,
        output_excel_path,
        headers_by_table
    )
    print()
    
    # 결과 요약
    print("=" * 80)
    print("✅ 처리 완료")
    print("=" * 80)
    print(f"입력: {image_path}")
    print(f"출력: {output_excel_path}")
    print(f"생성된 시트 수: {sheet_count}")
    print(f"총 토큰 수: {len(tokens)}")
    print(f"검토 필요 토큰: {low_conf_count}")
    print("=" * 80)
    
    return {
        "input_path": str(image_path),
        "output_path": str(output_excel_path),
        "sheet_count": sheet_count,
        "total_tokens": len(tokens),
        "low_confidence_tokens": sum(1 for t in filtered_tokens if t[3]),
        "tables": list(tables.keys())  # data_by_table → tables로 수정
    }


if __name__ == "__main__":
    # 샘플 이미지 처리 (Google Gemini가 성공한 이미지로 테스트)
    sample_image = "image/bank_audit_letter-0003.jpg"
    
    if Path(sample_image).exists():
        result = process_image_to_excel(sample_image)
        print(f"\n✅ 성공: {result['output_path']}")
    else:
        print(f"❌ 샘플 이미지를 찾을 수 없습니다: {sample_image}")
        print("   사용법: python main.py")
