from pathlib import Path
import shutil

models_dir = Path('models')

# 모델 디렉토리 내의 파일명을 PaddleOCR 표준에 맞게 정정
for model_dir in models_dir.iterdir():
    if model_dir.is_dir():
        print(f"처리 중: {model_dir}")
        # 일부 버전에서 요구하는 'model.*' 형식을 맞추기 위해 복사
        search_files = ['inference.pdmodel', 'inference.pdiparams']
        for file_name in search_files:
            file_path = model_dir / file_name
            if file_path.exists():
                new_name = file_name.replace('inference', 'model')
                new_path = model_dir / new_name
                if not new_path.exists():
                    shutil.copy(file_path, new_path)
                    print(f"{file_name} 파일을 {new_name}(으)로 복사했습니다.")
                else:
                    print(f"{new_name} 파일이 이미 존재합니다.")
