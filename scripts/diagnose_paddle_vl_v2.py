import os
from paddlex import create_pipeline

def main():
    img_path = 'output/cropped/bank_audit_letter-0003_table_0.jpg'
    pipeline = create_pipeline(pipeline="PaddleOCR-VL-1.5")
    output = pipeline.predict(img_path)
    
    with open('paddle_vl_diag.txt', 'w', encoding='utf-8') as f:
        for i, res in enumerate(output):
            f.write(f"Result {i} keys: {list(res.keys())}\n")
            if 'doc_res' in res:
                doc_res = res['doc_res']
                f.write(f"Doc res keys: {list(doc_res.keys())}\n")
                if 'layout' in doc_res:
                    layout = doc_res['layout']
                    f.write(f"Layout keys: {list(layout.keys())}\n")
                    elements = layout.get('elements', [])
                    f.write(f"Number of elements: {len(elements)}\n")
                    for j, element in enumerate(elements):
                        f.write(f"Element {j} type: {element.get('type')}\n")
                        f.write(f"Element keys: {list(element.keys())}\n")
                        if 'table_res' in element:
                            f.write(f"Found table_res in element {j}\n")
                            f.write(f"table_res keys: {list(element['table_res'].keys())}\n")
                            f.write(f"HTML snippet: {element['table_res'].get('html')[:100] if element['table_res'].get('html') else 'None'}\n")

if __name__ == "__main__":
    main()
