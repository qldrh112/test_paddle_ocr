"""
audit-inquiry-automation1/excel_writer.py

엑셀 출력 모듈
추출된 표 데이터를 엑셀 파일로 저장
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple

from config import Config


def write_tables_to_excel(
    data_by_table: Dict[str, List[List[Tuple[float, float, str, bool]]]],
    output_path: str,
    headers_by_table: Dict[str, List[str]] = None
) -> int:
    """
    추출된 표 데이터를 엑셀 파일로 저장
    
    Args:
        data_by_table: 표 이름별 데이터
            {
                "금융상품_내역": [
                    [(y, x, '예금', False), (y, x, '123-456', False), ...],  # 첫 행
                    [(y, x, '적금', True), ...],  # 두 번째 행 (신뢰도 낮음)
                ]
            }
        output_path: 출력 파일 경로
        headers_by_table: 표별 헤더 정의 (선택사항)
    
    Returns:
        생성된 시트 수
    """
    if not data_by_table:
        print("⚠️  추출된 데이터가 없습니다.")
        return 0
    
    # 엑셀 파일 작성 준비
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        sheet_count = 0
        
        for table_name, rows_data in data_by_table.items():
            if not rows_data:
                continue
            
            # 시트명 정규화 (엑셀 제약 조건)
            sheet_name = _normalize_sheet_name(table_name, sheet_count + 1)
            
            # 데이터프레임 생성
            df_rows = []
            for row_tokens in rows_data:
                # 각 행의 텍스트만 추출
                row_values = [token[2] for token in row_tokens]
                df_rows.append(row_values)
            
            # 헤더 가져오기
            headers = None
            if headers_by_table and table_name in headers_by_table:
                headers = headers_by_table[table_name]
            
            # DataFrame 생성 (⭐ 헤더/데이터 불일치 시 유연하게 처리)
            if headers:
                # 최대 열 수 계산
                max_cols = max(len(row) for row in df_rows) if df_rows else 0
                
                # 헤더가 데이터보다 많으면 잘라내기
                if len(headers) > max_cols:
                    headers = headers[:max_cols]
                
                # 헤더가 데이터보다 적으면 자동 컬럼명 추가
                while len(headers) < max_cols:
                    headers.append(f"Column_{len(headers) + 1}")
                
                df = pd.DataFrame(df_rows, columns=headers)
            else:
                df = pd.DataFrame(df_rows)
            
            # 엑셀에 쓰기
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            sheet_count += 1
            print(f"✅ 시트 '{sheet_name}' 생성 완료 ({len(df_rows)}행)")
    
    print(f"\n📁 엑셀 파일 생성 완료: {output_path}")
    return sheet_count


def _normalize_sheet_name(table_name: str, counter: int) -> str:
    """
    엑셀 시트명 정규화
    
    - 31자 제한
    - 특수문자 제거
    - 빈 이름은 자동 부여
    """
    import re
    
    if not table_name or table_name == "미분류_표":
        return f"Table_{counter}"
    
    # 특수문자 제거
    safe_name = re.sub(r'[\\/*?:\[\]]', '_', table_name)
    
    # 길이 제한
    return safe_name[:31]
