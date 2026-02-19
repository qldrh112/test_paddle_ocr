import sys
import os
from paddleocr import PaddleOCR

def main():
    # Note: doc_parser is invoked differently in newer versions
    # Usually it's via the PaddleOCR(lang='ch', layout=True, table=True, ...)
    # Or specifically using the doc_parser command/API
    
    # Let's try the standard table/layout mode first but with the newer environment
    # The doc-parser extra adds enhanced capabilities.
    
    ocr = PaddleOCR(use_angle_cls=True, lang='ch', layout=True, table=True)
    img_path = 'output/cropped/bank_audit_letter-0003_table_0.jpg'
    
    result = ocr.ocr(img_path, cls=True)
    
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            print(line)

if __name__ == "__main__":
    main()
