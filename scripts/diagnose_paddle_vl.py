import os
from paddlex import create_pipeline

def main():
    img_path = 'output/cropped/bank_audit_letter-0003_table_0.jpg'
    pipeline = create_pipeline(pipeline="PaddleOCR-VL-1.5")
    output = pipeline.predict(img_path)
    
    for i, res in enumerate(output):
        print(f"Result {i} keys: {res.keys()}")
        if 'doc_result' in res:
            doc_res = res['doc_result']
            print(f"Doc result keys: {doc_res.keys()}")
            elements = doc_res.get('elements', [])
            print(f"Number of elements: {len(elements)}")
            for j, element in enumerate(elements):
                print(f"Element {j} type: {element.get('type')}")
                # Print all keys of the first element to see what's inside
                if j == 0:
                    print(f"Element keys: {element.keys()}")

if __name__ == "__main__":
    main()
