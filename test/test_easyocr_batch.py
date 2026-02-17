"""
EasyOCR 성능 테스트 스크립트

test/image 디렉토리의 모든 이미지를 EasyOCR로 처리하여
Tesseract와 비교 가능한 결과를 생성합니다.
"""

import easyocr
import cv2
import numpy as np
from pathlib import Path
import time
import json
import pandas as pd
from datetime import datetime

def test_easyocr_on_images(input_dir: str, output_dir: str):
    """
    디렉토리의 모든 이미지를 EasyOCR로 처리
    
    Args:
        input_dir: 입력 이미지 디렉토리
        output_dir: 결과 저장 디렉토리
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # 이미지 파일 찾기
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_files = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    print(f"\n{'='*80}")
    print(f"EasyOCR 성능 테스트")
    print(f"{'='*80}\n")
    print(f"테스트 이미지: {len(image_files)}개")
    print(f"출력 디렉토리: {output_dir}\n")
    
    # EasyOCR Reader 초기화
    print("EasyOCR Reader 초기화 중 (ko+en)...")
    init_start = time.time()
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    init_time = time.time() - init_start
    print(f"초기화 완료 ({init_time:.2f}초)\n")
    
    # 전체 결과 저장
    all_results = []
    total_ocr_time = 0
    total_regions = 0
    
    # 각 이미지 처리
    for idx, image_file in enumerate(sorted(image_files), 1):
        print(f"[{idx}/{len(image_files)}] 처리 중: {image_file.name}")
        
        # 이미지 로드
        img = cv2.imread(str(image_file))
        
        # OCR 수행
        ocr_start = time.time()
        results = reader.readtext(str(image_file), detail=1, paragraph=False)
        ocr_time = time.time() - ocr_start
        
        total_ocr_time += ocr_time
        total_regions += len(results)
        
        # 신뢰도 통계
        confidences = [conf for _, _, conf in results]
        avg_conf = np.mean(confidences) if confidences else 0
        
        print(f"  - OCR 시간: {ocr_time:.2f}초")
        print(f"  - 추출 영역: {len(results)}개")
        print(f"  - 평균 신뢰도: {avg_conf:.3f}\n")
        
        # 결과 저장
        result_data = {
            'image': image_file.name,
            'ocr_time': float(ocr_time),
            'total_regions': int(len(results)),
            'avg_confidence': float(avg_conf),
            'min_confidence': float(min(confidences)) if confidences else 0.0,
            'max_confidence': float(max(confidences)) if confidences else 0.0,
            'texts': [
                {
                    'bbox': [[float(p[0]), float(p[1])] for p in bbox],
                    'text': str(text),
                    'confidence': float(confidence)
                }
                for bbox, text, confidence in results
            ]
        }
        
        all_results.append(result_data)
        
        # 개별 결과 JSON 저장
        json_path = output_path / f"{image_file.stem}_easyocr.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    # 요약 통계
    print(f"\n{'='*80}")
    print("최종 통계")
    print(f"{'='*80}")
    print(f"초기화 시간: {init_time:.2f}초")
    print(f"총 OCR 시간: {total_ocr_time:.2f}초")
    print(f"평균 처리 시간: {total_ocr_time / len(image_files):.2f}초/이미지")
    print(f"총 추출 영역: {total_regions}개")
    print(f"평균 영역 수: {total_regions / len(image_files):.1f}개/이미지")
    
    # 전체 요약 저장
    summary = {
        'framework': 'EasyOCR',
        'test_date': datetime.now().isoformat(),
        'total_images': len(image_files),
        'init_time': init_time,
        'total_ocr_time': total_ocr_time,
        'avg_time_per_image': total_ocr_time / len(image_files),
        'total_regions': total_regions,
        'avg_regions_per_image': total_regions / len(image_files),
        'results': all_results
    }
    
    summary_path = output_path / "easyocr_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n요약 저장: {summary_path}")
    print(f"{'='*80}\n")
    
    return summary

if __name__ == "__main__":
    test_easyocr_on_images("test/image", "output/easyocr_results")
