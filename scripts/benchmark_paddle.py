import argparse
from pathlib import Path
import os
import cv2
import csv
from paddleocr import PPStructure
from paddleocr.ppstructure.recovery.recovery_to_doc import sorted_layout_boxes

def process_image(img_path, output_csv_path):
    # Initialize PPStructure with local models
    # Assuming models are in 'models/' directory relative to CWD
    
    # Path names from tar extraction usually match tar filename without .tar
    base_model_dir = Path('models')
    
    # Need to verify exact folder names after extraction
    # Standard names:
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
    
    print(f"DEBUG: Checking model paths...")
    for k, v in args.items():
        if 'dir' in k:
            p = Path(v)
            print(f"{k}: {v} (Exists: {p.exists()})")
            if p.exists():
                print(f" Contents: {[x.name for x in p.iterdir()]}")
    
    try:
        engine = PPStructure(**args)
    except Exception as e:
        print(f"Error initializing PPStructure: {e}")
        return

    img = cv2.imread(str(img_path))
    if img is None:
        print(f"Error: Could not read image {img_path}")
        return

    result = engine(img)
    
    # Filter for table regions
    table_regions = [res for res in result if res['type'] == 'table']
    
    if not table_regions:
        print(f"No table found in {img_path}")
        # Create empty CSV or handle appropriately
        with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
            pass
        return

    # Assuming the largest table or the first significant one is what we want
    # For this benchmark, we'll take the first one or merge? 
    # Usually structure recognition splits table if it segments the layout.
    # Let's write the result of the first table found (simplification for benchmark)
    
    target_table = table_regions[0]
    html_content = target_table['res']['html']
    
    # We could parse HTML, but PPStructure res also has 'cell_bbox' and structure info.
    # However, parsing the HTML to CSV is often easiest if structure is good.
    # Let's use a simple HTML table parser or just leverage the 'html' body.
    
    # A cleaner way using BeautifulSoup to convert HTML table to CSV
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
                
        print(f"Successfully saved table from {img_path} to {output_csv_path}")
            
    except ImportError:
        print("BeautifulSoup not found. Please install beautifulsoup4.")
    except Exception as e:
        print(f"Error parsing HTML: {e}")

def main():
    parser = argparse.ArgumentParser(description="Benchmark PaddleOCR Table Extraction")
    parser.add_argument('--inputs', nargs='+', required=True, help="List of input image paths")
    parser.add_argument('--outputs', nargs='+', required=True, help="List of output CSV paths")
    
    args = parser.parse_args()
    
    if len(args.inputs) != len(args.outputs):
        print("Error: Number of inputs and outputs must match")
        return

    for img_p, out_p in zip(args.inputs, args.outputs):
        process_image(Path(img_p), Path(out_p))

if __name__ == "__main__":
    main()
