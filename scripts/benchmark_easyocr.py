import easyocr
import argparse
import csv
import cv2
import numpy as np
from pathlib import Path

def overlap(box1, box2):
    # box: [min_x, max_x, min_y, max_y]
    # Check if lines overlap in Y-axis significant enough to be same row
    # Using center point or intersection over union for 1D (Y-axis)
    
    y1_min, y1_max = box1[2], box1[3]
    y2_min, y2_max = box2[2], box2[3]
    
    intersection = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
    union = max(y1_max, y2_max) - min(y1_min, y2_min)
    
    if union == 0: return 0
    
    # If intersection covers a large portion of the smaller box's height
    min_height = min(y1_max - y1_min, y2_max - y2_min)
    if min_height == 0: return 0
    return intersection / min_height

def group_into_rows(results, y_threshold=0.5):
    # results: list of (bbox, text, prob)
    # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    
    # Calculate Y-range for each box
    # [min_x, max_x, min_y, max_y]
    boxes = []
    for (bbox, text, prob) in results:
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        boxes.append({
            'min_x': min(xs), 'max_x': max(xs),
            'min_y': min(ys), 'max_y': max(ys),
            'text': text,
            'prob': prob
        })
        
    # Sort by Y
    boxes.sort(key=lambda b: (b['min_y'] + b['max_y'])/2)
    
    rows = []
    current_row = []
    
    if not boxes:
        return []

    # Simple row clustering
    # If a new box's vertical center is within the y-range of the current row average, add it
    
    current_row.append(boxes[0])
    
    for box in boxes[1:]:
        # Compare with the last added box or existing row average
        # Let's take the last box of the current row to check proximity
        last_box = current_row[-1]
        
        # Check vertical intersection
        # We can treat each box as a y-interval. 
        # If the overlap of y-intervals is significant, same row.
        
        lb_y = [0, 0, last_box['min_y'], last_box['max_y']]
        cb_y = [0, 0, box['min_y'], box['max_y']]
        
        ov = overlap(lb_y, cb_y)
        
        # Threshold: if overlap is > 50% of height
        if ov > y_threshold:
            current_row.append(box)
        else:
            rows.append(current_row)
            current_row = [box]
            
    if current_row:
        rows.append(current_row)
        
    # For each row, sort by X
    for row in rows:
        row.sort(key=lambda b: b['min_x'])
        
    return rows

def process_image(img_path, output_csv_path):
    reader = easyocr.Reader(['ko', 'en']) # Assuming Korean and English
    result = reader.readtext(str(img_path))
    
    rows = group_into_rows(result)
    
    # Write to CSV
    # Note: This simply dumps text in order. 
    # Real table reconstruction needs column alignment.
    # For this benchmark, we will try to align columns crudely.
    
    # Find all unique column centers or boundaries? 
    # Simplified approach: Just write the text items in the row. 
    # The comparison logic later will check content regardless of strict column index 
    # if we use a bag-of-words or fuzzy row matching, OR we try to aligning.
    
    # Let's try to just write variable length rows for now. 
    # The user asked for "Table Data Extraction", so preserving structure is key.
    # But without vertical separators, column alignment is hard.
    
    with open(output_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow([item['text'] for item in row])
            
    print(f"Processed {img_path} -> {output_csv_path}")

def main():
    parser = argparse.ArgumentParser(description="Benchmark EasyOCR Table Extraction")
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
