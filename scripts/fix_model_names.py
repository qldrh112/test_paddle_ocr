from pathlib import Path
import shutil

models_dir = Path('models')

for model_dir in models_dir.iterdir():
    if model_dir.is_dir():
        print(f"Processing {model_dir}")
        search_files = ['inference.pdmodel', 'inference.pdiparams']
        for file_name in search_files:
            file_path = model_dir / file_name
            if file_path.exists():
                new_name = file_name.replace('inference', 'model')
                new_path = model_dir / new_name
                if not new_path.exists():
                    shutil.copy(file_path, new_path)
                    print(f"Copied {file_name} to {new_name}")
                else:
                    print(f"{new_name} already exists")
