import argparse
from pathlib import Path
import os
import cv2
from paddleocr import PPStructure

def get_table_crops(img_path, output_dir):
    # 로컬 모델을 사용하여 PPStructure 초기화 (레이아웃 감지 전용)
    base_model_dir = Path('models')
    
    args = {
        'show_log': True,
        'image_orientation': False,
        'layout': True,
        'table': False, # 레이아웃 감지만 필요하므로 비활성화
        'det': False,
        'rec': False,
        'det_model_dir': str(base_model_dir / 'ch_PP-OCRv4_det_infer'),
        'rec_model_dir': str(base_model_dir / 'ch_PP-OCRv4_rec_infer'),
        'table_model_dir': str(base_model_dir / 'ch_ppstructure_mobile_v2.0_SLANet_infer'),
        'layout_model_dir': str(base_model_dir / 'picodet_lcnet_x1_0_fgd_layout_cdla_infer'),
        'use_gpu': False,
    }
    
    engine = PPStructure(**args)
    
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"오류: 이미지 {img_path}를 읽을 수 없습니다.")
        return

    result = engine(img)
    
    # 표(table) 영역만 필터링
    table_regions = [res for res in result if res['type'] == 'table']
    
    if not table_regions:
        print(f"{img_path}에서 표를 찾을 수 없습니다.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, region in enumerate(table_regions):
        bbox = region['bbox'] # [x1, y1, x2, y2]
        x1, y1, x2, y2 = bbox
        
        # 여백(Padding) 추가
        h, w, _ = img.shape
        padding = 20
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        # 이미지 크롭
        crop = img[int(y1):int(y2), int(x1):int(x2)]
        
        # 크롭 이미지 저장
        stem = Path(img_path).stem
        crop_name = f"{stem}_table_{i}.jpg"
        crop_path = output_dir / crop_name
        cv2.imwrite(str(crop_path), crop)
        print(f"크롭 저장 완료: {crop_path}")

def main():
    parser = argparse.ArgumentParser(description="표 영역 크롭 추출 도구")
    parser.add_argument('--inputs', nargs='+', required=True, help="입력 이미지 리스트")
    parser.add_argument('--output_dir', required=True, help="크롭 이미지를 저장할 디렉토리")
    
    args = parser.parse_args()
    
    out_dir = Path(args.output_dir)
    for img_p in args.inputs:
        get_table_crops(Path(img_p), out_dir)

if __name__ == "__main__":
    main()
