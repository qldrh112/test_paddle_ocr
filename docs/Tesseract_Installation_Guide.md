Tesseract OCR 설치 가이드
개요
표 인식 시스템에서 이미지의 텍스트를 추출하기 위해서는 Tesseract OCR이 필수적으로 설치되어 있어야 합니다.

IMPORTANT

Tesseract OCR은 Google에서 개발한 오픈소스 OCR 엔진으로, 로컬 환경에서 무료로 사용할 수 있습니다.

Windows 설치 방법
1. Tesseract OCR 다운로드
공식 Windows 인스톨러를 다운로드합니다:

다운로드 링크: UB-Mannheim Tesseract

추천 버전:

tesseract-ocr-w64-setup-5.3.3.20231005.exe (64비트 Windows)
tesseract-ocr-w32-setup-5.3.3.20231005.exe (32비트 Windows)
2. 설치 실행
다운로드한 .exe 파일을 실행합니다
설치 중 "Additional language data (download)" 옵션에서 다음 언어를 선택합니다:
✅ Korean (한국어)
✅ English (영어)
기본 설치 경로 사용 (권장):
C:\Program Files\Tesseract-OCR
설치 완료
3. 환경 변수 설정 (중요!)
Tesseract를 어디서든 사용할 수 있도록 PATH 환경 변수에 추가합니다:

시스템 속성 열기:

Windows 검색에서 "환경 변수" 검색
또는 Win + R → sysdm.cpl 입력 → 고급 탭
환경 변수 버튼 클릭

시스템 변수에서 Path 선택 후 편집

새로 만들기를 클릭하고 Tesseract 설치 경로 추가:

C:\Program Files\Tesseract-OCR
확인을 클릭하여 모든 창 닫기

4. 설치 확인
새 PowerShell 또는 명령 프롬프트를 열고 다음 명령어를 실행합니다:

powershell
tesseract --version
예상 출력:

tesseract v5.3.3.20231005
 leptonica-1.83.1
  libgif 5.2.1 : libjpeg 8d (libjpeg-turbo 2.1.5.1) : libpng 1.6.40 : libtiff 4.5.1 : zlib 1.2.13 : libwebp 1.3.2 : libopenjp2 2.5.0
 Found AVX2
 Found AVX
 Found FMA
 Found SSE4.1
 Found libarchive 3.6.2 zlib/1.2.13 liblzma/5.4.1 bz2/1.0.8 liblz4/1.9.4 libzstd/1.5.4
 Found libcurl/8.0.1 Schannel zlib/1.2.13 zstd/1.5.4 libidn2/2.3.4 libpsl/0.21.2 (+libidn2/2.3.3) libssh2/1.10.0
5. 한국어 언어 팩 확인
한국어 데이터가 설치되어 있는지 확인:

powershell
tesseract --list-langs
예상 출력 (kor이 포함되어야 함):

List of available languages in "C:\Program Files\Tesseract-OCR\tessdata" (5):
eng
kor
osd
snum
설치 후 테스트
Tesseract 설치가 완료되면 표 인식 시스템을 테스트합니다:

단일 이미지 테스트
powershell
.venv\Scripts\python.exe src/main.py --input test/image/bank_audit_letter-0003.jpg --output output
또는 Poetry가 정상 작동하는 경우:

powershell
poetry run python src/main.py --input test/image/bank_audit_letter-0003.jpg --output output
전체 디렉토리 테스트
powershell
.venv\Scripts\python.exe src/main.py --input test/image --output output
문제 해결
1. "tesseract를 찾을 수 없습니다" 오류
원인: PATH 환경 변수가 설정되지 않음

해결:

환경 변수 설정 단계를 다시 확인
PowerShell 또는 명령 프롬프트를 재시작
컴퓨터 재부팅
2. "Korean language data not found" 오류
원인: 한국어 언어 팩이 설치되지 않음

해결:

tessdata repository에서 kor.traineddata 다운로드
C:\Program Files\Tesseract-OCR\tessdata 폴더에 복사
한국어 데이터 확인:
powershell
tesseract --list-langs
3. OCR 정확도가 낮음
해결책:

이미지 품질 확인 (최소 300 DPI 권장)
이미지가 너무 작거나 흐릿한 경우 스캔 재실행
회전되거나 기울어진 이미지는 사전에 보정
추가 정보
공식 문서: https://tesseract-ocr.github.io/
GitHub: https://github.com/tesseract-ocr/tesseract
한국어 학습 데이터: https://github.com/tesseract-ocr/tessdata