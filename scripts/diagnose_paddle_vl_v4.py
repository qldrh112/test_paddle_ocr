import os
import sys

# Ensure logs are visible
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

from paddlex import create_pipeline

def main():
    img_path = 'output/cropped/bank_audit_letter-0003_table_0.jpg'
    print(f"Starting pipeline creation for PaddleOCR-VL-1.5...")
    try:
        pipeline = create_pipeline(pipeline="PaddleOCR-VL-1.5")
    except Exception as e:
        print(f"Error creating pipeline: {e}")
        return

    print(f"Predicting for {img_path}...")
    try:
        output = pipeline.predict(img_path)
    except Exception as e:
        print(f"Error during prediction: {e}")
        return

    print(f"Prediction done. Output type: {type(output)}")
    # If it's a generator, convert to list to check length
    if not isinstance(output, list):
        print("Converting output to list...")
        output = list(output)
    print(f"Output length: {len(output)}")

    with open('paddle_vl_diag_v4.txt', 'w', encoding='utf-8') as f:
        for i, res in enumerate(output):
            f.write(f"Result {i} keys: {list(res.keys())}\n")
            print(f"Result {i} keys: {list(res.keys())}")
            for key in res.keys():
                val = res[key]
                if key == 'parsing_res_list':
                    f.write(f"  Key '{key}' is a list of length {len(val)}\n")
                    for j, block in enumerate(val):
                        f.write(f"    Block {j} type: {type(block)}\n")
                        # Try to see attributes or dict keys
                        if hasattr(block, '__dict__'):
                            f.write(f"    Block {j} dict keys: {list(block.__dict__.keys())}\n")
                        if hasattr(block, 'content'):
                            f.write(f"    Block {j} content snippet: {str(block.content)[:200]}\n")
                        if hasattr(block, 'type'):
                            f.write(f"    Block {j} block type: {block.type}\n")
                elif isinstance(val, list):
                    f.write(f"  Key '{key}' is a list of length {len(val)}\n")
                    if len(val) > 0:
                        f.write(f"    First item type: {type(val[0])}\n")
                        if isinstance(val[0], dict):
                            f.write(f"    First item keys: {list(val[0].keys())}\n")
                else:
                    f.write(f"  Key '{key}' type: {type(val)}\n")

if __name__ == "__main__":
    main()
