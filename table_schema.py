"""
audit-inquiry-automation1/table_schema.py

금융거래조회서 표 스키마 정의
간단한 앵커 패턴 기반 표 인식
"""

import re
from typing import List, Tuple


class TableSchema:
    """
    기본 표 스키마 클래스
    
    표의 시작을 인식하는 앵커 패턴 정의
    """
    
    def __init__(
        self,
        table_name: str,
        anchor_pattern: str,
        headers: List[str] = None
    ):
        """
        Args:
            table_name: 표 이름 (예: "금융상품_내역")
            anchor_pattern: 앵커 패턴 (정규식)
            headers: 표 헤더 (선택사항)
        """
        self.table_name = table_name
        self.anchor_pattern = re.compile(anchor_pattern) if anchor_pattern else None
        self.headers = headers or []
    
    def matches_anchor(self, text: str) -> bool:
        """
        텍스트가 이 표의 앵커 패턴과 일치하는지 확인
        
        정규식 매칭 실패 시 퍼지 매칭(Levenshtein Distance) 시도
        
        Args:
            text: 행 텍스트 (공백 제거된 깨끗한 텍스트)
        
        Returns:
            일치 여부
        """
        if not self.anchor_pattern:
            return False
        
        # 1. 정규식 매칭 시도
        if self.anchor_pattern.search(text):
            return True
        
        # 2. 퍼지 매칭 시도 (Req-112: 조회처 자동 분류)
        from config import Config
        
        if Config.ENABLE_FUZZY_ANCHOR_MATCHING:
            return self._fuzzy_match_anchor(text)
        
        return False
    
    def _fuzzy_match_anchor(self, text: str) -> bool:
        """
        퍼지 매칭으로 앵커 패턴 감지
        
        OCR 오인식에 강건한 매칭 (예: '귤읍기래' ≈ '금융거래')
        """
        from rapidfuzz import fuzz
        from config import Config
        
        # 앵커 키워드 정의 (표별로 커스터마이징)
        if self.table_name == "금융상품_내역":
            keywords = ["종류", "계좌번호", "금액"]  # 필수 키워드만 사용 (3개)
        elif self.table_name == "담보_제공_내역":
            keywords = ["담보", "제공", "내역"]
        elif self.table_name == "채무_보증_내역":
            keywords = ["채무", "보증", "내역"]
        else:
            return False
        
        # 텍스트에서 각 키워드와 유사도 계산
        matched_count = 0
        matched_keywords = []
        
        for keyword in keywords:
            # 부분 문자열 유사도 계산
            similarity = fuzz.partial_ratio(keyword, text) / 100.0
            
            if similarity >= Config.FUZZY_MATCH_THRESHOLD:
                matched_count += 1
                matched_keywords.append(f"{keyword}({similarity:.2f})")
        
        # 디버그: 매칭 정보 출력
        if Config.DEBUG_MODE and matched_count > 0:
            print(f"[Fuzzy Match] '{text[:50]}' → {self.table_name}: {matched_count}/{len(keywords)} 매칭: {', '.join(matched_keywords)}")
        
        # ⭐ 순수 OCR 접근: 최소 1개만 매칭되어도 인정 (데이터 손실 방지)
        return matched_count >= 1


# 금융거래조회서 표 스키마 정의
# ⭐ 다중 표 지원: 3개 표 스키마로 확장
BANK_INQUIRY_SCHEMAS = [
    TableSchema(
        table_name="금융상품_내역",
        anchor_pattern=r"금융상품|종류|계좌번호|금액",  # | 구분자로 키워드 나열
        headers=[
            "금융상품의 종류",
            "계좌번호",
            "금액",
            "연이자율",
            "최종이자 지급일",
            "만기일",
            "인출제한 등"
        ]
    ),
    TableSchema(
        table_name="담보_제공_내역",
        anchor_pattern=r"담보|제공|종류|담보물|내역",
        headers=[
            "담보종류",
            "담보물내역",
            "담보가액",
            "비고"
        ]
    ),
    TableSchema(
        table_name="채무_보증_내역",
        anchor_pattern=r"채무|보증|내역|금액",
        headers=[
            "보증종류",
            "보증금액",
            "피보증인",
            "보증기간",
            "비고"
        ]
    ),
]


# Footer 키워드 (데이터 종료 지점)
FOOTER_KEYWORDS = ["작성요령", "안내사항", "참고사항", "확인합니다"]
