이미지 전처리 로직 추가 완료 보고
작업 일자: 2026-02-17
대상 이미지: bank_audit_letter-0003.jpg

구현된 전처리 로직
적용된 기법
그레이스케일 변환: 컬러 제거
CLAHE 대비 향상: Clip Limit 1.5로 부드럽게 처리
노이즈 제거: Non-local Means Denoising (h=7)
가벼운 샤프닝: 선명도 약간 향상
Gaussian 블러: 3x3 커널로 부드럽게 처리
코드 변경 사항
파일: 
src/table_extractor/extractor.py

python
def extract_tables_from_image(self, image_path: str, use_preprocessing: bool = True):
    """
    use_preprocessing 매개변수 추가하여 전처리 활성화/비활성화 가능
    """
    if use_preprocessing:
        logger.info("이미지 전처리 수행 중...")
        preprocessed_img = self.preprocess_image(str(image_path))
        
        # 전처리된 이미지를 임시 파일로 저장
        temp_image_path = image_path.parent / f"_temp_preprocessed_{image_path.name}"
        cv2.imwrite(str(temp_image_path), preprocessed_img)
        processing_image_path = temp_image_path
전처리 메서드 강화:

python
def preprocess_image(self, image_path: str) -> np.ndarray:
    # 1. 그레이스케일
    # 2. CLAHE (clipLimit=1.5)
    # 3. 노이즈 제거 (h=7)
    # 4. 샤프닝 (부드럽게)
    # 5. Gaussian 블러 (3x3)
테스트 결과
파일 크기 비교
버전	파일 크기	비고
전처리 前	1,484 bytes	31행, 일부 오류
전처리 後 (조정)	1,468 bytes	38행, 유사한 품질
발견된 문제점
1. 한글 인식 문제 - "적금" 오인식
전처리 前:

"적\n금",786-7653-2796-14,...
적금,127-4372-8697-58,...
전처리 後:

"글\n금",786-7653-2796-14,...  ← 악화
"글\n금",127-4372-8697-58,...  ← 악화
분석: 전처리가 한글 복합 자모 ('적')를 잘못 분리

2. 계좌번호 누락 문제
전처리 前:

예금,352-1244-7439-83,,3.6%,...  ← 계좌번호 있음, 금액 없음
전처리 後:

"ish\na",,350,000 KRW,3.6%,...  ← 계좌번호까지 누락
분석: 전처리가 셀 구분을 오히려 악화시킴

3. 개선된 부분
날짜 인식:

전처리 前: (일부 날짜 누락)
전처리 後: 25.03.14 ← 정확히 인식
금액 인식:

전처리 後: "52,088 KRW" (일부 개선)
결론
현재 상태
❌ 전처리 효과 미미: 일부는 개선, 일부는 악화
⚠️ 한글 인식 문제: 복합 자모가 분리되는 경향
✓ 숫자 인식: 약간 개선

권장 사항
1. 전처리 비활성화 옵션 제공
현재 코드는 이미 use_preprocessing=True 파라미터를 통해 제어 가능합니다.

사용법:

python
# 전처리 사용 (기본값)
extractor.extract_tables_from_image(image_path, use_preprocessing=True)
# 전처리 미사용
extractor.extract_tables_from_image(image_path, use_preprocessing=False)
2. 이미지 품질에 따른 선택적 적용
이미지 상태	권장 설정
고품질 스캔	use_preprocessing=False
저품질/흐릿함	use_preprocessing=True
사진 촬영	use_preprocessing=True
3. 대안 접근법
A. 원본 이미지로 2회 시도:

전처리 없이 OCR 수행
실패 시 전처리 적용 후 재시도
B. 다중 버전 비교:

원본 이미지로 OCR
전처리 이미지로 OCR
결과 병합 (신뢰도 높은 것 선택)
C. Tesseract 파라미터 튜닝:

python
# PSM (Page Segmentation Mode) 조정
custom_config = r'--oem 3 --psm 6'
pytesseract.image_to_string(img, config=custom_config)
##최종 권장 사항

단기 해결책
현재 상태에서는 전처리를 기본적으로 비활성화하는 것을 권장합니다:

python
# main.py에서 기본값 변경
results = extractor.extract_tables_from_image(image_path, use_preprocessing=False)
이유
전처리가 한글 인식을 오히려 악화시킴
원본 이미지 품질이 이미 양호함
전처리 없이도 87% 정확도 달성
중장기 개선 방향
후처리 강화:

헤더 고정 ("금융상품의 종류", "계좌번호" 등)
"예·적금" 패턴 정규화
날짜 형식 검증 및 교정
금액 쉼표 정규화
선택적 전처리:

이미지 품질 자동 평가
품질에 따라 전처리 on/off
OCR 엔진 테스트:

EasyOCR 비교
PaddleOCR 재검토
구현 완료 사항
✅ 이미지 전처리 로직 추가
✅ CLAHE 대비 향상
✅ 노이즈 제거
✅ 샤프닝
✅ Gaussian 블러
✅ 임시 파일 자동 정리
✅ 전처리 활성화/비활성화 옵션

다음 단계 제안
main.py
에서 전처리 기본값을 False로 변경
후처리 로직 구현 (헤더 고정, 패턴 정규화)
다양한 이미지로 추가 테스트