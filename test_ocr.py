"""
audit-inquiry-automation1/test_ocr.py

간단한 OCR 테스트 스크립트
샘플 이미지에 대한 OCR 및 후처리 검증
"""

from PIL import Image
from pathlib import Path

from config import Config
from engine import get_engine
from postprocessor import FinancialPatternNormalizer, filter_low_confidence


def test_ocr_pipeline():
    """OCR 파이프라인 전체 테스트"""
    
    # 테스트 이미지 경로
    test_img_path = Path("bank_audit_letter_1page.png")
    
    if not test_img_path.exists():
        print(f"❌ 테스트 이미지가 없습니다: {test_img_path}")
        return
    
    print("=" * 80)
    print("PaddleOCR 금융거래조회서 표 추출 테스트")
    print("=" * 80)
    print()
    
    # 1. 이미지 로드
    print(f"[1/4] 이미지 로드: {test_img_path}")
    img = Image.open(test_img_path)
    print(f"      크기: {img.size}")
    print()
    
    # 2. OCR 엔진 획득 및 추출
    print("[2/4] OCR 엔진 초기화 및 텍스트 추출")
    engine = get_engine()
    tokens = engine.extract(img)
    print(f"      추출된 토큰 수: {len(tokens)}")
    print()
    
    # 3. 후처리: 금액-통화 병합
    print("[3/4] 후처리: 금액-통화 병합")
    normalizer = FinancialPatternNormalizer()
    page_height = img.size[1]  # 이미지 높이
    merged_tokens = normalizer.merge_amount_currency(tokens, page_height)
    print(f"      병합 후 토큰 수: {len(merged_tokens)}")
    print()
    
    # 4. 신뢰도 필터링
    print("[4/4] 신뢰도 필터링")
    filtered = filter_low_confidence(merged_tokens)
    
    low_conf_count = sum(1 for _, _, _, needs_review in filtered if needs_review)
    print(f"      검토 필요 토큰: {low_conf_count}/{len(filtered)}")
    print()
    
    # 결과 샘플 출력
    print("=" * 80)
    print("추출 결과 샘플 (처음 20개)")
    print("=" * 80)
    
    for idx, (y, x, text, needs_review) in enumerate(filtered[:20], 1):
        flag = "[⚠️ REVIEW]" if needs_review else ""
        print(f"{idx:2d}. {text:30s} {flag}")
    
    print()
    print("=" * 80)
    print("✅ 테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    # 디버그 모드 활성화 (선택적)
    # Config.DEBUG_MODE = True
    # Config.SAVE_OCR_DEBUG_IMAGES = True
    
    test_ocr_pipeline()
