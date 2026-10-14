#!/usr/bin/env python3
"""Контактные листы для просмотра скриншотов: сетка миниатюр с номером кадра и таймкодом.

Использование:
    python3 sheet.py <папка_скриншотов> <папка_листов> [--cols 8] [--rows 3] [--w 180]

Создаёт sheet_01.jpg, sheet_02.jpg … (по cols*rows кадров на лист).
Листы нужны только Claude для разметки — в Drive их не класть.
"""
import argparse, json, os
import cv2, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--cols", type=int, default=8)
ap.add_argument("--rows", type=int, default=3)
ap.add_argument("--w", type=int, default=180)
a = ap.parse_args()

idx = json.load(open(os.path.join(a.src, "_index.json")))
os.makedirs(a.out, exist_ok=True)
per = a.cols * a.rows
LBL = 26
for p in range(0, len(idx), per):
    chunk = idx[p:p + per]
    tiles = []
    for x in chunk:
        im = cv2.imread(os.path.join(a.src, x["file"]))
        h = int(im.shape[0] * a.w / im.shape[1])
        im = cv2.resize(im, (a.w, h), interpolation=cv2.INTER_AREA)
        lab = np.full((LBL, a.w, 3), 255, np.uint8)
        m, s = divmod(x["t"], 60)
        cv2.putText(lab, f"#{x['n']}  {int(m):02d}:{s:04.1f}", (4, 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(np.vstack([lab, im]))
    H = max(t.shape[0] for t in tiles)
    tiles = [np.vstack([t, np.full((H - t.shape[0], a.w, 3), 255, np.uint8)]) for t in tiles]
    while len(tiles) % a.cols:
        tiles.append(np.full((H, a.w, 3), 255, np.uint8))
    rows = [np.hstack([np.pad(t, ((2, 2), (2, 2), (0, 0)), constant_values=200)
                       for t in tiles[r:r + a.cols]]) for r in range(0, len(tiles), a.cols)]
    name = f"sheet_{p // per + 1:02d}.jpg"
    cv2.imwrite(os.path.join(a.out, name), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])
    print(name, f"кадры {chunk[0]['n']}–{chunk[-1]['n']}")
