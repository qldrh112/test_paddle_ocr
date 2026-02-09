"""
배치 처리 스크립트 - 통합 엑셀 버전
모든 이미지의 표를 하나의 엑셀 파일에 시트별로 저장
"""

from pathlib import Path
from datetime import datetime
import sys

from main import process_image_to_excel
from excel_writer_unified import write_all_tables_to_single_excel
from engine import get_engine
from postprocessor import FinancialPatternNormalizer, filter_low_confidence
from line_builder import LineBuilder
from chunker import Chunker
from PIL import Image

def batch_process_to_unified_excel():
    """모든 이미지 파일을 처리하여 하나의 통합 엑셀 파일 생성"""
    
    # 로그 파일 준비
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"unified_batch_log_{timestamp}.txt"
    output_excel = f"all_results_{timestamp}.xlsx"
    
    log_file = open(log_path, "w", encoding="utf-8")
    
    def log(msg):
        """로그 파일에만 기록"""
        log_file.write(msg + "\n")
        log_file.flush()
    
    # 이미지 디렉토리
    image_dir = Path("image")
    
    # 모든 jpg 파일 찾기
    image_files = sorted(image_dir.glob("*.jpg"))
    
    if not image_files:
        log("[ERROR] No image files found")
        log_file.close()
        return
    
    log("=" * 80)
    log(f"Unified Batch Processing Started: {len(image_files)} images")
    log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Output: {output_excel}")
    log("=" * 80)
    log("")
    
    # 전체 데이터 수집
    all_data = {}
    success_count = 0
    fail_count = 0
    total_sheets = 0
    
    # OCR 엔진 초기화
    engine = get_engine()
    normalizer = FinancialPatternNormalizer()
    
    for idx, image_path in enumerate(image_files, 1):
        log(f"[{idx}/{len(image_files)}] Processing: {image_path.name}")
        log("-" * 80)
        
        try:
            # 이미지 로드
            img = Image.open(image_path)
            page_height = img.size[1]
            
            # OCR 추출
            tokens = engine.extract(img)
            log(f"  OCR: {len(tokens)} tokens extracted")
            
            # 후처리
            merged_tokens = normalizer.merge_amount_currency(tokens, page_height)
            filtered_tokens = filter_low_confidence(merged_tokens)
            
            # 행 그룹화
            line_builder = LineBuilder(page_height=page_height)
            rows = line_builder.build_lines(filtered_tokens)
            log(f"  Grouped: {len(rows)} rows")
            
            # 표 분할
            chunker = Chunker()
            data_by_table = chunker.split_into_chunks(rows)
            
            if data_by_table:
                all_data[image_path.name] = data_by_table
                table_count = len(data_by_table)
                total_sheets += table_count
                success_count += 1
                
                log(f"  [SUCCESS] {table_count} table(s) detected")
                for table_name, table_rows in data_by_table.items():
                    log(f"    - {table_name}: {len(table_rows)} rows")
            else:
                fail_count += 1
                log(f"  [FAILED] No tables detected")
                
        except Exception as e:
            fail_count += 1
            error_msg = str(e)[:100]
            log(f"  [ERROR] {error_msg}")
        
        log("")
    
    # 통합 엑셀 파일 생성
    if all_data:
        log("=" * 80)
        log("Creating unified Excel file...")
        log("=" * 80)
        
        try:
            sheet_count = write_all_tables_to_single_excel(all_data, output_excel)
            log(f"[SUCCESS] Created {output_excel}")
            log(f"          Total sheets: {sheet_count}")
            log(f"          Images with data: {len(all_data)}")
        except Exception as e:
            log(f"[ERROR] Failed to create Excel: {str(e)}")
    else:
        log("[WARNING] No data to write to Excel")
    
    # 결과 요약
    log("")
    log("=" * 80)
    log("Batch Processing Completed")
    log("=" * 80)
    log(f"Total images: {len(image_files)}")
    log(f"Success: {success_count}")
    log(f"Failed: {fail_count}")
    log(f"Total sheets created: {total_sheets}")
    log(f"Output file: {output_excel}")
    log(f"Log file: {log_path}")
    log("")
    
    log_file.close()
    
    return output_excel, success_count, fail_count, total_sheets


if __name__ == "__main__":
    try:
        output_file, success, fail, sheets = batch_process_to_unified_excel()
        # Silent mode - check log files
        print(f"Complete: {output_file} ({sheets} sheets)")
    except Exception as e:
        # Write error to file only
        with open("unified_batch_error.txt", "w", encoding="utf-8") as f:
            f.write(f"UNIFIED BATCH PROCESSING ERROR\n")
            f.write("=" * 80 + "\n")
            f.write(f"{str(e)}\n")
        print(f"ERROR: Check unified_batch_error.txt")
        sys.exit(1)
