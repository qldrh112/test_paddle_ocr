"""
배치 처리 스크립트 (SILENT MODE)
image 폴더의 모든 jpg 파일을 처리하여 개별 xlsx 파일 생성
모든 출력은 로그 파일로만 저장 (UnicodeEncodeError 방지)
"""

from pathlib import Path
from datetime import datetime
import sys

from main import process_image_to_excel

def batch_process_images():
    """모든 이미지 파일을 배치 처리 (SILENT)"""
    
    # 로그 파일 준비
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"batch_log_{timestamp}.txt"
    summary_path = f"batch_result_{timestamp}.txt"
    
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
    log(f"Batch Processing Started: {len(image_files)} images")
    log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 80)
    log("")
    
    # 결과 저장
    results = []
    success_count = 0
    fail_count = 0
    
    for idx, image_path in enumerate(image_files, 1):
        log(f"[{idx}/{len(image_files)}] Processing: {image_path.name}")
        log("-" * 80)
        
        try:
            # 이미지 처리
            result = process_image_to_excel(str(image_path))
            
            if result and result.get('output_path'):
                success_count += 1
                status = "SUCCESS"
                output_path = result['output_path']
                sheet_count = result.get('sheet_count', 0)
                row_count = result.get('row_count', 0)
                
                results.append({
                    'index': idx,
                    'image': image_path.name,
                    'status': status,
                    'output': output_path,
                    'sheets': sheet_count,
                    'rows': row_count
                })
                
                log(f"[SUCCESS] Output: {output_path}")
                log(f"          Sheets: {sheet_count}, Rows: {row_count}")
            else:
                fail_count += 1
                status = "FAILED"
                results.append({
                    'index': idx,
                    'image': image_path.name,
                    'status': status,
                    'output': '-',
                    'sheets': 0,
                    'rows': 0
                })
                log(f"[FAILED]")
                
        except Exception as e:
            fail_count += 1
            error_msg = str(e)[:100]
            results.append({
                'index': idx,
                'image': image_path.name,
                'status': f"ERROR: {error_msg}",
                'output': '-',
                'sheets': 0,
                'rows': 0
            })
            log(f"[ERROR] {error_msg}")
        
        log("")
    
    # 결과 요약 로그
    log("=" * 80)
    log("Batch Processing Completed")
    log("=" * 80)
    log(f"Total: {len(image_files)}")
    log(f"Success: {success_count}")
    log(f"Failed: {fail_count}")
    log("")
    
    # 결과를 텍스트 파일로 저장
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("Batch Processing Result Summary\n")
        f.write("=" * 80 + "\n")
        f.write(f"Processing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Images: {len(image_files)}\n")
        f.write(f"Success: {success_count}\n")
        f.write(f"Failed: {fail_count}\n")
        f.write(f"Success Rate: {success_count/len(image_files)*100:.1f}%\n")
        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write("Individual Results\n")
        f.write("=" * 80 + "\n")
        f.write("\n")
        
        for r in results:
            f.write(f"[{r['index']:2d}] {r['image']:<35s} | {r['status']}\n")
            if r['status'] == "SUCCESS":
                f.write(f"      Output: {r['output']}\n")
                f.write(f"      Sheets: {r['sheets']}, Rows: {r['rows']}\n")
            f.write("\n")
    
    log(f"Summary saved: {summary_path}")
    log("Log file: " + log_path)
    log_file.close()
    
    return results, summary_path, log_path


if __name__ == "__main__":
    try:
        results, summary_path, log_path = batch_process_images()
        # No terminal output - check log files
    except Exception as e:
        # Write error to file only
        with open("batch_error.txt", "w", encoding="utf-8") as f:
            f.write(f"BATCH PROCESSING ERROR\n")
            f.write("=" * 80 + "\n")
            f.write(f"{str(e)}\n")
        sys.exit(1)
