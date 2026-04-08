#!/usr/bin/env python3
"""
PaddleOCR 결과 재분석 스크립트

PP-StructureV2가 표의 셀 경계를 인식하지 못해 1개 행에 모든 값을 병합한 경우,
열별 패턴(정규식)으로 각 셀을 분리하여 20개 행으로 복원한 뒤 F1을 재산출합니다.

대상: output/paddleocr_results/cropped/paddle_sheet1_crop.csv  (sheet1만 구조적으로 복원 가능)
비교: output/easyocr_results/cropped/easy_sheet1_crop.csv
정답: public/label/sheet1_label.csv
"""

import re
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from compare_results import load_csv, compare_tables


# ── 열별 분리 패턴 ────────────────────────────────────────────────────────────
#  Col1: 금융상품 종류 (예금/적금/예·적금) → 중국어 모델로 인식 불가, 완전 공백
#  Col2: 계좌번호  (\d{3}-\d{4}-\d{4}-\d{2})
#  Col3: 금액      ([\d,\.]+(?:KRW|USD|JPY))
#  Col4: 연이자율  (\d+\.?\d*%)
#  Col5: 최종이자지급일 (\d{2}\.\d{2}\.\d{2})
#  Col6: 만기일    (\d{2}\.\d{2}\.\d{2})
#  Col7: 비고      공백 구분 (내용은 한자로 오인식, 매칭 불가 예상)

PATTERNS = {
    'account': re.compile(r'\d{3}-\d{4}-\d{4}-\d{2}'),
    'amount':  re.compile(r'[\d,\.]+(?:KRW|USD|JPY)'),
    'rate':    re.compile(r'\d+\.?\d*%'),
    'date':    re.compile(r'\d{2}\.\d{2}\.\d{2}'),
}


def split_paddle_sheet1(csv_path: Path) -> list[list[str]]:
    """병합된 paddle sheet1 CSV를 20개 행으로 복원"""
    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))

    # row[0] = 헤더(오인식), row[1] = 데이터 행(7개 열, 각각 병합)
    if len(rows) < 2:
        return []

    data = rows[1]
    col1_raw = data[0] if len(data) > 0 else ''   # 금융상품 종류 (비어있음)
    col2_raw = data[1] if len(data) > 1 else ''   # 계좌번호 (병합)
    col3_raw = data[2] if len(data) > 2 else ''   # 금액 (병합)
    col4_raw = data[3] if len(data) > 3 else ''   # 연이자율 (병합)
    col5_raw = data[4] if len(data) > 4 else ''   # 최종이자지급일 (병합)
    col6_raw = data[5] if len(data) > 5 else ''   # 만기일 (병합)
    col7_raw = data[6] if len(data) > 6 else ''   # 비고 (병합, 한자 오인식)

    accounts = PATTERNS['account'].findall(col2_raw)
    amounts  = PATTERNS['amount'].findall(col3_raw)
    rates    = PATTERNS['rate'].findall(col4_raw)
    dates1   = PATTERNS['date'].findall(col5_raw)
    dates2   = PATTERNS['date'].findall(col6_raw)
    notes    = col7_raw.strip().split() if col7_raw.strip() else []

    n = len(accounts)  # 기준: 계좌번호 수 (가장 신뢰도 높은 패턴)

    print(f"\n  [분리 결과]")
    print(f"  Col1 (금융상품 종류): {'비어있음 (중국어 모델로 인식 불가)':}")
    print(f"  Col2 (계좌번호)    : {n}개 추출 (정답: 20개)")
    print(f"  Col3 (금액)        : {len(amounts)}개 추출 (정답: 20개)")
    print(f"  Col4 (연이자율)    : {len(rates)}개 추출 (정답: 20개)")
    print(f"  Col5 (최종이자일)  : {len(dates1)}개 추출 (정답: 20개)")
    print(f"  Col6 (만기일)      : {len(dates2)}개 추출 (정답: 20개)")
    print(f"  Col7 (비고)        : {len(notes)}개 추출 (정답: 7개, 오인식으로 매칭 불가 예상)")

    split_rows = []
    for i in range(n):
        row = [
            '',                                          # Col1: 금융상품 종류 (공백)
            accounts[i] if i < len(accounts) else '',   # Col2: 계좌번호
            amounts[i]  if i < len(amounts)  else '',   # Col3: 금액
            rates[i]    if i < len(rates)    else '',   # Col4: 연이자율
            dates1[i]   if i < len(dates1)   else '',   # Col5: 최종이자지급일
            dates2[i]   if i < len(dates2)   else '',   # Col6: 만기일
            notes[i]    if i < len(notes)    else '',   # Col7: 비고 (오인식 그대로)
        ]
        split_rows.append(row)

    return split_rows


def save_csv(rows: list[list[str]], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def print_comparison(label: str, stats: dict, n_gt: int):
    print(f"\n  {label}")
    print(f"    Precision : {stats['precision']:.3f}")
    print(f"    Recall    : {stats['recall']:.3f}")
    print(f"    F1-Score  : {stats['f1']:.3f}")
    print(f"    매칭 셀   : {stats['matched']} / {n_gt} (정답 셀 수)")


def main():
    gt_path    = ROOT / 'public/label/sheet1_label.csv'
    paddle_orig = ROOT / 'output/paddleocr_results/cropped/paddle_sheet1_crop.csv'
    paddle_fixed = ROOT / 'output/paddleocr_results/fixed/paddle_sheet1_fixed.csv'
    easy_path  = ROOT / 'output/easyocr_results/cropped/easy_sheet1_crop.csv'
    tess_path  = ROOT / 'output/tesseract_results/cropped/tess_sheet1_crop.csv'

    gt = load_csv(str(gt_path))
    n_gt_cells = sum(1 for r in gt for c in r if c.strip())

    print("=" * 62)
    print("PaddleOCR 병합 셀 분리 후 F1 재산출 (sheet1 / 0003 cropped)")
    print("=" * 62)

    # ── 1. 분리 전 원본 ─────────────────────────────────────────────────────
    print("\n[1] 병합 전 원본 결과 (비교 기준)")
    pred_orig = load_csv(str(paddle_orig))
    stats_orig = compare_tables(gt, pred_orig)
    print_comparison("PaddleOCR (원본, 병합 상태)", stats_orig, n_gt_cells)

    # ── 2. 셀 분리 후 복원 ──────────────────────────────────────────────────
    print("\n[2] 병합 셀 분리 후 복원")
    split_rows = split_paddle_sheet1(paddle_orig)
    save_csv(split_rows, paddle_fixed)
    print(f"  → 저장: {paddle_fixed.relative_to(ROOT)}")

    pred_fixed = load_csv(str(paddle_fixed))
    stats_fixed = compare_tables(gt, pred_fixed)
    print_comparison("PaddleOCR (분리 후)", stats_fixed, n_gt_cells)

    # ── 3. 다른 엔진과 비교 ─────────────────────────────────────────────────
    print("\n[3] 엔진 간 비교 (sheet1 / cropped)")
    easy_stats = compare_tables(gt, load_csv(str(easy_path)))
    tess_stats = compare_tables(gt, load_csv(str(tess_path)))

    print(f"\n  {'엔진':<20} {'Precision':>10} {'Recall':>8} {'F1':>8} {'매칭/정답':>10}")
    print("  " + "-" * 60)
    for name, s in [
        ("EasyOCR",               easy_stats),
        ("Tesseract",             tess_stats),
        ("PaddleOCR (원본)",      stats_orig),
        ("PaddleOCR (분리 후)",   stats_fixed),
    ]:
        print(f"  {name:<20} {s['precision']:>10.3f} {s['recall']:>8.3f} "
              f"{s['f1']:>8.3f} {s['matched']:>5}/{n_gt_cells}")

    # ── 4. 열별 인식 상세 ──────────────────────────────────────────────────
    print("\n[4] PaddleOCR 분리 후 열별 인식 품질 분석")
    col_names = ['금융상품 종류', '계좌번호', '금액', '연이자율', '최종이자일', '만기일', '비고']
    for col_idx, col_name in enumerate(col_names):
        gt_col   = [r[col_idx] if col_idx < len(r) else '' for r in gt]
        pred_col = [r[col_idx] if col_idx < len(r) else '' for r in split_rows]
        gt_col_nz   = [c for c in gt_col   if c.strip()]
        pred_col_nz = [c for c in pred_col if c.strip()]
        col_stats = compare_tables([[c] for c in gt_col_nz], [[c] for c in pred_col_nz])
        print(f"  {col_name:<14}: F1={col_stats['f1']:.3f}  "
              f"pred={len(pred_col_nz)}개 / gt={len(gt_col_nz)}개")

    print("\n[5] 주의사항")
    print("  - Sheet2/5/9: PP-StructureV2가 표 구조를 파편화하여 분리 불가")
    print("  - Col1 (금융상품 종류): 중국어 모델로 한국어 인식 불가 → F1=0")
    print("  - Col7 (비고): '비고' → '明卫/日卫' 오인식 → F1≈0")
    print("  - 분리 후 F1은 텍스트 인식 품질만 반영, 구조 인식 실패는 별도 평가 필요")


if __name__ == '__main__':
    main()
