"""
표 추출 모듈 - img2table을 사용한 이미지에서 표 감지 및 데이터 추출

이 모듈은 다음 기능을 제공합니다:
1. 이미지에서 표 감지 (img2table 사용)
2. Tesseract OCR을 사용한 셀 텍스트 추출
3. 표 구조 분석 및 데이터 구조화
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from img2table.document import Image
from img2table.ocr import TesseractOCR
import pandas as pd
import cv2
import numpy as np
from PIL import Image as PILImage

from .header_fixer import fix_table_header, identify_table_type, get_table_type_name

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TableExtractor:
    """
    이미지에서 표를 추출하는 클래스
    """
    
    def __init__(self, lang: str = 'kor+eng'):
        """
        초기화
        
        Args:
            lang: Tesseract OCR 언어 설정 (기본값: 'kor+eng' - 한국어와 영어)
        """
        self.lang = lang
        try:
            self.ocr = TesseractOCR(lang=lang)
            logger.info(f"Tesseract OCR 초기화 완료 (언어: {lang})")
        except Exception as e:
            logger.error(f"Tesseract OCR 초기화 실패: {e}")
            logger.warning("OCR 없이 표 구조만 추출합니다.")
            self.ocr = None
    
    def extract_tables_from_image(self, image_path: str, use_preprocessing: bool = True) -> List[Dict[str, Any]]:
        """
        이미지에서 표를 추출
        
        Args:
            image_path: 이미지 파일 경로
            use_preprocessing: 이미지 전처리 사용 여부 (기본값: True)
            
        Returns:
            추출된 표 리스트. 각 표는 다음 정보를 포함:
            - dataframe: pandas DataFrame 형식의 표 데이터
            - bbox: 표의 바운딩 박스 (x1, y1, x2, y2)
            - title: 표의 제목 (있는 경우)
        """
        image_path = Path(image_path)
        if not image_path.exists():
            logger.error(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            return []
        
        logger.info(f"이미지 처리 시작: {image_path}")
        
        # 전처리 사용 여부에 따라 이미지 경로 결정
        processing_image_path = image_path
        temp_image_path = None
        
        if use_preprocessing:
            logger.info("이미지 전처리 수행 중...")
            preprocessed_img = self.preprocess_image(str(image_path))
            
            # 전처리된 이미지를 임시 파일로 저장
            temp_image_path = image_path.parent / f"_temp_preprocessed_{image_path.name}"
            cv2.imwrite(str(temp_image_path), preprocessed_img)
            processing_image_path = temp_image_path
            logger.info(f"전처리 완료: {temp_image_path}")
        
        try:
            # img2table을 사용하여 표 추출
            doc = Image(str(processing_image_path))
            
            # OCR을 사용하여 표 추출
            if self.ocr:
                extracted_tables = doc.extract_tables(
                    ocr=self.ocr,
                    implicit_rows=True,  # 암시적 행 감지
                    implicit_columns=True,  # 암시적 열 감지
                    borderless_tables=True,  # 테두리 없는 표도 감지
                    min_confidence=50  # 최소 신뢰도
                )
            else:
                # OCR 없이 표 구조만 추출
                extracted_tables = doc.extract_tables(
                    implicit_rows=True,
                    implicit_columns=True,
                    borderless_tables=True
                )
            
            if not extracted_tables:
                logger.info(f"이미지에서 표를 찾지 못했습니다: {image_path}")
                return []
            
            logger.info(f"{len(extracted_tables)}개의 표를 찾았습니다.")
            
            # 결과 구조화
            results = []
            for idx, table in enumerate(extracted_tables):
                try:
                    # img2table의 결과를 DataFrame으로 변환
                    df = table.df
                    
                    if df is not None and not df.empty:
                        # 표 유형 식별 및 헤더 고정
                        table_type = identify_table_type(df)
                        if table_type:
                            df_fixed = fix_table_header(df, table_type)
                            table_type_name = get_table_type_name(table_type)
                            logger.info(f"표 {idx + 1} 유형 식별: {table_type_name}")
                        else:
                            df_fixed = df
                            logger.info(f"표 {idx + 1} 유형 식별 실패 - 원본 헤더 사용")
                        
                        result = {
                            'table_index': idx,
                            'dataframe': df_fixed,
                            'bbox': table.bbox if hasattr(table, 'bbox') else None,
                            'title': table.title if hasattr(table, 'title') else None,
                            'table_type': table_type
                        }
                        results.append(result)
                        logger.info(f"표 {idx + 1}: {df_fixed.shape[0]}행 x {df_fixed.shape[1]}열")
                    else:
                        logger.warning(f"표 {idx + 1}: 데이터가 비어있습니다.")
                        
                except Exception as e:
                    logger.error(f"표 {idx + 1} 처리 중 오류 발생: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"표 추출 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
        finally:
            # 임시 전처리 이미지 삭제
            if temp_image_path and temp_image_path.exists():
                try:
                    temp_image_path.unlink()
                    logger.debug(f"임시 파일 삭제: {temp_image_path}")
                except Exception as e:
                    logger.warning(f"임시 파일 삭제 실패: {e}")
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        이미지 전처리 - OCR 정확도 향상을 위한 다단계 처리
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            전처리된 이미지 (numpy 배열)
        """
        # OpenCV로 이미지 로드
        img = cv2.imread(str(image_path))
        
        if img is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")
        
        logger.debug(f"원본 이미지 크기: {img.shape}")
        
        # 1. 그레이스케일 변환
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. 대비 향상 (CLAHE - Contrast Limited Adaptive Histogram Equalization)
        # clipLimit을 낮춰서 부드럽게 처리
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        logger.debug("CLAHE 대비 향상 완료")
        
        # 3. 노이즈 제거 (매우 약하게)
        # h 값을 낮춰서 과도한 블러를 방지
        denoised = cv2.fastNlMeansDenoising(enhanced, h=7)
        logger.debug("노이즈 제거 완료")
        
        # 4. 가벼운 샤프닝 (선명도 약간 향상)
        # 강도를 낮춰서 자연스럽게
        kernel_sharpening = np.array([[-0.5, -0.5, -0.5],
                                      [-0.5,   5, -0.5],
                                      [-0.5, -0.5, -0.5]])
        sharpened = cv2.filter2D(denoised, -1, kernel_sharpening)
        logger.debug("샤프닝 완료")
        
        # 5. 약간의 블러를 추가하여 OCR 성능 향상
        # Tesseract는 약간 부드러운 이미지를 더 잘 인식
        final = cv2.GaussianBlur(sharpened, (3, 3), 0)
        logger.debug("최종 블러 처리 완료")
        
        return final
    
    def save_table_to_csv(self, df: pd.DataFrame, output_path: str):
        """
        DataFrame을 CSV 파일로 저장
        
        Args:
            df: pandas DataFrame
            output_path: 출력 파일 경로
        """
        try:
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"CSV 파일 저장 완료: {output_path}")
        except Exception as e:
            logger.error(f"CSV 저장 중 오류 발생: {e}")
    
    def save_table_to_excel(self, df: pd.DataFrame, output_path: str):
        """
        DataFrame을 Excel 파일로 저장
        
        Args:
            df: pandas DataFrame
            output_path: 출력 파일 경로
        """
        try:
            df.to_excel(output_path, index=False, engine='openpyxl')
            logger.info(f"Excel 파일 저장 완료: {output_path}")
        except Exception as e:
            logger.error(f"Excel 저장 중 오류 발생: {e}")
    
    def save_table_to_json(self, df: pd.DataFrame, output_path: str):
        """
        DataFrame을 JSON 파일로 저장
        
        Args:
            df: pandas DataFrame
            output_path: 출력 파일 경로
        """
        try:
            df.to_json(output_path, orient='records', force_ascii=False, indent=2)
            logger.info(f"JSON 파일 저장 완료: {output_path}")
        except Exception as e:
            logger.error(f"JSON 저장 중 오류 발생: {e}")
