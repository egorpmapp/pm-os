#!/usr/bin/env python3
"""Раскладка скриншотов по папкам флоу по плану разметки.

Использование:
    python3 place.py <plan.json> <папка_результата>

plan.json:
{
  "flows": [
    {
      "path": "02 Пейволы/03 Вход в категорию Videos",
      "frames": [
        {"src": "/путь/к/скриншотам/V1", "n": 50, "caption": "Главный экран"},
        {"src": "/путь/к/скриншотам/V1", "n": 52, "caption": "Пейвол"}
      ]
    }
  ]
}

- n — номер кадра из _index.json соответствующей папки скриншотов (src).
- Файлы получают имена «NN Подпись.jpg» в порядке списка. Один кадр можно класть в несколько флоу.
- Если папка флоу уже существует в результате (докидываем к прежнему), нумерация продолжается после последнего файла.
- Печатает итог: сколько файлов в какую папку.
"""
import json, os, re, shutil, sys

plan, out = json.load(open(sys.argv[1])), sys.argv[2]
cache = {}

def frame_file(src, n):
    if src not in cache:
        cache[src] = {x["n"]: x["file"] for x in json.load(open(os.path.join(src, "_index.json")))}
    return os.path.join(src, cache[src][n])

bad = re.compile(r'[\\/:*?"<>|]')
total = 0
for fl in plan["flows"]:
    d = os.path.join(out, fl["path"])
    os.makedirs(d, exist_ok=True)
    nums = [int(m.group(1)) for f in os.listdir(d) if (m := re.match(r"(\d+) ", f))]
    k = max(nums, default=0)
    seen = {}
    for fr in fl["frames"]:
        k += 1
        cap = bad.sub("-", fr["caption"]).strip()
        seen[cap] = seen.get(cap, 0) + 1
        if seen[cap] > 1:
            cap = f"{cap} ({seen[cap]})"
        f = frame_file(fr["src"], fr["n"])
        shutil.copy2(f, os.path.join(d, f"{k:02d} {cap}{os.path.splitext(f)[1]}"))
        total += 1
    print(f"{fl['path']}: {len(fl['frames'])}")
print(f"Итого файлов: {total}")
