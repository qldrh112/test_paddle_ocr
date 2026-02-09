"""
PaddleOCR 기본 성능 테스트
모든 커스텀 로직 제거, 순수 PaddleOCR API만 사용  
"""

from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
from datetime import datetime

# 테스트 이미지 (Google Gemini가 성공적으로 인식한 이미지)
image_path = "image/bank_audit_letter-0003.jpg"

# 출력 파일
output_file = f"paddleocr_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def log(msg, file=None):
    """화면과 파일에 동시 출력"""
    print(msg)
    if file:
        file.write(msg + "\n")

with open(output_file, "w", encoding="utf-8") as f:
    log("=" * 80, f)
    log("PaddleOCR 기본 성능 테스트", f)
    log("=" * 80, f)
    log("", f)
    
    # 1. 이미지 로드
    img = Image.open(image_path)
    log(f"이미지: {image_path}", f)
    log(f"크기: {img.size}", f)
    log("", f)
    
    # 2. PaddleOCR 초기화 (기본 설정)
    log("PaddleOCR 초기화 중...", f)
    ocr = PaddleOCR(
        lang='korean',
        use_angle_cls=True,  # 각도 분류 사용
        use_gpu=False,
        show_log=False
    )
    log("초기화 완료", f)
    log("", f)
    
    # 3. OCR 실행
    log("OCR 실행 중...", f)
    img_np = np.array(img)
    result = ocr.ocr(img_np, cls=True)
    log("OCR 완료", f)
    log("", f)
    
    # 4. 결과 출력
    if result and result[0]:
        log(f"추출된 토큰 수: {len(result[0])}", f)
        log("", f)
        log("추출 결과 전체:", f)
        log("=" * 80, f)
        
        for idx, line in enumerate(result[0], 1):
            bbox = line[0]
            text, conf = line[1]
            y_center = (bbox[0][1] + bbox[2][1]) / 2
            x_min = min(p[0] for p in bbox)
            
            log(f"{idx:3d}. [{conf:.3f}] {text:40s} (y={y_center:6.1f}, x={x_min:6.1f})", f)
        
        log("", f)
        log("=" * 80, f)
        log("전체 텍스트 (공백으로 연결):", f)
        log("=" * 80, f)
        
        full_text = " ".join([line[1][0] for line in result[0]])
        log(full_text, f)
        log("", f)
        
        # 5. 키워드 검색
        log("=" * 80, f)
        log("금융거래조회서 관련 키워드 검색:", f)
        log("=" * 80, f)
        
        keywords = ["금융상품", "계좌번호", "금액", "연이자율", "예금", "적금", "만기일"]
        found_keywords = []
        
        for line in result[0]:
            text = line[1][0]
            for keyword in keywords:
                if keyword in text:
                    found_keywords.append((keyword, text, line[1][1]))  # (키워드, 텍스트, 신뢰도)
        
        if found_keywords:
            log(f"발견된 키워드: {len(found_keywords)}개", f)
            for keyword, text, conf in found_keywords:
                log(f"  - '{keyword}' in '{text}' (conf: {conf:.3f})", f)
        else:
            log("키워드를 찾을 수 없습니다.", f)
        
    else:
        log("❌ OCR 결과가 없습니다.", f)
    
    log("", f)
    log("=" * 80, f)
    log("테스트 완료", f)
    log("=" * 80, f)
    log(f"\n결과 파일 저장: {output_file}", f)

print(f"\n✅ 결과 파일 생성: {output_file}")

