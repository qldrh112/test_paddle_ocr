import pytesseract
from pytesseract import Output
import argparse
import csv
import cv2
import pandas as pd
from pathlib import Path

# Set tesseract cmd if not in path, usually it's in env, but user said 'venv_tesseract'.
# Assuming tesseract binary is in PATH or configured in the venv context.

def group_into_rows(df, y_threshold=10):
    # df has left, top, width, height, text
    # Filter empty text
    df = df[df.text.str.strip() != '']
    
    # Sort by Top
    df = df.sort_values(by='top')
    
    rows = []
    if df.empty:
        return rows
        
    current_row = []
    # Use the first item to start a row
    # We will iterate and check if 'top' is close to the current row's average 'top' or 'bottom'
    
    # Simple logic: if a word's top is within [prev_top - th, prev_top + th], same row.
    # But font size matters.
    # Let's use the center Y.
    
    row_clusters = []
    
    # Convert to list of dicts for easier handling
    items = df.to_dict('records')
    
    current_cluster = [items[0]]
    
    for item in items[1:]:
        # Check against the average center of the current cluster
        cluster_ys = [(i['top'] + i['height']/2) for i in current_cluster]
        avg_y = sum(cluster_ys) / len(cluster_ys)
        
        item_y = item['top'] + item['height']/2
        
        if abs(item_y - avg_y) < (item['height'] / 2 + 5): # heuristic tolerance
            current_cluster.append(item)
        else:
            row_clusters.append(current_cluster)
            current_cluster = [item]
            
    if current_cluster:
        row_clusters.append(current_cluster)
        
    # Sort each cluster by 'left' to order columns
    parsed_rows = []
    for cluster in row_clusters:
        cluster.sort(key=lambda x: x['left'])
        parsed_rows.append([x['text'] for x in cluster])
        
    return parsed_rows

def process_image(img_path, output_csv_path):
    img = cv2.imread(str(img_path))
    
    # Page segmentation mode 6 (Assume a single uniform block of text) works well for tables sometimes
    # or 4 (Assume a single column of text of variable sizes)
    # or 11 (Sparse text)
    # Default 3 might struggle with strict table formatting without grid lines.
    # Let's try --psm 6 based on common table practices. 
    # Also set language to kor+eng
    
    custom_config = r'--oem 3 --psm 6 -l kor+eng'
    
    try:
        data = pytesseract.image_to_data(img, config=custom_config, output_type=Output.DATAFRAME)
    except pytesseract.TesseractNotFoundError:
        print("Tesseract binary not found. Ensure it's installed and in PATH.")
        return
        
    # Group by rows
    rows = group_into_rows(data)
    
    with open(output_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
            
    print(f"Processed {img_path} -> {output_csv_path}")

def main():
    parser = argparse.ArgumentParser(description="Benchmark Tesseract Table Extraction")
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
