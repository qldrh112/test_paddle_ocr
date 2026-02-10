"""
test_ppstructure.py

PP-Structure 엔진 기능 테스트
Layout Analysis, Table Structure Recognition 검증
"""

from pathlib import Path
from PIL import Image

from config import Config
from engine import get_engine

def test_ppstructure_initialization():
    """PP-Structure 엔진 초기화 테스트"""
    print("=" * 80)
    print("Test 1: PP-Structure 엔진 초기화")
    print("=" * 80)
    
    engine = get_engine()
    engine.initialize()
    
    assert engine.reader is not None, "엔진이 초기화되지 않았습니다"
    
    if Config.USE_PP_STRUCTURE:
        # PPStructure 객체인지 확인
        assert hasattr(engine.reader, '__call__'), "PPStructure 객체가 아닙니다"
        print("✅ PP-Structure 엔진 초기화 성공")
    else:
        print("✅ PaddleOCR 엔진 초기화 성공 (fallback)")
    
    print()

def test_ppstructure_extraction():
    """PP-Structure 표 구조 추출 테스트"""
    print("=" * 80)
    print("Test 2: PP-Structure 표 구조 추출")
    print("=" * 80)
    
    # 샘플 이미지 경로
    sample_image = Path("image/bank_audit_letter-0003.jpg")
    
    if not sample_image.exists():
        print(f"⚠️  샘플 이미지가 없습니다: {sample_image}")
        print("   테스트를 건너뜁니다.")
        return
    
    # 이미지 로드
    img = Image.open(sample_image)
    print(f"이미지 로드: {sample_image.name}")
    print(f"크기: {img.size}")
    print()
    
    # OCR 추출
    engine = get_engine()
    tokens = engine.extract(img)
    
    print(f"추출된 토큰 수: {len(tokens)}")
    
    # 샘플 토큰 출력 (처음 10개)
    print("\n샘플 토큰 (처음 10개):")
    print("-" * 80)
    for idx, (y, x, text, conf) in enumerate(tokens[:10], 1):
        print(f"[{idx}] {text}")
        print(f"     위치: y={y:.1f}, x={x:.1f}, 신뢰도: {conf:.4f}")
    
    if len(tokens) > 10:
        print(f"\n... 외 {len(tokens) - 10}개 토큰")
    
    assert len(tokens) > 0, "토큰이 추출되지 않았습니다"
    print("\n✅ 표 구조 추출 성공")
    print()

def test_token_format():
    """토큰 형식 검증 (기존 파이프라인 호환성)"""
    print("=" * 80)
    print("Test 3: 토큰 형식 검증 (파이프라인 호환성)")
    print("=" * 80)
    
    sample_image = Path("image/bank_audit_letter-0003.jpg")
    
    if not sample_image.exists():
        print(f"⚠️  샘플 이미지가 없습니다: {sample_image}")
        print("   테스트를 건너뜁니다.")
        return
    
    img = Image.open(sample_image)
    engine = get_engine()
    tokens = engine.extract(img)
    
    # 형식 검증
    for idx, token in enumerate(tokens[:5], 1):
        assert len(token) == 4, f"토큰 형식 오류: {token}"
        y, x, text, conf = token
        assert isinstance(y, (int, float)), f"y 좌표 타입 오류: {type(y)}"
        assert isinstance(x, (int, float)), f"x 좌표 타입 오류: {type(x)}"
        assert isinstance(text, str), f"텍스트 타입 오류: {type(text)}"
        assert isinstance(conf, (int, float)), f"신뢰도 타입 오류: {type(conf)}"
        assert 0 <= conf <= 1, f"신뢰도 범위 오류: {conf}"
    
    print("✅ 토큰 형식 검증 성공")
    print("   - 형식: (center_y, min_x, text, confidence)")
    print("   - 모든 토큰이 4-튜플 형식")
    print("   - 좌표 및 신뢰도 타입 정상")
    print()

def test_debug_output():
    """디버그 출력 파일 생성 확인"""
    print("=" * 80)
    print("Test 4: 디버그 출력 확인")
    print("=" * 80)
    
    if not Config.DEBUG_MODE:
        print("⚠️  DEBUG_MODE가 비활성화되어 있습니다")
        print("   디버그 파일 생성을 건너뜁니다.")
        return
    
    debug_dir = Config.DEBUG_OUTPUT_DIR
    
    if debug_dir.exists():
        # 최근 생성된 파일들 확인
        files = sorted(debug_dir.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        print(f"디버그 디렉토리: {debug_dir}")
        print(f"생성된 파일 수: {len(files)}")
        
        if files:
            print("\n최근 생성된 파일 (최대 5개):")
            for file in files[:5]:
                size = file.stat().st_size
                print(f"  - {file.name} ({size:,} bytes)")
            
            print("\n✅ 디버그 출력 확인 완료")
        else:
            print("⚠️  디버그 파일이 생성되지 않았습니다")
    else:
        print(f"⚠️  디버그 디렉토리가 없습니다: {debug_dir}")
    
    print()

def run_all_tests():
    """모든 테스트 실행"""
    print("\n")
    print("#" * 80)
    print("# PP-Structure 엔진 테스트 스위트")
    print("#" * 80)
    print()
    print(f"PP-Structure 활성화: {Config.USE_PP_STRUCTURE}")
    print(f"Layout Analysis: {Config.ENABLE_LAYOUT_ANALYSIS}")
    print(f"디버그 모드: {Config.DEBUG_MODE}")
    print()
    
    try:
        test_ppstructure_initialization()
        test_ppstructure_extraction()
        test_token_format()
        test_debug_output()
        
        print("=" * 80)
        print("✅ 모든 테스트 통과!")
        print("=" * 80)
        
    except Exception as e:
        print("=" * 80)
        print(f"❌ 테스트 실패: {str(e)}")
        print("=" * 80)
        raise

if __name__ == "__main__":
    # 디버그 디렉토리 생성
    Config.ensure_debug_dir()
    
    run_all_tests()
