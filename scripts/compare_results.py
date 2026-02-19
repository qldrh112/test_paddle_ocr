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
    # 평가지표
    total_gt_cells = sum(len(r) for r in gt_rows)
    total_pred_cells = sum(len(r) for r in pred_rows)
    
    match_count = 0
    exact_match_count = 0
    
    # 1. Bag of Cells 비교 (구조와 무관하게 내용 중심 비교)
    # 모든 셀 데이터 수집
    gt_cells = [c.strip() for r in gt_rows for c in r if c.strip()]
    pred_cells = [c.strip() for r in pred_rows for c in r if c.strip()]
    
    # 단순 매칭
    # 중복 계산을 방지하기 위해 매칭된 항목은 제거함
    
    temp_pred = pred_cells.copy()
    
    for gt_cell in gt_cells:
        # 예측값 중에서 최적의 매칭 탐색
        best_match_idx = -1
        best_score = 0
        
        for i, pred_cell in enumerate(temp_pred):
            score = calculate_similarity(gt_cell, pred_cell)
            if score > best_score:
                best_score = score
                best_match_idx = i
        
        if best_match_idx != -1 and best_score > 0.8: # 임계값 설정
            match_count += 1
            if best_score == 1.0:
                exact_match_count += 1
            temp_pred.pop(best_match_idx)
            
    # 정밀도(Precision) / 재현율(Recall) 계산
    # Recall = 매칭된 수 / 전체 정답 셀 수
    # Precision = 매칭된 수 / 전체 예측 셀 수
    
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
    parser.add_argument('--gt', required=True, help="정답 레이블(Ground Truth) CSV 경로")
    parser.add_argument('--paddle', help="PaddleOCR 결과 CSV 경로")
    parser.add_argument('--easy', help="EasyOCR 결과 CSV 경로")
    parser.add_argument('--tess', help="Tesseract 결과 CSV 경로")
    
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
        
    print(f"{Path(args.gt).name}에 대한 비교 결과:")
    print(f"{'프레임워크':<12} | {'정밀도':<6} | {'재현율':<6} | {'F1':<6} | {'일치율':<6}")
    print("-" * 50)
    
    for name, stats in results.items():
        print(f"{name:<12} | {stats['precision']:.3f}  | {stats['recall']:.3f}  | {stats['f1']:.3f}  | {stats['exact_matches']}/{stats['gt_cells']}")
    print("\n")

if __name__ == "__main__":
    main()
