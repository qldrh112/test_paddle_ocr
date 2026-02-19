import os
from paddlex import create_pipeline

def main():
    img_path = 'output/cropped/bank_audit_letter-0003_table_0.jpg'
    pipeline = create_pipeline(pipeline="PaddleOCR-VL-1.5")
    output = pipeline.predict(img_path)
    
    with open('paddle_vl_diag_v3.txt', 'w', encoding='utf-8') as f:
        for i, res in enumerate(output):
            f.write(f"Result {i} keys: {list(res.keys())}\n")
            for key in res.keys():
                val = res[key]
                if isinstance(val, list):
                    f.write(f"  Key '{key}' is a list of length {len(val)}\n")
                    if len(val) > 0:
                        f.write(f"    First item type: {type(val[0])}\n")
                        if isinstance(val[0], dict):
                            f.write(f"    First item keys: {list(val[0].keys())}\n")
                else:
                    f.write(f"  Key '{key}' type: {type(val)}\n")

if __name__ == "__main__":
    main()
