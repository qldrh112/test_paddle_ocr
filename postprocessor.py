"""
audit-inquiry-automation1/postprocessor.py

후처리 모듈: 금융 패턴 정규화 [ADR-002]
OCR 결과의 오류를 도메인 지식으로 보정
"""

import re
from typing import List, Tuple

from config import Config


class FinancialPatternNormalizer:
    """
    금융거래조회서 필드 정규화
    
    ⚠️ Technical Lead's Advice 반영:
    - 이자율 복원은 '연이자율(4)' 컨텍스트에서만 적용
    """
    
    # 계좌번호 패턴: XXX-XXXX-XXXX-XX
    ACCOUNT_PATTERN = re.compile(r'(\d{3})[- ]?(\d{4})[- ]?(\d{4})[- ]?(\d{2})')
    
    # 날짜 패턴: YYMMDD
    DATE_PATTERN = re.compile(r'(\d{2})(\d{2})(\d{2})')
    
    # 금액 + 통화: 숫자 뒤 KRW/USD/JPY (오인식 패턴 포함)
    AMOUNT_CURRENCY_PATTERN = re.compile(
        r'(\d[\d,]*)\s*(KRW|USD|JPY|원|KRV|KRM|U5D?)'
    )
    
    # 통화 오타 보정 맵
    CURRENCY_CORRECTIONS = {
        'KRV': 'KRW',
        'KRM': 'KRW',
        'U5': 'USD',
        'U5D': 'USD',
    }
    
    # 이자율 패턴: X.X% 형태 (두 자리 숫자)
    INTEREST_PATTERN = re.compile(r'(\d)(\d+)%')
    
    def normalize_account_number(self, tokens: List[str]) -> str:
        """
        분할된 계좌번호 토큰을 병합
        
        Example:
            ['416-', '1241', '7568-', '9국'] → '416-1241-7568-93'
        """
        # 연속된 토큰을 합쳐서 패턴 매칭 시도
        combined = ''.join(tokens)
        
        # 한글 제거 (오인식 대응)
        combined = re.sub(r'[가-힣]', '', combined)
        
        match = self.ACCOUNT_PATTERN.search(combined)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}-{match.group(4)}"
        
        return combined  # 매칭 실패 시 원본 반환
    
    def normalize_date(self, text: str) -> str:
        """
        날짜 정규화
        
        Example:
            '2412국' → '2024-12-31'
        """
        # 한글 제거
        clean = re.sub(r'[가-힣]', '', text)
        
        match = self.DATE_PATTERN.search(clean)
        if match:
            yy, mm, dd = match.groups()
            # 20XX년으로 변환
            year = f"20{yy}"
            return f"{year}-{mm}-{dd}"
        
        return text
    
    def normalize_interest_rate(
        self,
        text: str,
        is_interest_rate_field: bool = True
    ) -> str:
        """
        이자율 소수점 복원
        
        ⚠️ Technical Lead's Advice:
        - 이자율 필드일 때만 적용 (25% -> 2.5%)
        - 컨텍스트 없이 일괄 적용하면 연체이자율 등 오류 가능
        
        Example:
            normalize_interest_rate('360%', is_interest_rate_field=True) → '3.6%'
            normalize_interest_rate('25%', is_interest_rate_field=True) → '2.5%'
        """
        if not is_interest_rate_field:
            return text
        
        # 두 자리 이상 숫자 + %
        match = self.INTEREST_PATTERN.match(text)
        if match and 2 <= len(match.group(0)) <= 4:
            first_digit = match.group(1)
            rest_digits = match.group(2)
            
            # 360% → 3.6%, 25% → 2.5%, 143% → 14.3%
            return f"{first_digit}.{rest_digits}%"
        
        return text
    
    def merge_amount_currency(
        self,
        tokens: List[Tuple[float, float, str, float]],
        page_height: float = 3000.0
    ) -> List[Tuple[float, float, str, float]]:
        """
        금액과 통화 단위 병합
        
        ⚠️ 아키텍처 보완: 좌표를 0~1000으로 정규화하여 해상도 독립적 거리 측정
        
        Example:
            [(y, x1, '602418268', 0.99), (y+5, x2, 'KRW', 0.99)]
            → [(y, x1, '602,418,268 KRW', 0.99)]
        """
        merged = []
        i = 0
        
        # 좌표 정규화 비율 계산
        norm_factor = Config.NORMALIZED_PAGE_HEIGHT / page_height
        
        while i < len(tokens):
            y, x, text, conf = tokens[i]
            y_norm = y * norm_factor
            
            # 다음 토큰이 통화 단위인지 확인
            if i + 1 < len(tokens):
                next_y, next_x, next_text, next_conf = tokens[i + 1]
                next_y_norm = next_y * norm_factor
                
                # 통화 오타 보정
                corrected_currency = self.CURRENCY_CORRECTIONS.get(
                    next_text,
                    next_text
                )
                
                # 정규화된 거리로 같은 행 판단
                if (corrected_currency in ['KRW', 'USD', 'JPY'] and
                    abs(next_y_norm - y_norm) < Config.CURRENCY_MERGE_THRESHOLD):
                    try:
                        # 금액에 천 단위 콤마 추가
                        amount_str = text.replace(',', '')
                        formatted = f"{int(amount_str):,} {corrected_currency}"
                        
                        # 두 토큰의 평균 신뢰도 사용
                        avg_conf = (conf + next_conf) / 2
                        merged.append((y, x, formatted, avg_conf))
                        i += 2
                        continue
                    except ValueError:
                        pass  # 숫자 변환 실패 시 개별 토큰 유지
            
            merged.append((y, x, text, conf))
            i += 1
        
        return merged


def filter_low_confidence(
    results: List[Tuple[float, float, str, float]],
    threshold: float = None
) -> List[Tuple[float, float, str, bool]]:
    """
    [ADR-002] 신뢰도 낮은 토큰에 PENDING_REVIEW 플래그 추가
    
    Args:
        results: [(y, x, text, confidence), ...]
        threshold: 신뢰도 임계값 (None이면 config.py 설정 사용)
    
    Returns:
        [(y, x, text, needs_review), ...]
    """
    # config.py에서 임계값 로드
    if threshold is None:
        threshold = Config.OCR_CONFIDENCE_THRESHOLD
    
    filtered = []
    for y, x, text, conf in results:
        needs_review = conf < threshold
        filtered.append((y, x, text, needs_review))
    
    return filtered
