"""
통합 엑셀 생성 모듈
여러 이미지의 표 데이터를 하나의 엑셀 파일에 시트별로 저장
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple

def write_all_tables_to_single_excel(
    all_data: Dict[str, Dict[str, List[List[Tuple[float, float, str, bool]]]]],
    output_path: str
) -> int:
    """
    여러 이미지의 표 데이터를 하나의 엑셀 파일에 저장
    
    Args:
        all_data: 전체 데이터
            {
                "bank_audit_letter-0001.jpg": {
                    "금융상품_내역": [행1, 행2, ...]
                },
                "bank_audit_letter-0003.jpg": {
                    "금융상품_내역": [행1, 행2, ...]
                }
            }
        output_path: 출력 파일 경로
    
    Returns:
        생성된 시트 수
    """
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        sheet_count = 0
        
        for image_name, tables in all_data.items():
            # 이미지 이름에서 확장자 제거
            image_base = Path(image_name).stem
            
            for table_name, rows_data in tables.items():
                if not rows_data:
                    continue
                
                # 시트명: "이미지이름_표이름" 형식
                sheet_name = f"{image_base}_{table_name}"
                sheet_name = _normalize_sheet_name(sheet_name, sheet_count + 1)
                
                # 데이터프레임 생성
                df_rows = []
                for row_tokens in rows_data:
                    # 각 행의 텍스트만 추출
                    row_values = [token[2] for token in row_tokens]
                    df_rows.append(row_values)
                
                # DataFrame 생성 (헤더 없이)
                df = pd.DataFrame(df_rows)
                
                # 엑셀에 쓰기
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                
                sheet_count += 1
    
    return sheet_count


def _normalize_sheet_name(name: str, counter: int) -> str:
    """
    엑셀 시트명 정규화
    
    - 31자 제한
    - 특수문자 제거
    - 빈 이름은 자동 부여
    """
    import re
    
    if not name:
        return f"Sheet_{counter}"
    
    # 특수문자 제거 ('_'는 유지)
    safe_name = re.sub(r'[\\/*?:\[\]]', '_', name)
    
    # 길이 제한 (31자)
    if len(safe_name) > 31:
        # 앞부분 유지 (이미지 번호 포함)
        safe_name = safe_name[:31]
    
    return safe_name
