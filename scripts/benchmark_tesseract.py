import pytesseract
from pytesseract import Output
import argparse
import csv
import cv2
import pandas as pd
from pathlib import Path

# PATH에 tesseract 명령어가 없는 경우 경로 설정 필요
# 일반적으로 환경 변수나 'venv_tesseract' 컨텍스트에 포함되어 있다고 가정함

def group_into_rows(df, y_threshold=10):
    # df 포함 항목: left, top, width, height, text
    # 빈 텍스트 필터링
    df = df[df.text.str.strip() != '']
    
    # 상단(top) 좌표 기준으로 정렬
    df = df.sort_values(by='top')
    
    rows = []
    if df.empty:
        return rows
        
    current_row = []
    # 첫 번째 항목으로 행 시작
    # 순회하면서 'top' 좌표가 현재 행의 평균 'top' 또는 'bottom'과 가까운지 확인
    
    # 단순 로직: 단어의 top 좌표가 [이전_top - th, 이전_top + th] 범위 내에 있으면 동일한 행으로 간주
    # 하지만 폰트 크기도 고려해야 함
    # 여기서는 Y축 중심좌표를 사용함
    
    row_clusters = []
    
    # 처리를 용이하게 하기 위해 딕셔너리 리스트로 변환
    items = df.to_dict('records')
    
    current_cluster = [items[0]]
    
    for item in items[1:]:
        # 현재 클러스터의 평균 Y 중심점과 비교
        cluster_ys = [(i['top'] + i['height']/2) for i in current_cluster]
        avg_y = sum(cluster_ys) / len(cluster_ys)
        
        item_y = item['top'] + item['height']/2
        
        if abs(item_y - avg_y) < (item['height'] / 2 + 5): # 휴리스틱 허용 오차
            current_cluster.append(item)
        else:
            row_clusters.append(current_cluster)
            current_cluster = [item]
            
    if current_cluster:
        row_clusters.append(current_cluster)
        
    # 열 순서를 잡기 위해 각 클러스터를 'left' 좌표 기준으로 정렬
    parsed_rows = []
    for cluster in row_clusters:
        cluster.sort(key=lambda x: x['left'])
        parsed_rows.append([x['text'] for x in cluster])
        
    return parsed_rows

def process_image(img_path, output_csv_path):
    img = cv2.imread(str(img_path))
    
    # 페이지 분할 모드(PSM) 6(단일 균일 텍스트 블록 가정)이 표에 잘 작동하는 경우가 있음
    # 또는 4(가변 크기의 단일 텍스트 열 가정)
    # 또는 11(듬성듬성한 텍스트)
    # 기본값 3은 격자선이 없는 엄격한 표 형식에서 어려움을 겪을 수 있음
    # 일반적인 표 처리 관행에 따라 --psm 6 시도
    # 언어는 한국어+영어(kor+eng)로 설정
    
    custom_config = r'--oem 3 --psm 6 -l kor+eng'
    
    try:
        data = pytesseract.image_to_data(img, config=custom_config, output_type=Output.DATAFRAME)
    except pytesseract.TesseractNotFoundError:
        print("Tesseract 바이너리를 찾을 수 없습니다. 설치 여부와 PATH 설정을 확인하세요.")
        return
        
    # 행으로 그룹화
    rows = group_into_rows(data)
    
    with open(output_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
            
    print(f"처리 완료: {img_path} -> {output_csv_path}")

def main():
    parser = argparse.ArgumentParser(description="Tesseract 표 추출 벤치마크")
    parser.add_argument('--inputs', nargs='+', required=True, help="입력 이미지 경로 리스트")
    parser.add_argument('--outputs', nargs='+', required=True, help="출력 CSV 경로 리스트")
    
    args = parser.parse_args()
    
    if len(args.inputs) != len(args.outputs):
        print("오류: 입력과 출력의 개수가 일치해야 합니다.")
        return

    for img_p, out_p in zip(args.inputs, args.outputs):
        process_image(Path(img_p), Path(out_p))

if __name__ == "__main__":
    main()
