"""
EasyOCR을 사용한 표 추출 테스트 스크립트

Tesseract와 EasyOCR의 성능을 비교합니다.
"""

import easyocr
import cv2
import numpy as np
from pathlib import Path
import time
import json

def test_easyocr_on_image(image_path: str):
    """
    EasyOCR로 이미지에서 텍스트 추출
    
    Args:
        image_path: 이미지 파일 경로
    """
    print(f"\n{'='*80}")
    print(f"EasyOCR 테스트: {Path(image_path).name}")
    print(f"{'='*80}\n")
    
    # EasyOCR reader 초기화 (한국어 + 영어)
    print("EasyOCR Reader 초기화 중 (ko+en)...")
    start_init = time.time()
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    init_time = time.time() - start_init
    print(f"초기화 완료 ({init_time:.2f}초)\n")
    
    # 이미지 로드
    img = cv2.imread(image_path)
    print(f"이미지 크기: {img.shape}\n")
    
    # OCR 수행
    print("OCR 수행 중...")
    start_ocr = time.time()
    results = reader.readtext(image_path, detail=1, paragraph=False)
    ocr_time = time.time() - start_ocr
    print(f"OCR 완료 ({ocr_time:.2f}초)\n")
    
    # 결과 출력
    print(f"{'='*80}")
    print(f"추출된 텍스트 영역: {len(results)}개")
    print(f"{'='*80}\n")
    
    # 신뢰도별 분류
    high_conf = []
    medium_conf = []
    low_conf = []
    
    for i, (bbox, text, confidence) in enumerate(results[:50], 1):  # 처음 50개만
        if confidence >= 0.7:
            high_conf.append((text, confidence))
        elif confidence >= 0.5:
            medium_conf.append((text, confidence))
        else:
            low_conf.append((text, confidence))
        
        print(f"[{i}] 신뢰도: {confidence:.3f} | 텍스트: {text}")
        if i % 10 == 0:
            print()
    
    if len(results) > 50:
        print(f"\n... 외 {len(results) - 50}개 생략\n")
    
    # 통계
    print(f"\n{'='*80}")
    print("신뢰도 통계")
    print(f"{'='*80}")
    print(f"높음 (≥70%): {len(high_conf)}개")
    print(f"중간 (50-70%): {len(medium_conf)}개")
    print(f"낮음 (<50%): {len(low_conf)}개")
    print(f"평균 신뢰도: {np.mean([conf for _, _, conf in results]):.3f}")
    
    # 처리 시간
    print(f"\n{'='*80}")
    print("처리 시간")
    print(f"{'='*80}")
    print(f"초기화: {init_time:.2f}초")
    print(f"OCR 수행: {ocr_time:.2f}초")
    print(f"총 시간: {init_time + ocr_time:.2f}초")
    
    # 결과 저장
    output_dir = Path("output/easyocr_test")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    output_file = output_dir / f"{Path(image_path).stem}_easyocr.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'image': str(image_path),
            'total_regions': len(results),
            'init_time': init_time,
            'ocr_time': ocr_time,
            'avg_confidence': float(np.mean([conf for _, _, conf in results])),
            'results': [
                {
                    'bbox': bbox,
                    'text': text,
                    'confidence': float(confidence)
                }
                for bbox, text, confidence in results
            ]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n결과 저장: {output_file}")
    print(f"{'='*80}\n")
    
    return results

if __name__ == "__main__":
    # 테스트 이미지
    test_image = "test/image/bank_audit_letter-0003.jpg"
    
    print("\n" + "="*80)
    print("EasyOCR 성능 테스트")
    print("="*80)
    
    if Path(test_image).exists():
        results = test_easyocr_on_image(test_image)
    else:
        print(f"오류: 이미지를 찾을 수 없습니다: {test_image}")
