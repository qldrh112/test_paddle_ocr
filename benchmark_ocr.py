"""
benchmark_ocr.py

OCR 성능 벤치마킹 스크립트 (label_bank_audit_letter.csv 활용)

PP-Structure 도입 전/후의 표 내부 텍스트 일치율을 정량화
"""

import csv
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Dict
import difflib
from datetime import datetime

from config import Config
from engine import get_engine
from line_builder import LineBuilder
from chunker import Chunker
from table_schema import BANK_INQUIRY_SCHEMAS


def load_ground_truth(csv_path: str) -> List[Dict[str, str]]:
    """
    Ground truth CSV 파일 로드
    
    Args:
        csv_path: label_bank_audit_letter.csv 경로
    
    Returns:
        각 행의 필드 딕셔너리 리스트
    """
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def normalize_text(text: str) -> str:
    """
    텍스트 정규화 (비교를 위한 전처리)
    
    - 공백 제거
    - 특수문자 정규화
    """
    # 타입 체크: list나 다른 타입인 경우 문자열로 변환
    if isinstance(text, list):
        text = " ".join(str(item) for item in text)
    elif not isinstance(text, str):
        text = str(text)
    
    # 공백 제거
    text = text.replace(" ", "").replace("\t", "").replace("\n", "")
    # 쉼표 제거 (숫자 표현)
    text = text.replace(",", "")
    return text


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    두 텍스트의 유사도 계산 (0.0 ~ 1.0)
    
    Uses SequenceMatcher for similarity
    """
    text1_norm = normalize_text(text1)
    text2_norm = normalize_text(text2)
    
    return difflib.SequenceMatcher(None, text1_norm, text2_norm).ratio()


def calculate_cer(reference: str, hypothesis: str) -> float:
    """
    Character Error Rate (CER) 계산
    
    CER = (substitutions + deletions + insertions) / total_characters
    """
    ref_chars = list(normalize_text(reference))
    hyp_chars = list(normalize_text(hypothesis))
    
    # Levenshtein distance 계산
    m, n = len(ref_chars), len(hyp_chars)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_chars[i - 1] == hyp_chars[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,      # deletion
                    dp[i][j - 1] + 1,      # insertion
                    dp[i - 1][j - 1] + 1   # substitution
                )
    
    edit_distance = dp[m][n]
    cer = edit_distance / max(len(ref_chars), 1)
    
    return cer


def extract_ocr_data(image_path: str) -> List[Dict[str, str]]:
    """
    이미지에서 OCR 데이터 추출
    
    Args:
        image_path: 입력 이미지 경로
    
    Returns:
        추출된 표 데이터 (ground truth와 동일한 형식)
    """
    img = Image.open(image_path)
    page_height = img.size[1]
    
    # OCR 추출
    engine = get_engine()
    tokens = engine.extract(img)  # [(y, x, text, conf), ...]
    
    # 행 그룹화 (tokens를 그대로 전달)
    line_builder = LineBuilder(page_height=page_height)
    rows = line_builder.build_lines(tokens)
    
    # 표 영역 분할
    chunker = Chunker()
    tables = chunker.split_into_chunks(rows)
    
    # '금융상품_내역' 표만 추출
    extracted_rows = []
    
    if "금융상품_내역" in tables:
        table_rows = tables["금융상품_내역"]
        
        # 각 행을 딕셔너리로 변환 (헤더 매칭)
        schema = next((s for s in BANK_INQUIRY_SCHEMAS if s.table_name == "금융상품_내역"), None)
        if schema and schema.headers:
            headers = schema.headers
            
            for row in table_rows:
                # 행의 토큰들을 텍스트로 결합
                row_texts = [token[2] for token in row]  # (y, x, text, conf)
                
                # 헤더 개수에 맞춰 행 데이터 구성
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row_texts):
                        row_dict[f"{header}({i+1})"] = row_texts[i]
                    else:
                        row_dict[f"{header}({i+1})"] = ""
                
                extracted_rows.append(row_dict)
    
    return extracted_rows


def benchmark_ocr(
    image_path: str,
    ground_truth_csv: str,
    output_report: str = None
):
    """
    OCR 성능 벤치마킹 실행
    
    Args:
        image_path: 테스트 이미지 경로
        ground_truth_csv: Ground truth CSV 경로
        output_report: 결과 리포트 저장 경로 (선택사항)
    
    Returns:
        벤치마크 결과 딕셔너리
    """
    print("=" * 80)
    print("OCR 성능 벤치마킹")
    print("=" * 80)
    print(f"이미지: {image_path}")
    print(f"Ground Truth: {ground_truth_csv}")
    print()
    
    # Ground truth 로드
    gt_rows = load_ground_truth(ground_truth_csv)
    print(f"[1/3] Ground Truth 로드 완료: {len(gt_rows)} 행")
    
    # OCR 데이터 추출
    print(f"[2/3] OCR 데이터 추출 중...")
    ocr_rows = extract_ocr_data(image_path)
    print(f"      OCR 추출 완료: {len(ocr_rows)} 행")
    print()
    
    # 성능 측정
    print(f"[3/3] 성능 측정 중...")
    
    total_cells = 0
    matched_cells = 0
    total_similarity = 0.0
    total_cer = 0.0
    
    field_stats = {}  # 필드별 통계
    
    # 행 단위 비교
    max_rows = min(len(gt_rows), len(ocr_rows))
    
    for i in range(max_rows):
        gt_row = gt_rows[i]
        ocr_row = ocr_rows[i] if i < len(ocr_rows) else {}
        
        # 필드 단위 비교
        for field in gt_row.keys():
            gt_value = gt_row.get(field, "")
            ocr_value = ocr_row.get(field, "")
            
            # 유사도 계산
            similarity = calculate_text_similarity(gt_value, ocr_value)
            cer = calculate_cer(gt_value, ocr_value)
            
            total_cells += 1
            total_similarity += similarity
            total_cer += cer
            
            if similarity > 0.9:  # 90% 이상 일치
                matched_cells += 1
            
            # 필드별 통계 업데이트
            if field not in field_stats:
                field_stats[field] = {
                    "count": 0,
                    "similarity": 0.0,
                    "cer": 0.0,
                    "matched": 0
                }
            
            field_stats[field]["count"] += 1
            field_stats[field]["similarity"] += similarity
            field_stats[field]["cer"] += cer
            if similarity > 0.9:
                field_stats[field]["matched"] += 1
    
    # 결과 계산
    accuracy = (matched_cells / total_cells * 100) if total_cells > 0 else 0
    avg_similarity = (total_similarity / total_cells) if total_cells > 0 else 0
    avg_cer = (total_cer / total_cells) if total_cells > 0 else 0
    
    # 결과 출력
    print()
    print("=" * 80)
    print("벤치마크 결과")
    print("=" * 80)
    print(f"전체 셀 수: {total_cells}")
    print(f"정확히 일치 (유사도 > 90%): {matched_cells} ({accuracy:.2f}%)")
    print(f"평균 유사도: {avg_similarity:.4f}")
    print(f"평균 CER: {avg_cer:.4f}")
    print()
    
    print("필드별 성능:")
    print("-" * 80)
    for field, stats in field_stats.items():
        field_similarity = stats["similarity"] / stats["count"]
        field_cer = stats["cer"] / stats["count"]
        field_accuracy = stats["matched"] / stats["count"] * 100
        
        print(f"{field}:")
        print(f"  정확도: {field_accuracy:.2f}% | 유사도: {field_similarity:.4f} | CER: {field_cer:.4f}")
    
    print("=" * 80)
    
    # 리포트 저장
    if output_report:
        with open(output_report, 'w', encoding='utf-8') as f:
            f.write("OCR 성능 벤치마킹 결과\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"이미지: {image_path}\n")
            f.write(f"Ground Truth: {ground_truth_csv}\n")
            f.write(f"PP-Structure 사용: {Config.USE_PP_STRUCTURE}\n")
            f.write(f"Layout Analysis: {Config.ENABLE_LAYOUT_ANALYSIS}\n")
            f.write("\n")
            f.write(f"전체 셀 수: {total_cells}\n")
            f.write(f"정확히 일치 (유사도 > 90%): {matched_cells} ({accuracy:.2f}%)\n")
            f.write(f"평균 유사도: {avg_similarity:.4f}\n")
            f.write(f"평균 CER: {avg_cer:.4f}\n")
            f.write("\n")
            f.write("필드별 성능:\n")
            f.write("-" * 80 + "\n")
            for field, stats in field_stats.items():
                field_similarity = stats["similarity"] / stats["count"]
                field_cer = stats["cer"] / stats["count"]
                field_accuracy = stats["matched"] / stats["count"] * 100
                
                f.write(f"{field}:\n")
                f.write(f"  정확도: {field_accuracy:.2f}% | 유사도: {field_similarity:.4f} | CER: {field_cer:.4f}\n")
        
        print(f"\n✅ 리포트 저장: {output_report}")
    
    return {
        "total_cells": total_cells,
        "matched_cells": matched_cells,
        "accuracy": accuracy,
        "avg_similarity": avg_similarity,
        "avg_cer": avg_cer,
        "field_stats": field_stats
    }


if __name__ == "__main__":
    # 샘플 이미지 경로
    image_path = "image/bank_audit_letter-0003.jpg"
    ground_truth_csv = "label_bank_audit_letter.csv"
    
    # 출력 리포트 경로
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_report = f"benchmark_report_{timestamp}.txt"
    
    # 벤치마킹 실행
    results = benchmark_ocr(image_path, ground_truth_csv, output_report)
