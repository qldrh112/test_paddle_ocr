import os
import requests
import tarfile
from pathlib import Path

# URLs for PP-OCRv4 and PP-Structure models (English/Chinese generic which supports numbers well)
# Using server-side generic models which are usually more robust
MODELS = {
    'det': 'https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_det_server_infer.tar',
    'rec': 'https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_rec_server_infer.tar',
    # 'table': 'https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/ch_ppstructure_mobile_v2.0_SLANet_infer.tar' # Slim version
    'table': 'https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/en_ppstructure_mobile_v2.0_SLANet_infer.tar', # English might be better for generic numbers/English headers? Let's stick to CH/EN generic.
    # Actually, let's use the one PP-Structure defaults to usually.
    # ch_ppstructure_mobile_v2.0_SLANet_infer is common.
    # Layout model (PicoDet)
    'layout': 'https://paddleocr.bj.bcebos.com/ppstructure/models/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer.tar'
}

# Let's try EN for table structure as headers are possibly English or mixed? User data has Korean.
# The `ch` models support Korean characters to some extent usually if not specific KO models.
# But PP-OCRv4-multilingual exists.
# However, PPStructure often defaults to these.
# Let's use the standard `ch_PP-OCRv4` sets as they are most stable and cover extensive charset.
MODELS['table'] = 'https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/ch_ppstructure_mobile_v2.0_SLANet_infer.tar'

MODEL_DIR = Path('models')

def download_file(url, save_path):
    print(f"Downloading {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded to {save_path}")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def extract_tar(tar_path, extract_path):
    print(f"Extracting {tar_path}...")
    try:
        with tarfile.open(tar_path, 'r') as tar:
            tar.extractall(path=extract_path)
            # Usually creates a subdir with same name as tar (minus extension)
        print(f"Extracted to {extract_path}")
    except Exception as e:
        print(f"Failed to extract {tar_path}: {e}")

def main():
    MODEL_DIR.mkdir(exist_ok=True)
    
    for name, url in MODELS.items():
        tar_name = url.split('/')[-1]
        tar_path = MODEL_DIR / tar_name
        
        if not tar_path.exists():
            if download_file(url, tar_path):
                extract_tar(tar_path, MODEL_DIR)
        else:
            print(f"{tar_name} already exists. Skipping download.")
            extract_tar(tar_path, MODEL_DIR)

if __name__ == "__main__":
    main()
