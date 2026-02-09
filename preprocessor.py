"""
audit-inquiry-automation1/preprocessor.py

이미지 전처리 모듈 [ADR-001]
OCR 인식률 향상을 위한 이미지 전처리 파이프라인

주요 기능:
- 이진화 (Binarization): 텍스트와 배경 분리
- 노이즈 제거: 스캔 노이즈 제거
- Deskewing: 문서 기울어짐 보정
"""

import cv2
import numpy as np
from typing import Optional

from config import Config
from exceptions import PreprocessingError


def binarize_image(img: np.ndarray) -> np.ndarray:
    """
    [ADR-001] 적응형 이진화로 표 영역 텍스트 선명화
    
    Args:
        img: 원본 이미지 (BGR 또는 Grayscale)
    
    Returns:
        이진화된 이미지 (Grayscale, 0 또는 255 값만)
    
    Raises:
        PreprocessingError: 이진화 실패 시
    """
    try:
        # 1. 그레이스케일 변환 (이미 그레이스케일이면 스킵)
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # 2. 적응형 가우시안 임계값 적용
        # 표 구조에서 각 셀마다 조명이 다를 수 있으므로 적응형 사용
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=Config.ADAPTIVE_THRESHOLD_BLOCK_SIZE,
            C=Config.ADAPTIVE_THRESHOLD_C
        )
        
        return binary
    
    except Exception as e:
        raise PreprocessingError(
            f"이진화 실패: {str(e)}",
            step="binarization"
        )


def denoise_image(img: np.ndarray) -> np.ndarray:
    """
    [ADR-001] 스캔 노이즈 제거로 오인식 방지
    
    Args:
        img: 이진화된 이미지
    
    Returns:
        노이즈 제거된 이미지
    
    Raises:
        PreprocessingError: 노이즈 제거 실패 시
    """
    try:
        # 모폴로지 닫힘 연산으로 작은 점 제거
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            Config.MORPHOLOGY_KERNEL_SIZE
        )
        denoised = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
        
        return denoised
    
    except Exception as e:
        raise PreprocessingError(
            f"노이즈 제거 실패: {str(e)}",
            step="denoising"
        )


def deskew_image(img: np.ndarray) -> np.ndarray:
    """
    [ADR-001] 문서 기울어짐 자동 보정
    
    ⚠️ Technical Lead's Advice 반영:
    - 고해상도 이미지는 축소하여 각도 계산 (성능 최적화)
    - 계산된 회전 행렬을 원본 이미지에 적용
    
    스캔 시 발생하는 미세한 각도 틀어짐을 감지하여 수평 정렬
    LineBuilder의 행 구성 정확도 향상
    
    Args:
        img: 원본 또는 전처리된 이미지
    
    Returns:
        기울어짐 보정된 이미지
    
    Raises:
        PreprocessingError: Deskewing 실패 시
    """
    if not Config.ENABLE_DESKEWING:
        return img  # Deskewing 비활성화 시 원본 반환
    
    try:
        # 원본 크기 저장
        original_shape = img.shape
        
        # ⚠️ 성능 최적화: 고해상도 이미지 축소하여 각도 계산
        resize_factor = Config.DESKEW_RESIZE_FACTOR
        if resize_factor < 1.0:
            resized = cv2.resize(
                img,
                None,
                fx=resize_factor,
                fy=resize_factor,
                interpolation=cv2.INTER_LINEAR
            )
        else:
            resized = img
        
        # 그레이스케일 변환 (필요 시)
        if len(resized.shape) == 3:
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        else:
            gray = resized
        
        # 1. Canny edge detection으로 선 추출
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # 2. Hough Line Transform으로 직선 검출
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        
        if lines is None or len(lines) == 0:
            return img  # 선이 없으면 원본 반환
        
        # 3. 가장 많이 검출된 각도 계산
        angles = []
        for rho, theta in lines[:, 0]:
            angle = (theta - np.pi / 2) * 180 / np.pi
            angles.append(angle)
        
        median_angle = np.median(angles)
        
        # 4. 회전 변환 (각도가 임계값 이상일 때만 적용)
        if abs(median_angle) > Config.DESKEW_ANGLE_THRESHOLD:
            (h, w) = original_shape[:2]
            center = (w // 2, h // 2)
            
            # 회전 행렬 생성 (원본 이미지 크기 기준)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            
            # 원본 이미지에 회전 적용
            rotated = cv2.warpAffine(
                img,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            return rotated
        
        return img  # 기울어짐이 임계값 미만이면 원본 반환
    
    except Exception as e:
        raise PreprocessingError(
            f"Deskewing 실패: {str(e)}",
            step="deskewing"
        )


def enhance_contrast(img: np.ndarray) -> np.ndarray:
    """
    대비 향상
    
    Args:
        img: 그레이스케일 이미지
    
    Returns:
        대비가 향상된 이미지
    """
    try:
        # CLAHE (Contrast Limited Adaptive Histogram Equalization) 적용
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img)
        
        return enhanced
    
    except Exception as e:
        raise PreprocessingError(
            f"대비 향상 실패: {str(e)}",
            step="contrast_enhancement"
        )


def preprocess_pipeline(
    img: np.ndarray,
    apply_deskewing: bool = True,
    apply_binarization: bool = True,
    apply_denoising: bool = True,
    apply_contrast: bool = False
) -> np.ndarray:
    """
    전처리 파이프라인 통합 함수
    
    Args:
        img: 원본 이미지 (BGR 또는 Grayscale)
        apply_deskewing: Deskewing 적용 여부
        apply_binarization: 이진화 적용 여부
        apply_denoising: 노이즈 제거 적용 여부
        apply_contrast: 대비 향상 적용 여부
    
    Returns:
        전처리된 이미지
    
    Example:
        >>> import cv2
        >>> img = cv2.imread("document.png")
        >>> processed = preprocess_pipeline(img)
    """
    result = img.copy()
    
    # 1. Deskewing (기울어짐 보정)
    if apply_deskewing:
        result = deskew_image(result)
    
    # 2. 대비 향상 (선택적, 이진화 전에 적용)
    if apply_contrast:
        if len(result.shape) == 3:
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        else:
            gray = result
        result = enhance_contrast(gray)
    
    # 3. 이진화
    if apply_binarization:
        result = binarize_image(result)
    
    # 4. 노이즈 제거
    if apply_denoising:
        result = denoise_image(result)
    
    return result


def save_debug_image(
    img: np.ndarray,
    filename: str,
    step: str = "unknown"
) -> Optional[str]:
    """
    디버그 모드에서 이미지 저장
    
    Args:
        img: 저장할 이미지
        filename: 파일명
        step: 전처리 단계명
    
    Returns:
        저장된 파일 경로 (저장 성공 시), None (비활성화 시)
    """
    if not Config.SAVE_OCR_DEBUG_IMAGES:
        return None
    
    try:
        Config.ensure_debug_dir()
        
        output_path = Config.DEBUG_OUTPUT_DIR / f"{step}_{filename}"
        cv2.imwrite(str(output_path), img)
        
        return str(output_path)
    
    except Exception:
        # 디버그 이미지 저장 실패는 에러로 처리하지 않음
        return None
