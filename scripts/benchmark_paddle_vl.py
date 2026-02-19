import os
import argparse
import pandas as pd
from pathlib import Path
from paddlex import create_pipeline

def process_images(input_paths, output_paths):
    # doc_parser 파이프라인 생성
    # 기본적으로 레이아웃, 표 분석 등을 위해 고성능 모델을 사용함
    # 첫 실행 시 모델을 자동으로 다운로드할 수 있음
    try:
        pipeline = create_pipeline(pipeline="PaddleOCR-VL-1.5")
    except Exception as e:
        print(f"파이프라인 생성 오류: {e}")
        return

    for img_path, out_csv in zip(input_paths, output_paths):
        print(f"처리 중: {img_path} -> {out_csv}")
        
        # 파이프라인 실행
        output = pipeline.predict(img_path)
        
        # 출력 결과 파싱
        # doc_parser는 인식된 요소들을 포함하는 결과 리스트를 반환함
        # 표(table) 요소를 찾아 그 내용을 추출해야 함
        
        table_data = []
        for res in output:
            # 결과에서 table_res_list 확인
            if 'table_res_list' in res:
                tables = res['table_res_list']
                for table in tables:
                    table_html = table.get('table_html') or table.get('html')
                    if table_html:
                        try:
                            df_list = pd.read_html(table_html)
                            if df_list:
                                # VL의 경우 전체 HTML 페이지 또는 표만 반환할 수 있음
                                # pd.read_html은 두 경우 모두 잘 작동함
                                table_data.extend(df_list[0].values.tolist())
                        except Exception as e:
                            print(f"표 HTML 파싱 오류: {e}")
            
            # 레거시 또는 대체 경로: doc_result 또는 elements
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
                                print(f"표 HTML 파싱 오류: {e}")
        
        if table_data:
            df = pd.DataFrame(table_data)
            df.to_csv(out_csv, index=False, header=False, encoding='utf-8-sig')
            print(f"성공적으로 표를 {out_csv}에 저장했습니다.")
        else:
            print(f"{img_path}에서 표 데이터를 찾을 수 없습니다.")
            # 비교 스크립트 중단을 방지하기 위해 빈 CSV 생성
            pd.DataFrame().to_csv(out_csv, index=False)

def main():
    parser = argparse.ArgumentParser(description="PaddleOCR-VL 벤치마크")
    parser.add_argument('--inputs', nargs='+', required=True, help="입력 이미지 리스트")
    parser.add_argument('--outputs', nargs='+', required=True, help="출력 CSV 경로 리스트")
    
    args = parser.parse_args()
    
    if len(args.inputs) != len(args.outputs):
        print("오류: 입력과 출력의 개수가 일치해야 합니다.")
        return
        
    process_images(args.inputs, args.outputs)

if __name__ == "__main__":
    main()
