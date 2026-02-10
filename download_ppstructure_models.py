"""
download_ppstructure_models.py

PP-Structure 모델 다운로드 스크립트 (외부망 환경 전용)

외부망이 가능한 환경에서 실행하여 모델을 다운로드한 후,
오프라인 환경으로 복사하여 사용
"""

import os
from pathlib import Path
from paddleocr import PPStructure
import shutil

def download_models(save_dir: str = "./ppstructure_models"):
    """
    PP-Structure 모델을 다운로드하여 저장
    
    Args:
        save_dir: 모델 저장 디렉토리
    """
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("PP-Structure 모델 다운로드")
    print("=" * 80)
    print(f"저장 경로: {save_path.absolute()}")
    print()
    
    # 임시 디렉토리에 PPStructure 초기화 (모델 자동 다운로드)
    print("[1/3] Layout Detection 모델 다운로드...")
    temp_dir = Path("./.temp_ppstructure")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # PPStructure 초기화 시 모델이 자동으로 다운로드됨
        engine = PPStructure(
            lang='en',  # Layout 모델용
            layout=True,
            table=True,
            ocr=True,
            show_log=True,  # 다운로드 진행상황 표시
        )
        
        print("\n✅ 모델 다운로드 완료!")
        print()
        
        # PaddleOCR 모델 저장 경로 확인
        # 일반적으로 ~/.paddleocr/ 또는 사용자 홈 디렉토리에 저장됨
        home_dir = Path.home()
        paddleocr_dir = home_dir / ".paddleocr"
        
        if paddleocr_dir.exists():
            print(f"[2/3] 모델 파일 복사 중...")
            print(f"원본: {paddleocr_dir}")
            print(f"대상: {save_path}")
            print()
            
            # 전체 .paddleocr 디렉토리 복사
            # 디렉토리가 이미 존재하면 삭제 후 복사
            if save_path.exists():
                shutil.rmtree(save_path)
            shutil.copytree(paddleocr_dir, save_path)
            
            print("✅ 모델 파일 복사 완료!")
            print()
            
            # 복사된 파일 목록 출력
            print("[3/3] 다운로드된 모델 확인:")
            print("-" * 80)
            
            total_size = 0
            file_count = 0
            
            for item in save_path.rglob("*"):
                if item.is_file():
                    size = item.stat().st_size
                    total_size += size
                    file_count += 1
                    
                    # 주요 모델 파일만 출력
                    if item.suffix in ['.pdparams', '.pdiparams', '.pdmodel']:
                        rel_path = item.relative_to(save_path)
                        print(f"  {rel_path} ({size:,} bytes)")
            
            print("-" * 80)
            print(f"총 파일 수: {file_count}")
            print(f"총 크기: {total_size / (1024**2):.2f} MB")
            print()
            
            print("=" * 80)
            print("✅ 모델 다운로드 및 저장 완료!")
            print("=" * 80)
            print()
            print("다음 단계:")
            print(f"1. '{save_path}' 디렉토리를 오프라인 환경으로 복사")
            print("2. config.py에서 PPSTRUCTURE_MODEL_DIR 경로 설정")
            print("3. PP-Structure 엔진 재시작")
            print()
            
        else:
            print(f"⚠️  PaddleOCR 모델 디렉토리를 찾을 수 없습니다: {paddleocr_dir}")
            print("   모델이 다른 위치에 저장되었을 수 있습니다.")
            
    except Exception as e:
        print(f"❌ 모델 다운로드 실패: {str(e)}")
        raise
    
    finally:
        # 임시 디렉토리 정리
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    import sys
    
    # 명령줄 인자로 저장 경로 지정 가능
    save_dir = sys.argv[1] if len(sys.argv) > 1 else "./ppstructure_models"
    
    download_models(save_dir)
