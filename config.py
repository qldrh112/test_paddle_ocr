"""
audit-inquiry-automation1/config.py

시스템 설정 중앙 관리 [US-120 준수]
운영 중 환경변수로 튜닝 가능한 매개변수 정의
"""

import os
from pathlib import Path


class Config:
    """시스템 설정 클래스"""
    
    # ==================== OCR 설정 ====================
    
    # OCR 신뢰도 임계값 (운영 중 조정 가능)
    # 이 값보다 낮은 confidence를 가진 토큰은 PENDING_REVIEW 플래그 설정
    OCR_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.7")
    )
    
    # PaddleOCR GPU 사용 여부
    USE_GPU: bool = os.getenv("USE_GPU", "True").lower() == "true"
    
    # OCR 언어 설정
    OCR_LANG: str = os.getenv("OCR_LANG", "korean")
    
    # ==================== 좌표 정규화 설정 ====================
    
    # 페이지 높이 정규화 기준 (픽셀)
    # 모든 좌표를 이 값 기준으로 0~1000으로 정규화
    NORMALIZED_PAGE_HEIGHT: float = 1000.0
    
    # 같은 행으로 간주할 Y 좌표 차이 (정규화된 좌표 기준)
    LINE_Y_THRESHOLD: float = 10.0
    
    # ==================== 전처리 설정 ====================
    
    # Deskewing (기울어짐 보정) 활성화 여부
    # ⭐ 순수 OCR 접근: 전처리 비활성화로 데이터 손실 방지
    ENABLE_DESKEWING: bool = os.getenv("ENABLE_DESKEWING", "False").lower() == "true"
    
    # Deskewing 각도 임계값 (도 단위)
    # 이 값 이상의 기울어짐만 보정 (성능 최적화)
    DESKEW_ANGLE_THRESHOLD: float = 0.5
    
    # ⚠️ Technical Lead's Advice: Deskewing 성능 최적화
    # 고해상도 이미지에서 HoughLines 부하 방지를 위한 축소 비율
    DESKEW_RESIZE_FACTOR: float = 0.5  # 50% 축소하여 각도 계산
    
    # 이진화 활성화 여부 (OCR 품질 개선을 위해 비활성화 가능)
    ENABLE_BINARIZATION: bool = os.getenv("ENABLE_BINARIZATION", "False").lower() == "true"
    
    # 이진화 설정 (전처리 설정 완화)
    ADAPTIVE_THRESHOLD_BLOCK_SIZE: int = 11  # 이웃 픽셀 범위
    ADAPTIVE_THRESHOLD_C: int = 8            # 평균에서 뺄 상수 (2→8로 상향: 획 보존 우선)
    
    # 노이즈 제거 커널 크기
    MORPHOLOGY_KERNEL_SIZE: tuple = (2, 2)
    
    # ==================== 후처리 설정 ====================
    
    # 금액-통화 병합 시 같은 행으로 간주할 거리 (정규화된 좌표 기준)
    CURRENCY_MERGE_THRESHOLD: float = 10.0
    
    # 퍼지 앵커 매칭 설정 (Req-112: 조회처 자동 분류)
    ENABLE_FUZZY_ANCHOR_MATCHING: bool = True
    FUZZY_MATCH_THRESHOLD: float = 0.7  # 70% 이상 유사도면 매칭 (80%→70%로 완화)
    
    # ==================== PDF 처리 설정 ====================
    
    # A1/A2 경로 판정 임계값
    # 디지털 PDF 판단을 위한 최소 텍스트 길이
    DIGITAL_PDF_TEXT_THRESHOLD: int = 100
    
    # ⚠️ Technical Lead's Advice: A1/A2 판정 개선 (향후 고도화)
    # PDF 내 이미지 객체 비율 임계값 (미구현)
    # IMAGE_OBJECT_RATIO_THRESHOLD: float = 0.5
    
    # ==================== 디버그 설정 ====================
    
    # 디버그 모드 활성화 여부
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    # 디버그 출력 디렉토리
    DEBUG_OUTPUT_DIR: Path = Path("./debug_output")
    
    # OCR 입력/출력 이미지 저장 여부
    SAVE_OCR_DEBUG_IMAGES: bool = DEBUG_MODE
    
    @classmethod
    def ensure_debug_dir(cls):
        """디버그 모드 활성화 시 출력 디렉토리 생성"""
        if cls.DEBUG_MODE:
            cls.DEBUG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """현재 설정 요약 반환 (로깅용)"""
        return {
            "ocr_confidence_threshold": cls.OCR_CONFIDENCE_THRESHOLD,
            "use_gpu": cls.USE_GPU,
            "enable_deskewing": cls.ENABLE_DESKEWING,
            "debug_mode": cls.DEBUG_MODE,
        }
