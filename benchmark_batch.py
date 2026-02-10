"""
benchmark_batch.py

배치 벤치마킹 스크립트 (전체 이미지 세트 처리)

표 인식 성공률, 필드별 가중치, Baseline/PP-Structure 비교
"""

import csv
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Dict
import json
from datetime import datetime

from config import Config
from engine import get_engine
from line_builder import LineBuilder
from chunker import Chunker
from table_schema import BANK_INQUIRY_SCHEMAS
from benchmark_ocr import (
    normalize_text,
    calculate_text_similarity,
    calculate_cer
)


# 표가 있는 이미지 목록 (agent.md 기준)
IMAGES_WITH_TABLES = [
    "bank_audit_letter-0003.jpg",
    "bank_audit_letter-0004.jpg",
    "bank_audit_letter-0005.jpg",
    "bank_audit_letter-0006.jpg",
    "bank_audit_letter-0008.jpg",
    "bank_audit_letter-0009.jpg"
]

# 필드별 가중치 (회계 감사 관점에서 중요도)
FIELD_WEIGHTS = {
    "금융상품의 종류(1)": 0.5,     # 낮은 중요도
    "계좌번호(2)": 2.0,            # 매우 중요
    "금액(3)": 2.0,                # 매우 중요
    "연이자율(4)": 1.5,            # 중요
    "최종이자 지급일(5)": 1.0,     # 보통
    "만기일(6)": 1.0,              # 보통
    "인출제한 등(7)": 0.5          # 낮은 중요도
}


def load_ground_truth(csv_path: str) -> List[Dict[str, str]]:
    """Ground truth CSV 파일 로드"""
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def extract_table_from_image(image_path: str) -> Tuple[bool, List[Dict[str, str]]]:
    """
    이미지에서 표 추출
    
    Returns:
        (표 감지 여부, 추출된 데이터)
    """
    img = Image.open(image_path)
    page_height = img.size[1]
    
    # OCR 추출
    engine = get_engine()
    tokens = engine.extract(img)
    
    # 행 그룹화
    line_builder = LineBuilder(page_height=page_height)
    rows = line_builder.build_lines(tokens)
    
    # 표 영역 분할
    chunker = Chunker()
    tables = chunker.split_into_chunks(rows)
    
    # 표 감지 여부
    table_detected = "금융상품_내역" in tables
    
    # 표 데이터 추출
    extracted_rows = []
    
    if table_detected:
        table_rows = tables["금융상품_내역"]
        
        schema = next((s for s in BANK_INQUIRY_SCHEMAS if s.table_name == "금융상품_내역"), None)
        if schema and schema.headers:
            headers = schema.headers
            
            for row in table_rows:
                row_texts = [token[2] for token in row]
                
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row_texts):
                        row_dict[f"{header}({i+1})"] = row_texts[i]
                    else:
                        row_dict[f"{header}({i+1})"] = ""
                
                extracted_rows.append(row_dict)
    
    return table_detected, extracted_rows


def calculate_weighted_score(field_stats: Dict, weights: Dict[str, float]) -> float:
    """
    필드별 가중치를 적용한 점수 계산
    
    Args:
        field_stats: 필드별 통계
        weights: 필드별 가중치
    
    Returns:
        가중 평균 점수 (0.0 ~ 1.0)
    """
    total_weight = 0.0
    weighted_sum = 0.0
    
    for field, stats in field_stats.items():
        weight = weights.get(field, 1.0)
        similarity = stats["similarity"] / stats["count"] if stats["count"] > 0 else 0.0
        
        weighted_sum += similarity * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0


def benchmark_single_image(
    image_path: str,
    ground_truth_rows: List[Dict[str, str]],
    should_have_table: bool
) -> Dict:
    """
    단일 이미지 벤치마킹
    
    Returns:
        벤치마크 결과 딕셔너리
    """
    # 표 추출
    table_detected, ocr_rows = extract_table_from_image(image_path)
    
    # 표 인식 성공 여부
    detection_correct = (table_detected == should_have_table)
    
    # 표가 없어야 하는데 감지된 경우 (False Positive)
    if not should_have_table and table_detected:
        return {
            "image": Path(image_path).name,
            "should_have_table": should_have_table,
            "table_detected": table_detected,
            "detection_correct": False,
            "false_positive": True,
            "total_cells": 0,
            "matched_cells": 0,
            "accuracy": 0.0,
            "avg_similarity": 0.0,
            "avg_cer": 1.0,
            "weighted_score": 0.0,
            "field_stats": {}
        }
    
    # 표가 있어야 하는데 감지되지 않은 경우 (False Negative)
    if should_have_table and not table_detected:
        return {
            "image": Path(image_path).name,
            "should_have_table": should_have_table,
            "table_detected": table_detected,
            "detection_correct": False,
            "false_negative": True,
            "total_cells": 0,
            "matched_cells": 0,
            "accuracy": 0.0,
            "avg_similarity": 0.0,
            "avg_cer": 1.0,
            "weighted_score": 0.0,
            "field_stats": {}
        }
    
    # 표가 정상적으로 감지된 경우 - 정확도 측정
    if not should_have_table:  # 표가 없어야 하고 실제로도 없음
        return {
            "image": Path(image_path).name,
            "should_have_table": should_have_table,
            "table_detected": table_detected,
            "detection_correct": True,
            "total_cells": 0,
            "matched_cells": 0,
            "accuracy": 1.0,
            "avg_similarity": 1.0,
            "avg_cer": 0.0,
            "weighted_score": 1.0,
            "field_stats": {}
        }
    
    # 표가 있고 정상 감지됨 - 내용 비교
    total_cells = 0
    matched_cells = 0
    total_similarity = 0.0
    total_cer = 0.0
    field_stats = {}
    
    max_rows = min(len(ground_truth_rows), len(ocr_rows))
    
    for i in range(max_rows):
        gt_row = ground_truth_rows[i]
        ocr_row = ocr_rows[i] if i < len(ocr_rows) else {}
        
        for field in gt_row.keys():
            gt_value = gt_row.get(field, "")
            ocr_value = ocr_row.get(field, "")
            
            similarity = calculate_text_similarity(gt_value, ocr_value)
            cer = calculate_cer(gt_value, ocr_value)
            
            total_cells += 1
            total_similarity += similarity
            total_cer += cer
            
            if similarity > 0.9:
                matched_cells += 1
            
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
    
    accuracy = (matched_cells / total_cells * 100) if total_cells > 0 else 0
    avg_similarity = (total_similarity / total_cells) if total_cells > 0 else 0
    avg_cer = (total_cer / total_cells) if total_cells > 0 else 0
    weighted_score = calculate_weighted_score(field_stats, FIELD_WEIGHTS)
    
    return {
        "image": Path(image_path).name,
        "should_have_table": should_have_table,
        "table_detected": table_detected,
        "detection_correct": detection_correct,
        "total_cells": total_cells,
        "matched_cells": matched_cells,
        "accuracy": accuracy,
        "avg_similarity": avg_similarity,
        "avg_cer": avg_cer,
        "weighted_score": weighted_score,
        "field_stats": field_stats
    }


def run_batch_benchmark(
    image_dir: str,
    ground_truth_csv: str,
    output_dir: str = "./benchmark_results"
) -> Dict:
    """
    배치 벤치마킹 실행
    
    Returns:
        전체 벤치마크 결과
    """
    image_path = Path(image_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("배치 벤치마킹 시작")
    print("=" * 80)
    print(f"이미지 디렉토리: {image_path}")
    print(f"Ground Truth: {ground_truth_csv}")
    print(f"PP-Structure 사용: {Config.USE_PP_STRUCTURE}")
    print()
    
    # Ground truth 로드
    gt_rows = load_ground_truth(ground_truth_csv)
    print(f"[1/3] Ground Truth 로드: {len(gt_rows)} 행")
    
    # 이미지 파일 목록
    image_files = sorted(image_path.glob("*.jpg")) + sorted(image_path.glob("*.png"))
    print(f"[2/3] 이미지 파일 확인: {len(image_files)} 개")
    print()
    
    # 각 이미지 벤치마킹
    print("[3/3] 이미지별 벤치마킹 실행:")
    print("-" * 80)
    
    results = []
    
    for img_file in image_files:
        should_have_table = img_file.name in IMAGES_WITH_TABLES
        
        print(f"처리 중: {img_file.name} (표 {'있음' if should_have_table else '없음'})")
        
        result = benchmark_single_image(str(img_file), gt_rows, should_have_table)
        results.append(result)
        
        # 간단한 결과 출력
        if result["detection_correct"]:
            status = "✅"
        else:
            status = "❌"
        
        print(f"  {status} 표 인식: {'성공' if result['detection_correct'] else '실패'}")
        
        if result.get("total_cells", 0) > 0:
            print(f"     정확도: {result['accuracy']:.2f}% | "
                  f"유사도: {result['avg_similarity']:.4f} | "
                  f"CER: {result['avg_cer']:.4f} | "
                  f"가중 점수: {result['weighted_score']:.4f}")
        print()
    
    # 전체 통계 계산
    total_images = len(results)
    correct_detections = sum(1 for r in results if r["detection_correct"])
    false_positives = sum(1 for r in results if r.get("false_positive", False))
    false_negatives = sum(1 for r in results if r.get("false_negative", False))
    
    # 표가 정확히 인식된 이미지 중 내용 통계
    content_results = [r for r in results if r["detection_correct"] and r["total_cells"] > 0]
    
    if content_results:
        avg_accuracy = sum(r["accuracy"] for r in content_results) / len(content_results)
        avg_similarity = sum(r["avg_similarity"] for r in content_results) / len(content_results)
        avg_cer = sum(r["avg_cer"] for r in content_results) / len(content_results)
        avg_weighted_score = sum(r["weighted_score"] for r in content_results) / len(content_results)
    else:
        avg_accuracy = 0.0
        avg_similarity = 0.0
        avg_cer = 1.0
        avg_weighted_score = 0.0
    
    # 필드별 통합 통계
    aggregated_field_stats = {}
    for result in content_results:
        for field, stats in result.get("field_stats", {}).items():
            if field not in aggregated_field_stats:
                aggregated_field_stats[field] = {
                    "count": 0,
                    "similarity": 0.0,
                    "cer": 0.0,
                    "matched": 0,
                    "weight": FIELD_WEIGHTS.get(field, 1.0)
                }
            
            aggregated_field_stats[field]["count"] += stats["count"]
            aggregated_field_stats[field]["similarity"] += stats["similarity"]
            aggregated_field_stats[field]["cer"] += stats["cer"]
            aggregated_field_stats[field]["matched"] += stats["matched"]
    
    # 결과 요약
    summary = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "use_pp_structure": Config.USE_PP_STRUCTURE,
            "enable_layout_analysis": Config.ENABLE_LAYOUT_ANALYSIS,
            "ocr_lang": Config.OCR_LANG,
        },
        "table_detection": {
            "total_images": total_images,
            "correct_detections": correct_detections,
            "detection_rate": correct_detections / total_images * 100,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        },
        "content_accuracy": {
            "images_with_content": len(content_results),
            "avg_accuracy": avg_accuracy,
            "avg_similarity": avg_similarity,
            "avg_cer": avg_cer,
            "avg_weighted_score": avg_weighted_score
        },
        "field_stats": aggregated_field_stats,
        "image_results": results
    }
    
    # 결과 출력
    print("=" * 80)
    print("벤치마크 결과 요약")
    print("=" * 80)
    print()
    print("표 인식 성공률:")
    print(f"  총 이미지: {total_images}")
    print(f"  정확한 인식: {correct_detections} ({summary['table_detection']['detection_rate']:.2f}%)")
    print(f"  False Positive (표 없는데 인식): {false_positives}")
    print(f"  False Negative (표 있는데 미인식): {false_negatives}")
    print()
    
    if content_results:
        print("내용 정확도 (표가 정확히 인식된 이미지 기준):")
        print(f"  평균 정확도: {avg_accuracy:.2f}%")
        print(f"  평균 유사도: {avg_similarity:.4f}")
        print(f"  평균 CER: {avg_cer:.4f}")
        print(f"  가중 평균 점수: {avg_weighted_score:.4f}")
        print()
        
        print("필드별 성능 (중요도순):")
        print("-" * 80)
        
        # 가중치 순으로 정렬
        sorted_fields = sorted(
            aggregated_field_stats.items(),
            key=lambda x: x[1]["weight"],
            reverse=True
        )
        
        for field, stats in sorted_fields:
            similarity = stats["similarity"] / stats["count"] if stats["count"] > 0 else 0
            cer = stats["cer"] / stats["count"] if stats["count"] > 0 else 0
            accuracy = stats["matched"] / stats["count"] * 100 if stats["count"] > 0 else 0
            weight = stats["weight"]
            
            print(f"{field} (가중치: {weight}):")
            print(f"  정확도: {accuracy:.2f}% | 유사도: {similarity:.4f} | CER: {cer:.4f}")
    
    print("=" * 80)
    
    # JSON 파일로 저장
    mode_name = "ppstructure" if Config.USE_PP_STRUCTURE else "paddleocr"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = output_path / f"benchmark_{mode_name}_{timestamp}.json"
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 결과 저장: {json_file}")
    
    return summary


if __name__ == "__main__":
    # 배치 벤치마킹 실행
    results = run_batch_benchmark(
        image_dir="./image",
        ground_truth_csv="label_bank_audit_letter.csv",
        output_dir="./benchmark_results"
    )
