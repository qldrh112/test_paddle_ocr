import csv
import argparse
import sys
from pathlib import Path
from difflib import SequenceMatcher

def load_csv(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        return list(reader)

def calculate_similarity(s1, s2):
    return SequenceMatcher(None, s1, s2).ratio()

def compare_tables(gt_rows, pred_rows):
    # Metrics
    total_gt_cells = sum(len(r) for r in gt_rows)
    total_pred_cells = sum(len(r) for r in pred_rows)
    
    match_count = 0
    exact_match_count = 0
    
    # 1. Bag of Cells comparison (Structure agnostic)
    # Collect all cells
    gt_cells = [c.strip() for r in gt_rows for c in r if c.strip()]
    pred_cells = [c.strip() for r in pred_rows for c in r if c.strip()]
    
    # Simple matching
    # We remove matched items to avoid double counting
    
    temp_pred = pred_cells.copy()
    
    for gt_cell in gt_cells:
        # Find best match in pred
        best_match_idx = -1
        best_score = 0
        
        for i, pred_cell in enumerate(temp_pred):
            score = calculate_similarity(gt_cell, pred_cell)
            if score > best_score:
                best_score = score
                best_match_idx = i
        
        if best_match_idx != -1 and best_score > 0.8: # Threshold
            match_count += 1
            if best_score == 1.0:
                exact_match_count += 1
            temp_pred.pop(best_match_idx)
            
    # Precision / Recall
    # Recall = Matched / Total GT
    # Precision = Matched / Total Pred
    
    recall = match_count / len(gt_cells) if gt_cells else 0
    precision = match_count / len(pred_cells) if pred_cells else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "gt_cells": len(gt_cells),
        "pred_cells": len(pred_cells),
        "matched": match_count,
        "exact_matches": exact_match_count,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gt', required=True, help="Ground Truth CSV")
    parser.add_argument('--paddle', help="PaddleOCR Result CSV")
    parser.add_argument('--easy', help="EasyOCR Result CSV")
    parser.add_argument('--tess', help="Tesseract Result CSV")
    
    args = parser.parse_args()
    
    gt = load_csv(args.gt)
    
    results = {}
    
    if args.paddle:
        pred = load_csv(args.paddle)
        results['PaddleOCR'] = compare_tables(gt, pred)
        
    if args.easy:
        pred = load_csv(args.easy)
        results['EasyOCR'] = compare_tables(gt, pred)
        
    if args.tess:
        pred = load_csv(args.tess)
        results['Tesseract'] = compare_tables(gt, pred)
        
    print(f"Comparison for {Path(args.gt).name}:")
    print(f"{'Framework':<12} | {'Prec':<6} | {'Recall':<6} | {'F1':<6} | {'Exact':<6}")
    print("-" * 50)
    
    for name, stats in results.items():
        print(f"{name:<12} | {stats['precision']:.3f}  | {stats['recall']:.3f}  | {stats['f1']:.3f}  | {stats['exact_matches']}/{stats['gt_cells']}")
    print("\n")

if __name__ == "__main__":
    main()
