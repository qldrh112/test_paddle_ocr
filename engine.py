"""
audit-inquiry-automation1/engine.py

PaddleOCR 래퍼 엔진 (전처리 통합)
환경 자동 감지 및 전처리 파이프라인 적용
"""

import numpy as np
from PIL import Image
from typing import List, Tuple, Any
from datetime import datetime

from config import Config
from preprocessor import preprocess_pipeline, save_debug_image
from exceptions import OcrExtractionError

try:
    import torch
except ImportError:
    torch = None


class OcrEngine:
    """
    PaddleOCR 래퍼 엔진 (싱글톤 + 전처리 통합)
    
    전처리 파이프라인을 적용하여 OCR 인식률 향상
    confidence 정보를 보존하여 후처리 단계에서 활용
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OcrEngine, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        
        self.reader = None
        self._initialized = True
    
    def initialize(self):
        """PaddleOCR 모델 로딩 (환경 자동 감지)"""
        if self.reader:
            return
        
        # GPU 사용 가능 여부 확인
        use_gpu = False
        if torch is not None:
            use_gpu = torch.cuda.is_available() if hasattr(torch, 'cuda') else False
        
        # Config에서 설정 로드
        use_gpu = use_gpu and Config.USE_GPU
        
        # PaddleOCR 초기화
        from paddleocr import PaddleOCR
        
        self.reader = PaddleOCR(
            lang=Config.OCR_LANG,
            use_angle_cls=True,
            use_gpu=use_gpu,
            show_log=False,
            # ⭐ 순수 OCR 접근: 낮은 신뢰도도 모두 수용하여 데이터 손실 방지
            drop_score=0.1,              # 0.35 → 0.1: 최대한 많은 토큰 수용
            det_db_unclip_ratio=1.5,      # 1.8 → 1.5: 기본값 사용
        )
        
        print(f"[OCR Engine] 초기화 완료 (GPU: {use_gpu})")
    
    def extract(
        self,
        pil_img: Image.Image
    ) -> List[Tuple[float, float, str, float]]:
        """
        이미지에서 텍스트 추출 (전처리 포함)
        
        Args:
            pil_img: PIL Image 객체
        
        Returns:
            [(center_y, min_x, text, confidence), ...]
        
        Raises:
            OcrExtractionError: OCR 추출 실패 시
        """
        try:
            # OCR 엔진 초기화 확인
            if not self.reader:
                self.initialize()
            
            # 1. PIL → NumPy 변환
            img_np = np.array(pil_img)
            
            # 디버그: 원본 이미지 저장
            if Config.DEBUG_MODE:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_debug_image(img_np, f"{timestamp}.png", step="0_original")
            
            # 2. 전처리 우회 (⭐ 순수 OCR 접근: 원본 이미지 사용)
            # 전처리를 완전히 비활성화하여 데이터 손실 방지
            processed = img_np
            
            # 디버그: 전처리 결과 저장
            if Config.DEBUG_MODE:
                save_debug_image(processed, f"{timestamp}.png", step="1_preprocessed")
            
            # 3. OCR 실행 (⚠️ cls=True로 변경: 각도 분류 활성화)
            results = self.reader.ocr(processed, cls=True)
            
            # 4. 결과 정규화 (confidence 포함)
            tokens = []
            if results and results[0]:
                for line in results[0]:
                    bbox, (text, conf) = line
                    
                    # 좌표 계산
                    center_y = (bbox[0][1] + bbox[2][1]) / 2
                    min_x = min(p[0] for p in bbox)
                    
                    tokens.append((center_y, min_x, text, conf))
            
            # 디버그: OCR 결과 저장
            if Config.DEBUG_MODE and tokens:
                debug_path = Config.DEBUG_OUTPUT_DIR / f"{timestamp}_ocr_result.txt"
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(f"OCR 결과 ({len(tokens)}건)\\n")
                    f.write("=" * 80 + "\\n\\n")
                    for idx, (y, x, text, conf) in enumerate(tokens, 1):
                        f.write(f"[{idx}] {text} (conf: {conf:.4f})\\n")
                        f.write(f"     y={y:.1f}, x={x:.1f}\\n\\n")
            
            # Y좌표(행) → X좌표(열) 순으로 정렬
            tokens.sort(key=lambda t: (t[0], t[1]))
            
            return tokens
        
        except Exception as e:
            # ⚠️ 아키텍처 보완: 예외 상태 명확히 정의
            raise OcrExtractionError(
                message=f"OCR 추출 실패: {str(e)}",
                state="FAILED_OCR_ERROR",
                original_exception=e
            )


def get_engine() -> OcrEngine:
    """전역 OCR 엔진 인스턴스 반환"""
    return OcrEngine()
