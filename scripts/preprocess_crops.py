import argparse
from pathlib import Path
import os
import cv2
from paddleocr import PPStructure

def get_table_crops(img_path, output_dir):
    # Initialize PPStructure with local models (layout only)
    base_model_dir = Path('models')
    
    args = {
        'show_log': True,
        'image_orientation': False,
        'layout': True,
        'table': False, # We only need layout detection
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
        print(f"Error: Could not read image {img_path}")
        return

    result = engine(img)
    
    # Filter for table regions
    table_regions = [res for res in result if res['type'] == 'table']
    
    if not table_regions:
        print(f"No table found in {img_path}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, region in enumerate(table_regions):
        bbox = region['bbox'] # [x1, y1, x2, y2]
        x1, y1, x2, y2 = bbox
        
        # Add padding
        h, w, _ = img.shape
        padding = 20
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        crop = img[int(y1):int(y2), int(x1):int(x2)]
        
        # Save crop
        stem = Path(img_path).stem
        crop_name = f"{stem}_table_{i}.jpg"
        crop_path = output_dir / crop_name
        cv2.imwrite(str(crop_path), crop)
        print(f"Saved crop: {crop_path}")

def main():
    parser = argparse.ArgumentParser(description="Extract Table Crops")
    parser.add_argument('--inputs', nargs='+', required=True, help="Input images")
    parser.add_argument('--output_dir', required=True, help="Output directory for crops")
    
    args = parser.parse_args()
    
    out_dir = Path(args.output_dir)
    for img_p in args.inputs:
        get_table_crops(Path(img_p), out_dir)

if __name__ == "__main__":
    main()
