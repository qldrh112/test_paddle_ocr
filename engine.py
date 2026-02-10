"""
audit-inquiry-automation1/engine.py

PP-Structure 기반 OCR 엔진 (표 구조 인식)
Layout Analysis + Table Structure Recognition
"""

import numpy as np
from PIL import Image
from typing import List, Tuple, Any, Dict
from datetime import datetime
import json

from config import Config
from preprocessor import preprocess_pipeline, save_debug_image
from exceptions import OcrExtractionError

try:
    import torch
except ImportError:
    torch = None


class OcrEngine:
    """
    PP-Structure 기반 OCR 엔진 (싱글톤)
    
    Layout Analysis로 표 영역 감지 후 SLANet 모델로 표 구조 추출
    기존 파이프라인 호환성을 위해 토큰 형식으로 변환
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
        """PP-Structure 또는 PaddleOCR 모델 로딩 (환경 자동 감지)"""
        if self.reader:
            return
        
        # GPU 사용 가능 여부 확인
        use_gpu = False
        if torch is not None:
            use_gpu = torch.cuda.is_available() if hasattr(torch, 'cuda') else False
        
        # Config에서 설정 로드
        use_gpu = use_gpu and Config.USE_GPU
        
        if Config.USE_PP_STRUCTURE:
            # PP-Structure 초기화 (표 구조 인식 엔진)
            from paddleocr import PPStructure
            from pathlib import Path
            
            # 오프라인 모델 로딩 설정
            model_kwargs = {
                # Layout 모델용 언어 (영어/중국어만 지원)
                "lang": Config.LAYOUT_LANG,
                "use_gpu": use_gpu,
                "show_log": False,
                # Layout Analysis 활성화
                "layout": Config.ENABLE_LAYOUT_ANALYSIS,
                # 표 구조 인식 활성화
                "table": True,
                # OCR도 함께 수행 (표 내부 텍스트 추출)
                "ocr": True,
                # 낮은 신뢰도도 수용
                "drop_score": 0.1,
            }
            
            # 오프라인 모델 경로 지정 (설정된 경우)
            if Config.PPSTRUCTURE_MODEL_DIR:
                model_dir = Path(Config.PPSTRUCTURE_MODEL_DIR)
                
                if model_dir.exists():
                    print(f"[PP-Structure] 오프라인 모델 로딩: {model_dir}")
                    
                    # 모델 경로 자동 탐색
                    # PaddleOCR 모델 구조: .paddleocr/whl/{모델명}/
                    # 예: .paddleocr/whl/en_ppocr_mobile_v2.0_table_det/
                    
                    # Layout 모델은 layout 모드에서 자동으로 로딩되므로 생략
                    # OCR 모델 경로만 지정
                    
                    # 영어 모델 경로 예시
                    det_model = model_dir / "whl" / "en_PP-OCRv3_det_infer"
                    rec_model = model_dir / "whl" / "en_PP-OCRv3_rec_infer"
                    table_model = model_dir / "whl" / "en_ppstructure_mobile_v2.0_SLANet"
                    
                    # 한국어 모델 경로 예시 (OCR용)
                    korean_det_model = model_dir / "whl" / "korean_PP-OCRv3_det_infer"
                    korean_rec_model = model_dir / "whl" / "korean_PP-OCRv3_rec_infer"
                    
                    # OCR 언어에 따라 모델 선택
                    if Config.OCR_LANG == "korean":
                        if korean_det_model.exists():
                            model_kwargs["det_model_dir"] = str(korean_det_model)
                        if korean_rec_model.exists():
                            model_kwargs["rec_model_dir"] = str(korean_rec_model)
                    else:
                        if det_model.exists():
                            model_kwargs["det_model_dir"] = str(det_model)
                        if rec_model.exists():
                            model_kwargs["rec_model_dir"] = str(rec_model)
                    
                    # Table 모델 경로 (Layout 언어 기준)
                    if table_model.exists():
                        model_kwargs["table_model_dir"] = str(table_model)
                    
                    print(f"  - OCR Lang: {Config.OCR_LANG}")
                    if "det_model_dir" in model_kwargs:
                        print(f"  - Det Model: {Path(model_kwargs['det_model_dir']).name}")
                    if "rec_model_dir" in model_kwargs:
                        print(f"  - Rec Model: {Path(model_kwargs['rec_model_dir']).name}")
                    if "table_model_dir" in model_kwargs:
                        print(f"  - Table Model: {Path(model_kwargs['table_model_dir']).name}")
                else:
                    print(f"[PP-Structure] 모델 디렉토리를 찾을 수 없습니다: {model_dir}")
                    print("               온라인 모델 다운로드를 시도합니다...")
            
            self.reader = PPStructure(**model_kwargs)
            
            print(f"[PP-Structure Engine] 초기화 완료 (GPU: {use_gpu}, Layout: {Config.ENABLE_LAYOUT_ANALYSIS}, Lang: {Config.LAYOUT_LANG})")
        else:
            # 기존 PaddleOCR 초기화 (하위 호환성)
            from paddleocr import PaddleOCR
            
            self.reader = PaddleOCR(
                lang=Config.OCR_LANG,
                use_angle_cls=True,
                use_gpu=use_gpu,
                show_log=False,
                drop_score=0.1,
                det_db_unclip_ratio=1.5,
            )
            
            print(f"[PaddleOCR Engine] 초기화 완료 (GPU: {use_gpu})")
    
    def extract(
        self,
        pil_img: Image.Image
    ) -> List[Tuple[float, float, str, float]]:
        """
        이미지에서 텍스트 추출
        
        PP-Structure 사용 시: Layout Analysis → Table Structure → 토큰 변환
        PaddleOCR 사용 시: 기존 방식 유지
        
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
            timestamp = None
            if Config.DEBUG_MODE:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_debug_image(img_np, f"{timestamp}.png", step="0_original")
            
            # 2. 전처리 우회 (원본 이미지 사용)
            processed = img_np
            
            if Config.DEBUG_MODE:
                save_debug_image(processed, f"{timestamp}.png", step="1_preprocessed")
            
            # 3. PP-Structure 또는 PaddleOCR 실행
            if Config.USE_PP_STRUCTURE:
                tokens = self._extract_with_ppstructure(processed, timestamp)
            else:
                tokens = self._extract_with_paddleocr(processed, timestamp)
            
            # Y좌표(행) → X좌표(열) 순으로 정렬
            tokens.sort(key=lambda t: (t[0], t[1]))
            
            return tokens
        
        except Exception as e:
            raise OcrExtractionError(
                message=f"OCR 추출 실패: {str(e)}",
                state="FAILED_OCR_ERROR",
                original_exception=e
            )
    
    def _extract_with_ppstructure(
        self,
        img_np: np.ndarray,
        timestamp: str = None
    ) -> List[Tuple[float, float, str, float]]:
        """
        PP-Structure로 표 구조 추출 후 토큰 형식으로 변환
        
        Args:
            img_np: NumPy 이미지 배열
            timestamp: 디버그 타임스탬프
        
        Returns:
            [(center_y, min_x, text, confidence), ...]
        """
        # PP-Structure 실행
        results = self.reader(img_np)
        
        # 디버그: Layout 결과 저장
        if Config.DEBUG_MODE and timestamp:
            debug_path = Config.DEBUG_OUTPUT_DIR / f"{timestamp}_ppstructure_layout.json"
            with open(debug_path, "w", encoding="utf-8") as f:
                # Layout 정보만 추출 (간결하게)
                layout_info = []
                for item in results:
                    layout_info.append({
                        "type": item.get("type", "unknown"),
                        "bbox": item.get("bbox", []),
                        "score": item.get("score", 0.0)
                    })
                json.dump(layout_info, f, ensure_ascii=False, indent=2)
        
        tokens = []
        
        for item in results:
            item_type = item.get("type", "")
            
            # 표 영역만 처리
            if item_type == "table":
                tokens.extend(self._parse_table_structure(item, timestamp))
            # 일반 텍스트 영역도 처리 (표 외부 데이터)
            elif item_type == "text" and "res" in item:
                tokens.extend(self._parse_text_region(item))
        
        # 디버그: 추출된 토큰 저장
        if Config.DEBUG_MODE and timestamp and tokens:
            debug_path = Config.DEBUG_OUTPUT_DIR / f"{timestamp}_ppstructure_tokens.txt"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(f"PP-Structure 토큰 ({len(tokens)}건)\n")
                f.write("=" * 80 + "\n\n")
                for idx, (y, x, text, conf) in enumerate(tokens, 1):
                    f.write(f"[{idx}] {text} (conf: {conf:.4f})\n")
                    f.write(f"     y={y:.1f}, x={x:.1f}\n\n")
        
        return tokens
    
    def _parse_table_structure(
        self,
        table_item: Dict,
        timestamp: str = None
    ) -> List[Tuple[float, float, str, float]]:
        """
        표 구조 데이터를 토큰 리스트로 변환
        
        SLANet 모델의 출력(HTML/Cell 구조)을 기존 파이프라인 형식으로 변환
        
        Args:
            table_item: PP-Structure의 표 영역 결과
            timestamp: 디버그 타임스탬프
        
        Returns:
            [(center_y, min_x, text, confidence), ...]
        """
        tokens = []
        
        # 표 영역의 OCR 결과 추출
        if "res" not in table_item:
            return tokens
        
        ocr_results = table_item["res"]
        
        # 디버그: 표 구조 HTML 저장
        if Config.DEBUG_MODE and timestamp and "html" in table_item:
            debug_path = Config.DEBUG_OUTPUT_DIR / f"{timestamp}_table_structure.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(table_item["html"])
        
        # OCR 결과를 토큰으로 변환
        for cell in ocr_results:
            if "text" in cell and "bbox" in cell:
                bbox = cell["bbox"]
                text = cell["text"]
                conf = cell.get("confidence", cell.get("score", 0.9))
                
                # 좌표 계산 (bbox: [x1, y1, x2, y2])
                if len(bbox) == 4:
                    x1, y1, x2, y2 = bbox
                    center_y = (y1 + y2) / 2
                    min_x = x1
                    
                    tokens.append((center_y, min_x, text, conf))
        
        return tokens
    
    def _parse_text_region(
        self,
        text_item: Dict
    ) -> List[Tuple[float, float, str, float]]:
        """
        일반 텍스트 영역을 토큰 리스트로 변환
        
        Args:
            text_item: PP-Structure의 텍스트 영역 결과
        
        Returns:
            [(center_y, min_x, text, confidence), ...]
        """
        tokens = []
        
        if "res" not in text_item:
            return tokens
        
        for line in text_item["res"]:
            # 기존 PaddleOCR 형식과 동일
            if len(line) == 2:
                bbox, (text, conf) = line
                
                # 좌표 계산
                if len(bbox) >= 4:
                    center_y = (bbox[0][1] + bbox[2][1]) / 2
                    min_x = min(p[0] for p in bbox)
                    
                    tokens.append((center_y, min_x, text, conf))
        
        return tokens
    
    def _extract_with_paddleocr(
        self,
        img_np: np.ndarray,
        timestamp: str = None
    ) -> List[Tuple[float, float, str, float]]:
        """
        기존 PaddleOCR 방식으로 텍스트 추출 (하위 호환성)
        
        Args:
            img_np: NumPy 이미지 배열
            timestamp: 디버그 타임스탬프
        
        Returns:
            [(center_y, min_x, text, confidence), ...]
        """
        # OCR 실행
        results = self.reader.ocr(img_np, cls=True)
        
        # 결과 정규화
        tokens = []
        if results and results[0]:
            for line in results[0]:
                bbox, (text, conf) = line
                
                # 좌표 계산
                center_y = (bbox[0][1] + bbox[2][1]) / 2
                min_x = min(p[0] for p in bbox)
                
                tokens.append((center_y, min_x, text, conf))
        
        # 디버그: OCR 결과 저장
        if Config.DEBUG_MODE and timestamp and tokens:
            debug_path = Config.DEBUG_OUTPUT_DIR / f"{timestamp}_paddleocr_result.txt"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(f"PaddleOCR 결과 ({len(tokens)}건)\n")
                f.write("=" * 80 + "\n\n")
                for idx, (y, x, text, conf) in enumerate(tokens, 1):
                    f.write(f"[{idx}] {text} (conf: {conf:.4f})\n")
                    f.write(f"     y={y:.1f}, x={x:.1f}\n\n")
        
        return tokens


def get_engine() -> OcrEngine:
    """전역 OCR 엔진 인스턴스 반환"""
    return OcrEngine()
