"""
audit-inquiry-automation1/exceptions.py

시스템 예외 클래스 정의
상태 코드 기반 예외 처리 [Lifecycles.csv 매핑]
"""


class OcrExtractionError(Exception):
    """
    OCR 추출 과정에서 발생하는 예외
    
    Attributes:
        message: 에러 메시지
        state: 시스템 상태 코드 (예: FAILED_OCR_ERROR)
        original_exception: 원본 예외 객체
    """
    
    def __init__(
        self,
        message: str,
        state: str = "FAILED_OCR_ERROR",
        original_exception: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.state = state
        self.original_exception = original_exception
    
    def __str__(self):
        if self.original_exception:
            return f"[{self.state}] {self.message} (Caused by: {self.original_exception})"
        return f"[{self.state}] {self.message}"


class PreprocessingError(Exception):
    """이미지 전처리 과정에서 발생하는 예외"""
    
    def __init__(self, message: str, step: str = None):
        super().__init__(message)
        self.message = message
        self.step = step  # 실패한 전처리 단계 (예: 'deskewing', 'binarization')
    
    def __str__(self):
        if self.step:
            return f"[PreprocessingError:{self.step}] {self.message}"
        return f"[PreprocessingError] {self.message}"


class ValidationError(Exception):
    """데이터 검증 실패 예외"""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.message = message
        self.field = field  # 검증 실패한 필드명
    
    def __str__(self):
        if self.field:
            return f"[ValidationError:{self.field}] {self.message}"
        return f"[ValidationError] {self.message}"
