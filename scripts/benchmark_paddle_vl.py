import os
import argparse
import pandas as pd
from pathlib import Path
from paddlex import create_pipeline

def process_images(input_paths, output_paths):
    # Create doc_parser pipeline
    # By default, this uses high-performance models for layout, table, etc.
    # It might attempt to download models on first run.
    try:
        pipeline = create_pipeline(pipeline="PaddleOCR-VL-1.5")
    except Exception as e:
        print(f"Error creating pipeline: {e}")
        return

    for img_path, out_csv in zip(input_paths, output_paths):
        print(f"Processing {img_path} to {out_csv}")
        
        # Run pipeline
        output = pipeline.predict(img_path)
        
        # Parse output
        # doc_parser returns a list of results, each containing recognized elements.
        # We need to find the table element and its content.
        
        table_data = []
        for res in output:
            # Check for table_res_list in the result
            if 'table_res_list' in res:
                tables = res['table_res_list']
                for table in tables:
                    table_html = table.get('table_html') or table.get('html')
                    if table_html:
                        try:
                            df_list = pd.read_html(table_html)
                            if df_list:
                                # For VL, it might return a full HTML page or just the table
                                # pd.read_html works well for both
                                table_data.extend(df_list[0].values.tolist())
                        except Exception as e:
                            print(f"Error parsing table HTML: {e}")
            
            # Legacy/Alternate path: doc_result or elements
            elif hasattr(res, 'doc_result') or 'doc_res' in res:
                doc_res = res.get('doc_res') or getattr(res, 'doc_result', {})
                elements = doc_res.get('elements', [])
                for element in elements:
                    if element.get('type') == 'table':
                        table_html = element.get('html_content') or element.get('html')
                        if table_html:
                            try:
                                df_list = pd.read_html(table_html)
                                if df_list:
                                    table_data.extend(df_list[0].values.tolist())
                            except Exception as e:
                                print(f"Error parsing table HTML: {e}")
        
        if table_data:
            df = pd.DataFrame(table_data)
            df.to_csv(out_csv, index=False, header=False, encoding='utf-8-sig')
            print(f"Successfully saved table to {out_csv}")
        else:
            print(f"No table data found in {img_path}")
            # Create empty CSV to avoid breaking comparison script
            pd.DataFrame().to_csv(out_csv, index=False)

def main():
    parser = argparse.ArgumentParser(description="PaddleOCR-VL Benchmark")
    parser.add_argument('--inputs', nargs='+', required=True, help="Input images")
    parser.add_argument('--outputs', nargs='+', required=True, help="Output CSV paths")
    
    args = parser.parse_args()
    
    if len(args.inputs) != len(args.outputs):
        print("Error: Number of inputs and outputs must match.")
        return
        
    process_images(args.inputs, args.outputs)

if __name__ == "__main__":
    main()
