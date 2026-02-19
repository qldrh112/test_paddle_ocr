import os
import requests
import tarfile
from pathlib import Path

# PP-OCRv4 및 PP-Structure 모델 URL (숫자와 일반 텍스트에 강한 서버용 모델 사용)
MODELS = {
    'det': 'https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_det_server_infer.tar',
    'rec': 'https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_rec_server_infer.tar',
    # 'table': 'https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/ch_ppstructure_mobile_v2.0_SLANet_infer.tar' # 경량 버전
    'table': 'https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/en_ppstructure_mobile_v2.0_SLANet_infer.tar', # 영문 모델이 일반적인 숫자/영문 헤더에 유리할 수 있음
    # 레이아웃 모델 (PicoDet)
    'layout': 'https://paddleocr.bj.bcebos.com/ppstructure/models/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer.tar'
}

# 표준 `ch_PP-OCRv4` 세트는 안정적이며 광범위한 문자셋을 커버하므로 이를 사용함
MODELS['table'] = 'https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/ch_ppstructure_mobile_v2.0_SLANet_infer.tar'

MODEL_DIR = Path('models')

def download_file(url, save_path):
    print(f"다운로드 중: {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"다운로드 완료: {save_path}")
        return True
    except Exception as e:
        print(f"다운로드 실패 ({url}): {e}")
        return False

def extract_tar(tar_path, extract_path):
    print(f"압축 해제 중: {tar_path}...")
    try:
        with tarfile.open(tar_path, 'r') as tar:
            tar.extractall(path=extract_path)
            # 일반적으로 tar 파일명(확장자 제외)과 동일한 하위 디렉토리가 생성됨
        print(f"압축 해제 완료: {extract_path}")
    except Exception as e:
        print(f"압축 해제 실패 ({tar_path}): {e}")

def main():
    MODEL_DIR.mkdir(exist_ok=True)
    
    for name, url in MODELS.items():
        tar_name = url.split('/')[-1]
        tar_path = MODEL_DIR / tar_name
        
        if not tar_path.exists():
            if download_file(url, tar_path):
                extract_tar(tar_path, MODEL_DIR)
        else:
            print(f"{tar_name} 파일이 이미 존재합니다. 다운로드를 건너뜁니다.")
            extract_tar(tar_path, MODEL_DIR)

if __name__ == "__main__":
    main()
