import easyocr
import argparse
import csv
import cv2
import numpy as np
from pathlib import Path

def overlap(box1, box2):
    # box: [min_x, max_x, min_y, max_y]
    # Y축 방향으로 충분히 겹치는지 확인하여 동일한 행인지 판별
    # 1차원(Y축)에 대한 중심점 또는 교집합 비율(IoU) 사용
    
    y1_min, y1_max = box1[2], box1[3]
    y2_min, y2_max = box2[2], box2[3]
    
    intersection = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
    union = max(y1_max, y2_max) - min(y1_min, y2_min)
    
    if union == 0: return 0
    
    # 교집합이 더 작은 박스 높이의 상당 부분을 차지하는지 확인
    min_height = min(y1_max - y1_min, y2_max - y2_min)
    if min_height == 0: return 0
    return intersection / min_height

def group_into_rows(results, y_threshold=0.5):
    # results: (bbox, text, prob)의 리스트
    # bbox 형식: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    
    # 각 박스의 Y축 범위 계산
    # [min_x, max_x, min_y, max_y]
    boxes = []
    for (bbox, text, prob) in results:
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        boxes.append({
            'min_x': min(xs), 'max_x': max(xs),
            'min_y': min(ys), 'max_y': max(ys),
            'text': text,
            'prob': prob
        })
        
    # Y좌표 기준으로 정렬
    boxes.sort(key=lambda b: (b['min_y'] + b['max_y'])/2)
    
    rows = []
    current_row = []
    
    if not boxes:
        return []

    # 단순 행 클러스터링
    # 새로운 박스의 수직 중심이 현재 행의 평균 Y 범위 내에 있으면 추가
    
    current_row.append(boxes[0])
    
    for box in boxes[1:]:
        # 마지막으로 추가된 박스 또는 현재 행의 평균과 근접성 확인
        # 현재 행의 마지막 박스를 기준으로 거리를 확인
        last_box = current_row[-1]
        
        # 수직 교집합 확인
        # 각 박스를 Y 구간으로 취급
        # Y 구간의 겹침이 유의미하면 동일한 행으로 간주
        
        lb_y = [0, 0, last_box['min_y'], last_box['max_y']]
        cb_y = [0, 0, box['min_y'], box['max_y']]
        
        ov = overlap(lb_y, cb_y)
        
        # 임계값: 겹침이 높이의 50%를 초과하는 경우
        if ov > y_threshold:
            current_row.append(box)
        else:
            rows.append(current_row)
            current_row = [box]
            
    if current_row:
        rows.append(current_row)
        
    # 각 행에 대해 X좌표 기준으로 정렬
    for row in rows:
        row.sort(key=lambda b: b['min_x'])
        
    return rows

def process_image(img_path, output_csv_path):
    reader = easyocr.Reader(['ko', 'en']) # 한국어와 영어 지원
    result = reader.readtext(str(img_path))
    
    rows = group_into_rows(result)
    
    # CSV로 저장
    # 참고: 이는 단순히 텍스트를 순서대로 덤프함
    # 실제 표 복원에는 열 정렬이 필요함
    # 이 벤치마크에서는 대략적으로 열을 정렬함
    
    # 고유한 열 중심점 또는 경계 찾기?
    # 단순화된 접근 방식: 행 내의 텍스트 항목을 그대로 작성
    # 나중에 비교 로직에서 가변 열 인덱스에 관계없이 내용을 확인할 것임
    # (bag-of-words 또는 퍼지 행 매칭 사용 시)
    
    # 현재는 가변 길이의 행을 그대로 작성
    # 사용자가 "표 데이터 추출"을 요청했으므로 구조 보존이 핵심임
    # 하지만 수직 구분선 없이는 완벽한 열 정렬이 어려움
    
    with open(output_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow([item['text'] for item in row])
            
    print(f"처리 완료: {img_path} -> {output_csv_path}")

def main():
    parser = argparse.ArgumentParser(description="EasyOCR 표 추출 벤치마크")
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
