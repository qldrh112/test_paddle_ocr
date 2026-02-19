"""
금융거래조회서 표 추출 메인 스크립트

이미지 파일에서 표를 추출하고 CSV, Excel, JSON 형식으로 저장합니다.
"""

import argparse
import logging
from pathlib import Path
import sys

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from table_extractor.extractor import TableExtractor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_single_image(image_path: Path, output_dir: Path, extractor: TableExtractor):
    """
    단일 이미지 파일 처리
    
    Args:
        image_path: 이미지 파일 경로
        output_dir: 출력 디렉토리 경로
        extractor: TableExtractor 인스턴스
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"이미지 처리 중: {image_path.name}")
    logger.info(f"{'='*80}")
    
    # 표 추출
    tables = extractor.extract_tables_from_image(str(image_path), use_preprocessing=False)
    
    if not tables:
        logger.warning(f"⚠️  표를 찾지 못했습니다: {image_path.name}")
        return
    
    logger.info(f"✓ {len(tables)}개의 표를 찾았습니다.")
    
    # 각 표를 다양한 형식으로 저장
    for table_info in tables:
        idx = table_info['table_index']
        df = table_info['dataframe']
        
        # 파일명 생성
        base_name = image_path.stem
        
        # CSV 저장
        csv_path = output_dir / f"{base_name}_table_{idx}.csv"
        extractor.save_table_to_csv(df, str(csv_path))
        
        # Excel 저장
        excel_path = output_dir / f"{base_name}_table_{idx}.xlsx"
        extractor.save_table_to_excel(df, str(excel_path))
        
        # JSON 저장
        json_path = output_dir / f"{base_name}_table_{idx}.json"
        extractor.save_table_to_json(df, str(json_path))
        
        # 표 정보 출력
        logger.info(f"\n표 {idx + 1} 정보:")
        logger.info(f"  - 크기: {df.shape[0]}행 x {df.shape[1]}열")
        logger.info(f"  - CSV: {csv_path.name}")
        logger.info(f"  - Excel: {excel_path.name}")
        logger.info(f"  - JSON: {json_path.name}")
        
        # 표 미리보기 (처음 5행)
        logger.info(f"\n표 미리보기:")
        logger.info(f"\n{df.head()}\n")


def process_directory(input_dir: Path, output_dir: Path, extractor: TableExtractor):
    """
    디렉토리 내의 모든 이미지 파일 처리
    
    Args:
        input_dir: 입력 디렉토리 경로
        output_dir: 출력 디렉토리 경로
        extractor: TableExtractor 인스턴스
    """
    # 지원하는 이미지 확장자
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    # 이미지 파일 찾기
    image_files = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    if not image_files:
        logger.error(f"디렉토리에서 이미지 파일을 찾지 못했습니다: {input_dir}")
        return
    
    logger.info(f"\n총 {len(image_files)}개의 이미지 파일을 발견했습니다.")
    logger.info(f"처리 시작...\n")
    
    # 각 이미지 처리
    total_tables = 0
    for image_file in sorted(image_files):
        tables = extractor.extract_tables_from_image(str(image_file), use_preprocessing=False)
        
        if tables:
            total_tables += len(tables)
            
            for table_info in tables:
                idx = table_info['table_index']
                df = table_info['dataframe']
                base_name = image_file.stem
                
                # 파일 저장
                csv_path = output_dir / f"{base_name}_table_{idx}.csv"
                excel_path = output_dir / f"{base_name}_table_{idx}.xlsx"
                json_path = output_dir / f"{base_name}_table_{idx}.json"
                
                extractor.save_table_to_csv(df, str(csv_path))
                extractor.save_table_to_excel(df, str(excel_path))
                extractor.save_table_to_json(df, str(json_path))
                
                logger.info(f"✓ {image_file.name} - 표 {idx + 1} 저장 완료")
        else:
            logger.info(f"⊘ {image_file.name} - 표 없음")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"처리 완료!")
    logger.info(f"총 {len(image_files)}개 이미지에서 {total_tables}개의 표를 추출했습니다.")
    logger.info(f"출력 디렉토리: {output_dir}")
    logger.info(f"{'='*80}\n")


def main():
    """
    메인 함수
    """
    parser = argparse.ArgumentParser(
        description='금융거래조회서 이미지에서 표 추출',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 단일 이미지 처리
  python src/main.py --input test/image/bank_audit_letter-0003.jpg --output output
  
  # 디렉토리 내 모든 이미지 처리
  python src/main.py --input test/image --output output
  
  # OCR 언어 변경 (한국어 + 영어)
  python src/main.py --input test/image --output output --lang kor+eng
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='입력 이미지 파일 또는 디렉토리 경로'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='출력 디렉토리 경로'
    )
    
    parser.add_argument(
        '--lang', '-l',
        type=str,
        default='kor+eng',
        help='Tesseract OCR 언어 설정 (기본값: kor+eng)'
    )
    
    args = parser.parse_args()
    
    # 경로 검증
    input_path = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"입력 경로를 찾을 수 없습니다: {input_path}")
        sys.exit(1)
    
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # TableExtractor 초기화
    logger.info("표 추출기 초기화 중...")
    extractor = TableExtractor(lang=args.lang)
    
    # 입력이 파일인지 디렉토리인지 확인하고 처리
    if input_path.is_file():
        process_single_image(input_path, output_dir, extractor)
    elif input_path.is_dir():
        process_directory(input_path, output_dir, extractor)
    else:
        logger.error(f"유효하지 않은 입력 경로입니다: {input_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
