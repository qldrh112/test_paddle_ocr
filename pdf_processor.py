"""
PDF 다중 페이지 처리 모듈

⭐ 핵심 기능:
- PDF를 페이지별 이미지로 변환
- 각 페이지에서 표 추출
- 하나의 Excel 파일로 통합 (페이지별 시트 또는 표별 병합)
"""

from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image

from engine import get_engine
from postprocessor import FinancialPatternNormalizer, filter_low_confidence
from line_builder import LineBuilder
from chunker import Chunker
from excel_writer import write_tables_to_excel
from table_schema import BANK_INQUIRY_SCHEMAS


def pdf_to_images(pdf_path: str, dpi: int = 200) -> List[Image.Image]:
    """
    PDF를 페이지별 이미지로 변환
    
    Args:
        pdf_path: PDF 파일 경로
        dpi: 이미지 해상도 (기본 200)
    
    Returns:
        페이지별 PIL 이미지 리스트
    
    Raises:
        ImportError: pdf2image가 설치되지 않은 경우
        FileNotFoundError: PDF 파일이 없는 경우
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError(
            "pdf2image 라이브러리가 필요합니다. 설치: poetry add pdf2image"
        )
    
    images = convert_from_path(pdf_path, dpi=dpi)
    print(f"✅ PDF 변환 완료: {len(images)}페이지")
    return images


def process_pdf_to_unified_excel(
    pdf_path: str,
    output_excel_path: str = None,
    merge_same_tables: bool = False
) -> dict:
    """
    PDF 전체 페이지를 처리하여 하나의 Excel 파일로 통합
    
    ⭐ 두 가지 모드:
    1. merge_same_tables=False: 페이지별 시트 (P1_금융상품_내역, P2_금융상품_내역, ...)
    2. merge_same_tables=True: 표별 병합 (금융상품_내역에 모든 페이지 데이터 통합)
    
    Args:
        pdf_path: 입력 PDF 경로
        output_excel_path: 출력 Excel 경로 (None이면 자동 생성)
        merge_same_tables: 동일 표를 병합할지 여부
    
    Returns:
        처리 결과 정보
            {
                "input_path": str,
                "output_path": str,
                "pages": int,
                "sheet_count": int,
                "tables": List[str]
            }
    
    Raises:
        FileNotFoundError: PDF 파일이 없는 경우
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    
    # 출력 경로 자동 생성
    if output_excel_path is None:
        output_excel_path = pdf_path.with_suffix('.xlsx')
    
    print("=" * 80)
    print("PDF 다중 페이지 통합 처리")
    print("=" * 80)
    print(f"입력: {pdf_path}")
    print(f"출력: {output_excel_path}")
    print(f"병합 모드: {'표별 병합' if merge_same_tables else '페이지별 시트'}")
    print()
    
    # 1. PDF → 이미지 변환
    images = pdf_to_images(str(pdf_path))
    
    # 2. 각 페이지 처리
    all_tables = {}
    engine = get_engine()
    
    for page_num, img in enumerate(images, 1):
        print(f"[페이지 {page_num}/{len(images)}] 처리 중...")
        
        # OCR + 후처리 파이프라인
        tokens = engine.extract(img)
        print(f"  OCR: {len(tokens)}개 토큰 추출")
        
        normalizer = FinancialPatternNormalizer()
        merged_tokens = normalizer.merge_amount_currency(tokens, img.size[1])
        filtered_tokens = filter_low_confidence(merged_tokens)
        
        # 행 그룹화 + 표 분할
        line_builder = LineBuilder(page_height=img.size[1])
        rows = line_builder.build_lines(filtered_tokens)
        print(f"  행 그룹화: {len(rows)}개 행")
        
        chunker = Chunker()
        page_tables = chunker.split_into_chunks(rows)
        print(f"  표 감지: {len(page_tables)}개")
        
        # 3. 표 이름 처리 (병합 또는 페이지별 시트)
        for table_name, table_rows in page_tables.items():
            if merge_same_tables:
                # 동일 표는 하나의 시트로 병합
                if table_name not in all_tables:
                    all_tables[table_name] = []
                all_tables[table_name].extend(table_rows)
                print(f"    ✓ {table_name}: {len(table_rows)}행 추가 (누적: {len(all_tables[table_name])}행)")
            else:
                # 페이지별로 별도 시트 생성
                sheet_name = f"P{page_num}_{table_name}"
                all_tables[sheet_name] = table_rows
                print(f"    ✓ {sheet_name}: {len(table_rows)}행")
        print()
    
    # 4. 통합 Excel 생성
    print(f"[Excel 생성] 총 {len(all_tables)}개 시트")
    
    # 헤더 정보 준비
    headers_by_table = {}
    for schema in BANK_INQUIRY_SCHEMAS:
        for table_key in all_tables.keys():
            if schema.table_name in table_key:
                headers_by_table[table_key] = schema.headers
    
    sheet_count = write_tables_to_excel(all_tables, output_excel_path, headers_by_table)
    
    print()
    print("=" * 80)
    print("✅ PDF 처리 완료")
    print("=" * 80)
    print(f"입력: {pdf_path}")
    print(f"출력: {output_excel_path}")
    print(f"처리된 페이지 수: {len(images)}")
    print(f"생성된 시트 수: {sheet_count}")
    print("=" * 80)
    
    return {
        "input_path": str(pdf_path),
        "output_path": str(output_excel_path),
        "pages": len(images),
        "sheet_count": sheet_count,
        "tables": list(all_tables.keys())
    }


if __name__ == "__main__":
    # 테스트용
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        merge = len(sys.argv) > 2 and sys.argv[2].lower() == "merge"
        result = process_pdf_to_unified_excel(pdf_file, merge_same_tables=merge)
        print(f"\n✅ 성공: {result['output_path']}")
    else:
        print("사용법: python pdf_processor.py <PDF파일> [merge]")
        print("  예제: python pdf_processor.py bank_audit_letter.pdf")
        print("  예제: python pdf_processor.py bank_audit_letter.pdf merge")
