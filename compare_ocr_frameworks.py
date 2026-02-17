"""
결과 비교 및 분석 스크립트

Tesseract, EasyOCR의 테스트 결과를 비교 분석합니다.
"""

import json
from pathlib import Path
import pandas as pd
from datetime import datetime

def compare_ocr_results(tesseract_summary, easyocr_summary, output_path):
    """
    OCR 프레임워크 결과 비교
    
    Args:
        tesseract_summary: Tesseract 요약 파일 경로
        easyocr_summary: EasyOCR 요약 파일 경로
        output_path: 비교 결과 저장 경로
    """
    # 요약 파일 로드
    with open(tesseract_summary, 'r', encoding='utf-8') as f:
        tess_data = json.load(f)
    
    with open(easyocr_summary, 'r', encoding='utf-8') as f:
        easy_data = json.load(f)
    
    print(f"\n{'='*80}")
    print("OCR 프레임워크 성능 비교")
    print(f"{'='*80}\n")
    
    # 전체 성능 비교
    print("## 전체 성능 비교\n")
    print(f"| 항목 | Tesseract OCR | EasyOCR |")
    print(f"|------|---------------|---------|")
    print(f"| 총 이미지 | {tess_data['total_images']}개 | {easy_data['total_images']}개 |")
    print(f"| 초기화 시간 | - | {easy_data['init_time']:.2f}초 |")
    print(f"| 총 처리 시간 | {tess_data['total_ocr_time']:.2f}초 | {easy_data['total_ocr_time']:.2f}초 |")
    print(f"| 평균 처리 시간 | {tess_data['avg_time_per_image']:.2f}초 | {easy_data['avg_time_per_image']:.2f}초 |")
    print(f"| 추출 단위 | {tess_data['total_words']}개 (단어) | {easy_data['total_regions']}개 (영역) |")
    print(f"| 평균 개수 | {tess_data['avg_words_per_image']:.1f}개 | {easy_data['avg_regions_per_image']:.1f}개 |\n")
    
    # 이미지별 비교
    print("\n## 이미지별 처리 시간 비교\n")
    print(f"| 이미지 | Tesseract (초) | EasyOCR (초) | 차이 |")
    print(f"|--------|----------------|--------------|------|")
    
    comparison_data = []
    for tess_result in tess_data['results']:
        image_name = tess_result['image']
        # EasyOCR 결과 찾기
        easy_result = next((r for r in easy_data['results'] if r['image'] == image_name), None)
        
        if easy_result:
            tess_time = tess_result['ocr_time']
            easy_time = easy_result['ocr_time']
            diff = easy_time - tess_time
            diff_pct = (diff / tess_time * 100) if tess_time > 0 else 0
            
            print(f"| {image_name} | {tess_time:.2f} | {easy_time:.2f} | {diff:+.2f} ({diff_pct:+.1f}%) |")
            
            comparison_data.append({
                'image': image_name,
                'tesseract_time': tess_time,
                'tesseract_words': tess_result['total_words'],
                'tesseract_conf': tess_result['avg_confidence'],
                'easyocr_time': easy_time,
                'easyocr_regions': easy_result['total_regions'],
                'easyocr_conf': easy_result['avg_confidence'],
                'time_diff': diff,
                'time_diff_pct': diff_pct
            })
    
    # 신뢰도 비교
    print("\n## 평균 신뢰도 비교\n")
    print(f"| 이미지 | Tesseract | EasyOCR | 차이 |")
    print(f"|--------|-----------|---------|------|")
    
    for data in comparison_data:
        tess_conf = data['tesseract_conf']
        easy_conf = data['easyocr_conf']
        conf_diff = easy_conf - tess_conf
        
        print(f"| {data['image']} | {tess_conf:.3f} | {easy_conf:.3f} | {conf_diff:+.3f} |")
    
    # 종합 분석
    print("\n## 종합 분석\n")
    
    faster_count = sum(1 for d in comparison_data if d['time_diff'] < 0)
    avg_tess_time = tess_data['avg_time_per_image']
    avg_easy_time = easy_data['avg_time_per_image']
    avg_tess_conf = sum(r['avg_confidence'] for r in tess_data['results']) / len(tess_data['results'])
    avg_easy_conf = sum(r['avg_confidence'] for r in easy_data['results']) / len(easy_data['results'])
    
    print(f"**처리 속도**:")
    print(f"- Tesseract가 더 빠른 이미지: {faster_count}/{len(comparison_data)}개")
    print(f"- Tesseract 평균: {avg_tess_time:.2f}초/이미지")
    print(f"- EasyOCR 평균: {avg_easy_time:.2f}초/이미지 (초기화 {easy_data['init_time']:.2f}초 제외)")
    
    if avg_tess_time < avg_easy_time:
        speedup = ((avg_easy_time - avg_tess_time) / avg_easy_time * 100)
        print(f"- **Tesseract가 {speedup:.1f}% 더 빠름** ✓")
    else:
        speedup = ((avg_tess_time - avg_easy_time) / avg_tess_time * 100)
        print(f"- EasyOCR이 {speedup:.1f}% 더 빠름")
    
    print(f"\n**신뢰도**:")
    print(f"- Tesseract 평균 신뢰도: {avg_tess_conf:.3f}")
    print(f"- EasyOCR 평균 신뢰도: {avg_easy_conf:.3f}")
    
    if avg_easy_conf > avg_tess_conf:
        conf_improvement = ((avg_easy_conf - avg_tess_conf) / avg_tess_conf * 100)
        print(f"- **EasyOCR이 {conf_improvement:.1f}% 더 높은 신뢰도** ✓")
    else:
        conf_diff = ((avg_tess_conf - avg_easy_conf) / avg_easy_conf * 100)
        print(f"- Tesseract가 {conf_diff:.1f}% 더 높은 신뢰도")
    
    # 결과 저장
    output_dir = Path(output_path)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df.to_csv(output_dir / "comparison.csv", index=False, encoding='utf-8-sig')
    
    summary_report = {
        'test_date': datetime.now().isoformat(),
        'tesseract': {
            'avg_time': avg_tess_time,
            'avg_confidence': avg_tess_conf,
            'total_words': tess_data['total_words']
        },
        'easyocr': {
            'init_time': easy_data['init_time'],
            'avg_time': avg_easy_time,
            'avg_confidence': avg_easy_conf,
            'total_regions': easy_data['total_regions']
        },
        'comparison': comparison_data
    }
    
    with open(output_dir / "comparison_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n비교 결과 저장: {output_dir}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    compare_ocr_results(
        "output/tesseract_results/tesseract_summary.json",
        "output/easyocr_results/easyocr_summary.json",
        "output/comparison"
    )
