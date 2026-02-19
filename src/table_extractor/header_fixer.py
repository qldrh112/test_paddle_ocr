"""
표 헤더 정의 및 매칭 모듈

금융거래조회서의 9가지 표 유형에 대한 고정 헤더를 정의하고,
OCR 결과와 매칭하여 올바른 헤더로 교체합니다.
"""

from typing import List, Optional
import pandas as pd
from difflib import SequenceMatcher

# 9가지 표 유형의 고정 헤더
TABLE_HEADERS = {
    "table1": ["금융상품의 종류", "계좌번호", "금액", "연이자율", "최종이자지급일", "만기일", "인출제한 등"],
    
    "table2": ["대출 종류", "금액", "", "대출일", "최종만기일", "이자", "", "상환방법", "담보 보증 및 관련 약정"],
    
    "table2_sub": ["", "약정한도액", "대출금액", "", "", "연이자율", "최종이자지급일", "", ""],
    
    "table3": ["내용", "한도액", "실행금액", "지급보증수수료율", "기간", "담보 지급보증"],
    
    "table4": ["계약의 종류", "계약일", "한도액", "당행의 매입금액", "당행의 매도금액", "계약실행일 / 만기일", "약정환율 / 이자율 / 주가지수 등", "평가금액", "비고(결제조건 등)"],
    
    "table5": ["내용", "연대보증 등을 제공받은 회사(개인)", "연대 보증 등의 대상 여신", "연대보증 등의 한도", "담보 제공한 자산"],
    
    "table6": ["교부일자(전자어음)", "매수(전자어음)", "교부일자(수표어음)", "매수(수표어음)", "일련번호(수표어음)"],
    
    "table7": ["만기일자(미결제 전자어음)", "금액(미결제 전자어음)", "일련변호(미결제전자어음)", "교부일자(수표어음)", "매수(수표어음)", "일련번호(수표어음)"],
    
    "table8": ["구분(어음 또는 수표)", "번호", "금액", "발행일자", "만기일자", "담보 견질의 목적"],
    
    "table9": ["구분", "담보 보증의 내용", "소유자(제공자)", "감정금액", "설정금액", "설정순위", "선순위 설정 금액"],
}

# 표 유형별 키워드 (표 식별용)
TABLE_KEYWORDS = {
    "table1": ["금융상품", "계좌번호", "연이자율"],
    "table2": ["대출", "약정한도액", "상환방법"],
    "table3": ["한도액", "실행금액", "지급보증수수료율"],
    "table4": ["계약의 종류", "매입금액", "매도금액"],
    "table5": ["연대보증", "대상 여신"],
    "table6": ["전자어음", "수표어음", "교부일자"],
    "table7": ["미결제", "일련변호"],
    "table8": ["어음 또는 수표", "견질"],
    "table9": ["담보 보증", "감정금액", "설정순위"],
}


def calculate_header_similarity(ocr_header: List[str], fixed_header: List[str]) -> float:
    """
    OCR로 읽은 헤더와 고정 헤더의 유사도 계산
    
    Args:
        ocr_header: OCR 결과 헤더
        fixed_header: 고정 헤더
        
    Returns:
        유사도 (0-100%)
    """
    if len(ocr_header) != len(fixed_header):
        # 열 개수가 다르면 패널티
        length_penalty = abs(len(ocr_header) - len(fixed_header)) * 10
        base_similarity = 50  # 기본 유사도
        return max(0, base_similarity - length_penalty)
    
    total_similarity = 0
    for ocr_col, fixed_col in zip(ocr_header, fixed_header):
        # 빈 문자열 처리
        if not ocr_col and not fixed_col:
            total_similarity += 100
            continue
        if not ocr_col or not fixed_col:
            continue
            
        # 문자열 유사도 계산
        similarity = SequenceMatcher(None, str(ocr_col), str(fixed_col)).ratio() * 100
        total_similarity += similarity
    
    return total_similarity / len(fixed_header) if fixed_header else 0


def identify_table_type(df: pd.DataFrame) -> Optional[str]:
    """
    DataFrame의 헤더를 분석하여 표 유형 식별
    
    Args:
        df: pandas DataFrame
        
    Returns:
        표 유형 (table1 ~ table9) 또는 None
    """
    if df.empty or len(df.columns) == 0:
        return None
    
    # 첫 행을 헤더로 가정
    ocr_header = [str(col) for col in df.columns]
    
    # 각 표 유형과의 유사도 계산
    best_match = None
    best_score = 0
    
    for table_type, fixed_header in TABLE_HEADERS.items():
        # 서브 헤더는 건너뛰기
        if table_type == "table2_sub":
            continue
            
        similarity = calculate_header_similarity(ocr_header, fixed_header)
        
        # 키워드 매칭으로 추가 점수
        keyword_bonus = 0
        if table_type in TABLE_KEYWORDS:
            for keyword in TABLE_KEYWORDS[table_type]:
                for col in ocr_header:
                    if keyword in str(col):
                        keyword_bonus += 10
        
        total_score = similarity + keyword_bonus
        
        if total_score > best_score:
            best_score = total_score
            best_match = table_type
    
    # 최소 신뢰도 30% 이상일 때만 반환
    if best_score >= 30:
        return best_match
    
    return None


def fix_table_header(df: pd.DataFrame, table_type: Optional[str] = None) -> pd.DataFrame:
    """
    DataFrame의 헤더를 고정값으로 교체
    
    Args:
        df: pandas DataFrame
        table_type: 표 유형 (None이면 자동 식별)
        
    Returns:
        헤더가 수정된 DataFrame
    """
    if df.empty:
        return df
    
    # 표 유형 식별
    if table_type is None:
        table_type = identify_table_type(df)
    
    if table_type is None or table_type not in TABLE_HEADERS:
        # 식별 실패 시 원본 반환
        return df
    
    # 고정 헤더 가져오기
    fixed_header = TABLE_HEADERS[table_type]
    
    # 열 개수가 일치하는 경우에만 교체
    if len(df.columns) == len(fixed_header):
        df.columns = fixed_header
        return df
    
    # 열 개수가 다른 경우: 가능한 만큼만 교체
    if len(df.columns) < len(fixed_header):
        # DataFrame 열이 더 적음
        df.columns = fixed_header[:len(df.columns)]
    else:
        # DataFrame 열이 더 많음
        new_columns = fixed_header + [f"추가열{i+1}" for i in range(len(df.columns) - len(fixed_header))]
        df.columns = new_columns
    
    return df


def get_table_type_name(table_type: str) -> str:
    """표 유형 코드를 한글 이름으로 변환"""
    names = {
        "table1": "금융상품 명세표",
        "table2": "대출 명세표",
        "table3": "지급보증 명세표",
        "table4": "파생상품계약 명세표",
        "table5": "연대보증 명세표",
        "table6": "전자어음/수표 교부 명세표",
        "table7": "미결제 어음 명세표",
        "table8": "담보 어음/수표 명세표",
        "table9": "담보 설정 명세표",
    }
    return names.get(table_type, "알 수 없는 표")
