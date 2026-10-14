#!/usr/bin/env python3
"""Нарезка записи экрана на скриншоты: кадр сохраняется, когда меняется хотя бы один элемент экрана.

Использование:
    python3 cut.py <видео> <папка_вывода> [--ext jpg|png] [--quality 90]

Логика:
- статус-бар (верхние ~5.5% кадра) игнорируется: часы и батарея не считаются изменением;
- кадр сохраняется, когда экран «устоялся» (не меняется STABLE секунд) и отличается от последнего сохранённого;
- при непрерывном движении (видео, анимация) кадр сохраняется не чаще раза в MAXGAP секунд;
- рядом пишется _index.json: номер, таймкод, имя файла, тип кадра.
"""
import argparse, json, os, sys

try:
    import cv2
except ImportError:
    sys.exit("Нужен OpenCV: pip install opencv-python-headless")

TOP_FRAC = 0.055  # доля высоты кадра под статус-бар
PIX = 28          # порог разницы яркости пикселя (шум)
MINPIX = 12       # сколько пикселей (в уменьшенном кадре) должно измениться
STABLE = 0.25     # сек: экран должен простоять неподвижно
MAXGAP = 3.0      # сек: при непрерывном движении — не чаще этого
NORM_W = 222      # ширина уменьшенного кадра для сравнения


def small(f):
    top = int(round(TOP_FRAC * f.shape[0]))
    g = cv2.cvtColor(f[top:], cv2.COLOR_BGR2GRAY)
    k = NORM_W / g.shape[1]
    g = cv2.resize(g, (NORM_W, max(1, int(g.shape[0] * k))), interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(g, (3, 3), 0)


def changed(a, b):
    return int((cv2.absdiff(a, b) > PIX).sum()) >= MINPIX


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--ext", default="jpg", choices=["jpg", "png"])
    ap.add_argument("--quality", type=int, default=90)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    cap = cv2.VideoCapture(a.src)
    if not cap.isOpened():
        sys.exit(f"Не удалось открыть видео: {a.src}")
    params = [cv2.IMWRITE_JPEG_QUALITY, a.quality] if a.ext == "jpg" else []

    shots = []
    st = {"saved": None, "last_t": -1e9}

    def save(frame, t, s, kind):
        n = len(shots) + 1
        m, sec = divmod(t, 60)
        name = f"{n:03d}_{int(m):02d}-{sec:05.2f}.{a.ext}"
        cv2.imwrite(os.path.join(a.out, name), frame, params)
        shots.append({"n": n, "t": round(t, 2), "file": name, "kind": kind})
        st["saved"], st["last_t"] = s, t

    anchor = still_since = motion_since = None
    while True:
        ok, f = cap.read()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        s = small(f)
        if st["saved"] is None:
            save(f, t, s, "start")
            anchor, still_since = s, t
            continue
        if anchor.shape != s.shape:  # смена ориентации
            anchor = s; still_since = t
            save(f, t, s, "rotate")
            continue
        if changed(s, anchor):
            anchor, still_since = s, t
            if motion_since is None:
                motion_since = t
        else:
            if t - still_since >= STABLE:
                if st["saved"].shape == s.shape and changed(s, st["saved"]):
                    save(f, t, s, "settled")
                motion_since = None
        if (motion_since is not None and t - motion_since >= MAXGAP
                and t - st["last_t"] >= MAXGAP and changed(s, st["saved"])):
            save(f, t, s, "motion")

    json.dump(shots, open(os.path.join(a.out, "_index.json"), "w"), indent=1, ensure_ascii=False)
    print(f"Скриншотов: {len(shots)} (из них при непрерывном движении: "
          f"{sum(1 for x in shots if x['kind'] == 'motion')})")


if __name__ == "__main__":
    main()
