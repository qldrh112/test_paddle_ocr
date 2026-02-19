import argparse
from pathlib import Path
import os
import cv2
import csv
from paddleocr import PPStructure
from paddleocr.ppstructure.recovery.recovery_to_doc import sorted_layout_boxes

def process_image(img_path, output_csv_path):
    # 로컬 모델을 사용하여 PPStructure 초기화
    # 모델은 현재 작업 디렉토리 기준 'models/' 폴더에 있다고 가정함
    
    # tar 압축 해제 후 경로명은 일반적으로 .tar를 제외한 파일명과 일치함
    base_model_dir = Path('models')
    
    # 압축 해제 후 정확한 폴더 이름 확인 필요
    # 표준 이름 예시:
    # ch_PP-OCRv4_det_infer
    # ch_PP-OCRv4_rec_infer
    # ch_ppstructure_mobile_v2.0_SLANet_infer
    
    args = {
        'show_log': True,
        'image_orientation': False,
        'layout': True,
        'det_model_dir': str(base_model_dir / 'ch_PP-OCRv4_det_server_infer'),
        'rec_model_dir': str(base_model_dir / 'ch_PP-OCRv4_rec_server_infer'),
        'table_model_dir': str(base_model_dir / 'ch_ppstructure_mobile_v2.0_SLANet_infer'),
        'layout_model_dir': str(base_model_dir / 'picodet_lcnet_x1_0_fgd_layout_cdla_infer'),
        'use_gpu': False,
    }
    
    print(f"디버그: 모델 경로 확인 중...")
    for k, v in args.items():
        if 'dir' in k:
            p = Path(v)
            print(f"{k}: {v} (존재 여부: {p.exists()})")
            if p.exists():
                print(f" 내용물: {[x.name for x in p.iterdir()]}")
    
    try:
        engine = PPStructure(**args)
    except Exception as e:
        print(f"PPStructure 초기화 오류: {e}")
        return

    img = cv2.imread(str(img_path))
    if img is None:
        print(f"오류: 이미지 {img_path}를 읽을 수 없습니다.")
        return

    result = engine(img)
    
    # 표 영역 필터링
    table_regions = [res for res in result if res['type'] == 'table']
    
    if not table_regions:
        print(f"{img_path}에서 표를 찾을 수 없습니다.")
        # 빈 CSV 파일을 생성하거나 적절히 처리
        with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
            pass
        return

    # 첫 번째 유의미한 표를 대상 표로 간주 (벤치마크 단순화)
    # 레이아웃 분석 시 표가 분할될 수 있으나, 여기서는 첫 번째 결과를 사용
    
    target_table = table_regions[0]
    html_content = target_table['res']['html']
    
    # HTML을 파싱하여 CSV로 변환
    # 구조가 잘 잡혀있다면 HTML 파싱이 가장 편리함
    
    # BeautifulSoup을 사용하여 HTML 표를 CSV로 변환
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        rows = soup.find_all('tr')
        
        with open(output_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            for row in rows:
                cols = row.find_all(['td', 'th'])
                cols = [ele.text.strip() for ele in cols]
                writer.writerow(cols)
                
        print(f"성공적으로 {img_path}에서 표를 추출하여 {output_csv_path}에 저장했습니다.")
            
    except ImportError:
        print("BeautifulSoup을 찾을 수 없습니다. beautifulsoup4를 설치해주세요.")
    except Exception as e:
        print(f"HTML 파싱 오류: {e}")

def main():
    parser = argparse.ArgumentParser(description="PaddleOCR 표 추출 벤치마크")
    parser.add_argument('--inputs', nargs='+', required=True, help="입력 이미지 경로 리스트")
    parser.add_argument('--outputs', nargs='+', required=True, help="출력 CSV 경로 리스트")
    
    args = parser.parse_args()
    
    if len(args.inputs) != len(args.outputs):
        print("오류: 입력과 출력의 개수가 일치해야 합니다.")
        return

    for img_p, out_p in zip(args.inputs, args.outputs):
        process_image(Path(img_p), Path(out_p))

if __name__ == "__main__":
    main()
