"""
Tesseract OCR 성능 테스트 스크립트

test/image 디렉토리의 모든 이미지를 Tesseract로 처리하여
다른 OCR 프레임워크와 비교 가능한 결과를 생성합니다.
"""

import pytesseract
import cv2
import numpy as np
from pathlib import Path
import time
import json
from datetime import datetime

def test_tesseract_on_images(input_dir: str, output_dir: str):
    """
    디렉토리의 모든 이미지를 Tesseract로 처리
    
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
    print(f"Tesseract OCR 성능 테스트")
    print(f"{'='*80}\n")
    print(f"테스트 이미지: {len(image_files)}개")
    print(f"출력 디렉토리: {output_dir}\n")
    
    # Tesseract 버전 확인
    version_info = pytesseract.get_tesseract_version()
    print(f"Tesseract 버전: {version_info}\n")
    
    # 전체 결과 저장
    all_results = []
    total_ocr_time = 0
    total_words = 0
    
    # 각 이미지 처리
    for idx, image_file in enumerate(sorted(image_files), 1):
        print(f"[{idx}/{len(image_files)}] 처리 중: {image_file.name}")
        
        # 이미지 로드
        img = cv2.imread(str(image_file))
        
        # OCR 수행 (단어 단위로 상세 정보 추출)
        ocr_start = time.time()
        data = pytesseract.image_to_data(img, lang='kor+eng', output_type=pytesseract.Output.DICT)
        ocr_time = time.time() - ocr_start
        
        # 유효한 텍스트만 필터링 (신뢰도 > 0)
        valid_texts = []
        confidences = []
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0 and data['text'][i].strip():
                valid_texts.append({
                    'text': data['text'][i],
                    'confidence': int(data['conf'][i]) / 100.0,  # 0-1 범위로 정규화
                    'bbox': [
                        data['left'][i],
                        data['top'][i],
                        data['left'][i] + data['width'][i],
                        data['top'][i] + data['height'][i]
                    ]
                })
                confidences.append(int(data['conf'][i]) / 100.0)
        
        total_ocr_time += ocr_time
        total_words += len(valid_texts)
        
        # 통계
        avg_conf = np.mean(confidences) if confidences else 0
        
        print(f"  - OCR 시간: {ocr_time:.2f}초")
        print(f"  - 추출 단어: {len(valid_texts)}개")
        print(f"  - 평균 신뢰도: {avg_conf:.3f}\n")
        
        # 결과 저장
        result_data = {
            'image': image_file.name,
            'ocr_time': ocr_time,
            'total_words': len(valid_texts),
            'avg_confidence': float(avg_conf),
            'min_confidence': float(min(confidences)) if confidences else 0,
            'max_confidence': float(max(confidences)) if confidences else 0,
            'texts': valid_texts
        }
        
        all_results.append(result_data)
        
        # 개별 결과 JSON 저장
        json_path = output_path / f"{image_file.stem}_tesseract.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    # 요약 통계
    print(f"\n{'='*80}")
    print("최종 통계")
    print(f"{'='*80}")
    print(f"총 OCR 시간: {total_ocr_time:.2f}초")
    print(f"평균 처리 시간: {total_ocr_time / len(image_files):.2f}초/이미지")
    print(f"총 추출 단어: {total_words}개")
    print(f"평균 단어 수: {total_words / len(image_files):.1f}개/이미지")
    
    # 전체 요약 저장
    summary = {
        'framework': 'Tesseract OCR',
        'version': str(version_info),
        'test_date': datetime.now().isoformat(),
        'total_images': len(image_files),
        'total_ocr_time': total_ocr_time,
        'avg_time_per_image': total_ocr_time / len(image_files),
        'total_words': total_words,
        'avg_words_per_image': total_words / len(image_files),
        'results': all_results
    }
    
    summary_path = output_path / "tesseract_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n요약 저장: {summary_path}")
    print(f"{'='*80}\n")
    
    return summary

if __name__ == "__main__":
    test_tesseract_on_images("test/image", "output/tesseract_results")
