"""
audit-inquiry-automation1/chunker.py

표 영역 분할 로직 [ADR-005]
앵커 패턴 기반으로 섹션을 분할하고 데이터 추출
"""

from typing import Dict, List, Tuple

from table_schema import BANK_INQUIRY_SCHEMAS, FOOTER_KEYWORDS


class Chunker:
    """
    앵커 패턴을 탐지하여 섹션별 데이터(Chunk)를 추출
    
    각 표의 시작과 끝을 인식하여 데이터를 분할
    """
    
    def __init__(self):
        self.footer_keywords = [kw.replace(" ", "") for kw in FOOTER_KEYWORDS]
    
    def split_into_chunks(
        self,
        rows: List[List[Tuple[float, float, str, float]]]
    ) -> Dict[str, List[List[Tuple[float, float, str, float]]]]:
        """
        행 토큰 목록을 순회하며 앵커를 탐지하고 섹션별 데이터 추출
        
        Args:
            rows: 행별 토큰 리스트
                [
                    [(y, x, text, conf), ...],  # 첫 번째 행
                    [(y, x, text, conf), ...],  # 두 번째 행
                ]
        
        Returns:
            표 이름별 데이터
                {
                    "금융상품_내역": [
                        [(y, x, '예금', conf), ...],  # 첫 번째 데이터 행
                        [(y, x, '적금', conf), ...],  # 두 번째 데이터 행
                    ]
                }
        """
        all_chunks = {}
        current_schema = None
        current_chunk_buffer = []
        
        for row in rows:
            # 1. 행 텍스트 결합 (공백 제거하여 패턴 매칭)
            row_text = "".join([t[2] for t in row]).replace(" ", "")
            
            # 2. 새로운 앵커(표 시작) 탐지
            found_new_schema = None
            for schema in BANK_INQUIRY_SCHEMAS:
                if schema.matches_anchor(row_text):
                    found_new_schema = schema
                    break
            
            # 3. 섹션 전환 로직
            if found_new_schema:
                # 이전까지 쌓인 청크가 있다면 저장
                if current_schema and current_chunk_buffer:
                    self._add_to_dict(
                        all_chunks,
                        current_schema.table_name,
                        current_chunk_buffer
                    )
                
                current_schema = found_new_schema
                current_chunk_buffer = []  # 앵커 행은 헤더로 사용, 데이터에서 제외
                print(f"⚓ 표 시작 감지: {current_schema.table_name}")
                continue
            
            # 4. Footer 키워드 탐지 시 섹션 종료
            if any(kw in row_text for kw in self.footer_keywords):
                if current_schema and current_chunk_buffer:
                    self._add_to_dict(
                        all_chunks,
                        current_schema.table_name,
                        current_chunk_buffer
                    )
                current_schema = None
                current_chunk_buffer = []
                continue
            
            # 5. 데이터 수집
            if current_schema:
                # 빈 행 필터링 (텍스트가 거의 없는 행)
                if len([t for t in row if t[2].strip()]) > 0:
                    current_chunk_buffer.append(row)
        
        # 루프 종료 후 남은 데이터 처리
        if current_schema and current_chunk_buffer:
            self._add_to_dict(
                all_chunks,
                current_schema.table_name,
                current_chunk_buffer
            )
        
        return all_chunks
    
    def _add_to_dict(
        self,
        store: Dict,
        key: str,
        data: List
    ):
        """딕셔너리에 데이터 추가"""
        if key not in store:
            store[key] = []
        store[key].extend(data)
