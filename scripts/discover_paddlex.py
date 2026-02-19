import paddlex
from paddlex.repo_apis import PipelineConfig

def main():
    # In some versions of PaddleX 3.x, you can find the pipeline names in 
    # the repo_apis or similar.
    # Let's try to list files in paddlex/configs/ to see what's available
    import pkg_resources
    try:
        dist = pkg_resources.get_distribution('paddlex')
        path = dist.location + '/paddlex/configs'
        print(f"Config path: {path}")
        if os.path.exists(path):
            print(f"Pipelines: {os.listdir(path)}")
    except Exception as e:
        print(f"Error finding configs: {e}")

    # Another approach: check the codebase search
    # or just try names: 'OCR', 'layout_parsing', 'table_recognition'
    
if __name__ == "__main__":
    import os
    main()
