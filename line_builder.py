"""
audit-inquiry-automation1/line_builder.py

좌표 기반 토큰 그룹화 및 행 재구성 [Func-121]
정규화된 좌표를 사용하여 해상도 독립적인 행 판단
"""

from typing import List, Tuple

from config import Config


class LineBuilder:
    """
    Y좌표 기반으로 토큰을 논리적 행으로 그룹화
    
    ⚠️ 아키텍처 개선: 정규화된 좌표 사용으로 해상도 독립성 확보
    """
    
    def __init__(
        self,
        row_threshold: float = None,
        page_height: float = 3000.0
    ):
        """
        Args:
            row_threshold: 같은 행으로 간주할 Y 좌표 차이 (정규화된 좌표 기준)
            page_height: 페이지 높이 (좌표 정규화용)
        """
        self.row_threshold = row_threshold or Config.LINE_Y_THRESHOLD
        self.page_height = page_height
        self.norm_factor = Config.NORMALIZED_PAGE_HEIGHT / page_height
    
    def build_lines(
        self,
        tokens: List[Tuple[float, float, str, float]]
    ) -> List[List[Tuple[float, float, str, float]]]:
        """
        Y좌표 오차 기반으로 토큰을 논리적 행으로 묶기
        
        Args:
            tokens: [(y, x, text, confidence), ...]
        
        Returns:
            [[(y, x, text, confidence), ...], ...]  # 행별 토큰 리스트
        
        Example:
            Input:
                [(100, 50, '예금', 0.99),
                 (105, 200, '1000000', 0.98),
                 (200, 50, '적금', 0.99)]
            
            Output:
                [
                    [(100, 50, '예금', 0.99), (105, 200, '1000000', 0.98)],
                    [(200, 50, '적금', 0.99)]
                ]
        """
        if not tokens:
            return []
        
        # Y좌표 기준으로 전체 정렬
        tokens.sort(key=lambda t: t[0])
        
        grouped_lines = []
        current_row = [tokens[0]]
        
        for token in tokens[1:]:
            y, x, text, conf = token
            
            # 현재 행의 평균 Y좌표 계산 (안정성 강화)
            avg_y = sum(t[0] for t in current_row) / len(current_row)
            
            # 좌표 정규화 (해상도 독립적 거리 측정)
            y_norm = y * self.norm_factor
            avg_y_norm = avg_y * self.norm_factor
            
            # 정규화된 거리로 같은 행 판단
            if abs(y_norm - avg_y_norm) <= self.row_threshold:
                current_row.append(token)
            else:
                # 새로운 행 시작: 기존 행은 X좌표(좌→우)로 정렬하여 저장
                grouped_lines.append(sorted(current_row, key=lambda t: t[1]))
                current_row = [token]
        
        # 마지막 행 처리
        if current_row:
            grouped_lines.append(sorted(current_row, key=lambda t: t[1]))
        
        return grouped_lines
