"""
OCR 정확도 비교 스크립트

정답 레이블(label.csv)과 Tesseract OCR 결과(bank_audit_letter-0003_table_0.csv)를 비교하여
정확도를 분석합니다.
"""

import pandas as pd
import os
from difflib import SequenceMatcher

def load_csv_safely(filepath):
    """CSV 파일을 안전하게 로드"""
    try:
        df = pd.read_csv(filepath)
        return df
    except Exception as e:
        print(f"CSV 로드 오류: {e}")
        return None

def calculate_similarity(str1, str2):
    """두 문자열 간의 유사도 계산 (0-100%)"""
    if pd.isna(str1) and pd.isna(str2):
        return 100.0
    if pd.isna(str1) or pd.isna(str2):
        return 0.0
    
    str1 = str(str1).strip()
    str2 = str(str2).strip()
    
    if str1 == str2:
        return 100.0
    
    # SequenceMatcher를 사용한 유사도 계산
    ratio = SequenceMatcher(None, str1, str2).ratio()
    return ratio * 100

def compare_csvs(label_path, ocr_path, output_path):
    """두 CSV 파일을 비교하고 결과를 분석"""
    
    print("=" * 80)
    print("OCR 정확도 비교 분석")
    print("=" * 80)
    
    # CSV 파일 로드
    label_df = load_csv_safely(label_path)
    ocr_df = load_csv_safely(ocr_path)
    
    if label_df is None or ocr_df is None:
        print("CSV 파일 로드 실패")
        return
    
    print(f"\n정답 레이블: {label_path}")
    print(f"  - 행 수: {len(label_df)}")
    print(f"  - 열 수: {len(label_df.columns)}")
    
    print(f"\nOCR 결과: {ocr_path}")
    print(f"  - 행 수: {len(ocr_df)}")
    print(f"  - 열 수: {len(ocr_df.columns)}")
    
    # 구조 비교
    print(f"\n{'='*80}")
    print("1. 구조 비교")
    print(f"{'='*80}")
    
    if len(label_df) == len(ocr_df):
        print(f"✓ 행 개수 일치: {len(label_df)}개")
    else:
        print(f"✗ 행 개수 불일치: 정답 {len(label_df)}개, OCR {len(ocr_df)}개")
    
    if len(label_df.columns) == len(ocr_df.columns):
        print(f"✓ 열 개수 일치: {len(label_df.columns)}개")
    else:
        print(f"✗ 열 개수 불일치: 정답 {len(label_df.columns)}개, OCR {len(ocr_df.columns)}개")
    
    # 셀별 비교
    print(f"\n{'='*80}")
    print("2. 셀별 정확도 분석")
    print(f"{'='*80}")
    
    total_cells = 0
    exact_matches = 0
    similarities = []
    differences = []
    
    max_rows = min(len(label_df), len(ocr_df))
    max_cols = min(len(label_df.columns), len(ocr_df.columns))
    
    for row_idx in range(max_rows):
        for col_idx in range(max_cols):
            label_val = label_df.iloc[row_idx, col_idx]
            ocr_val = ocr_df.iloc[row_idx, col_idx]
            
            total_cells += 1
            similarity = calculate_similarity(label_val, ocr_val)
            similarities.append(similarity)
            
            if similarity == 100.0:
                exact_matches += 1
            else:
                # 차이점 기록
                differences.append({
                    'row': row_idx + 1,
                    'col': col_idx,
                    'column_name': label_df.columns[col_idx] if col_idx < len(label_df.columns) else f"Column_{col_idx}",
                    'expected': str(label_val),
                    'actual': str(ocr_val),
                    'similarity': f"{similarity:.1f}%"
                })
    
    # 정확도 계산
    exact_accuracy = (exact_matches / total_cells * 100) if total_cells > 0 else 0
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0
    
    print(f"\n총 셀 개수: {total_cells}")
    print(f"정확히 일치하는 셀: {exact_matches}개")
    print(f"완전 일치 정확도: {exact_accuracy:.2f}%")
    print(f"평균 유사도: {avg_similarity:.2f}%")
    
    # 차이점 상세 출력
    if differences:
        print(f"\n{'='*80}")
        print(f"3. 차이점 상세 ({len(differences)}개)")
        print(f"{'='*80}")
        
        for i, diff in enumerate(differences[:30], 1):  # 최대 30개만 표시
            print(f"\n[{i}] 행 {diff['row']}, 열 \"{diff['column_name']}\"")
            print(f"    정답: {diff['expected']}")
            print(f"    OCR:  {diff['actual']}")
            print(f"    유사도: {diff['similarity']}")
        
        if len(differences) > 30:
            print(f"\n... 외 {len(differences) - 30}개 차이점 생략")
    
    # 결과를 파일로 저장
    print(f"\n{'='*80}")
    print("4. 결과 저장")
    print(f"{'='*80}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# OCR 정확도 비교 분석 결과\n\n")
        f.write(f"**분석 일자**: 2026-02-17\n\n")
        f.write(f"**대상 이미지**: bank_audit_letter-0003.jpg\n\n")
        
        f.write("## 요약\n\n")
        f.write(f"| 항목 | 값 |\n")
        f.write(f"|------|----|\n")
        f.write(f"| 총 셀 개수 | {total_cells}개 |\n")
        f.write(f"| 정확히 일치 | {exact_matches}개 |\n")
        f.write(f"| 완전 일치 정확도 | {exact_accuracy:.2f}% |\n")
        f.write(f"| 평균 유사도 | {avg_similarity:.2f}% |\n")
        f.write(f"| 차이점 개수 | {len(differences)}개 |\n\n")
        
        if differences:
            f.write("## 차이점 상세\n\n")
            f.write("| 행 | 열 | 정답 | OCR 결과 | 유사도 |\n")
            f.write("|----|----|------|----------|--------|\n")
            
            for diff in differences:
                f.write(f"| {diff['row']} | {diff['column_name']} | {diff['expected']} | {diff['actual']} | {diff['similarity']} |\n")
    
    print(f"\n분석 결과 저장 완료: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    label_path = "label.csv"
    ocr_path = "output/bank_audit_letter-0003_table_0.csv"
    output_path = "docs/ocr_accuracy_analysis.md"
    
    compare_csvs(label_path, ocr_path, output_path)
