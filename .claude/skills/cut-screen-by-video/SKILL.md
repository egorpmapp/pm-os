---
name: cut-screen-by-video
description: Нарезает загруженную запись экрана приложения на скриншоты (кадр — при любом изменении экрана), раскладывает их по папкам User Flow (Онбординг, Пейволы, Меню и главный экран, Флоу фичей) и кладёт в Google Drive в папку приложения; новые видео к тому же приложению докидываются в существующую структуру. Используй, когда я загружаю видео и говорю «нарежь на скриншоты», «разложи по флоу», «докинь видео», или вызываю /cut-screen-by-video.
---

# cut-screen-by-video: видео → скриншоты → папки User Flow в Drive

## Когда использовать
- Я загрузил запись экрана приложения (.mov, .mp4) и прошу нарезать её на скриншоты.
- Я докидываю новое видео к приложению, у которого папка User Flow уже есть.
- Когда НЕ использовать: если нужен один кадр по таймкоду — просто вытащи его ffmpeg-ом.

## Входные данные
| Параметр | Обязателен | Откуда взять / по умолчанию |
|---|---|---|
| Видео | да | загруженные файлы (`/mnt/user-data/uploads/` или вложения чата); несколько видео — это одна сессия, обрабатывай вместе, в порядке времени записи |
| Приложение | да | из сообщения или контекста; `drive_folder_path` / `drive_folder_id` — из `portfolio.yaml` (если файла нет — спроси название) |
| Папка в Drive | нет | `<drive_folder_path приложения>/User Flow`; если я назвал другую — туда |

Если приложение не понятно — спроси одним вопросом. Остальное не уточняй.

## Итоговая структура в Drive
```
<приложение>/User Flow/
  01 Онбординг/        NN <флоу>/   — первый запуск: сплэш, системные запросы, экраны онбординга до главного экрана
  02 Пейволы/          NN <точка входа>/ — каждый показ пейвола: экран до → пейвол → после закрытия; отдельно флоу покупки
  03 Меню/             NN <вкладка> [до/после покупки]/ — корневые экраны: главный экран и каждая вкладка таб-бара
  04 Флоу фичей/       NN <раздел (вкладка)>/NN <фича>/ — пройденные до конца сценарии фич
```
В папке флоу файлы называются `NN Подпись шага.jpg` (01, 02, …) — порядок как видит пользователь.
**Плоской папки со всеми скриншотами подряд в Drive быть не должно** — только разложенные флоу. `_index.json` и контактные листы в Drive тоже не кладутся.

## Правила разметки (как в эталоне Darksy Cleaner)
1. **Каждый флоу фичи начинается с главного экрана** (или корня вкладки, если фича живёт во вкладке): первый файл — главный экран, дальше путь до фичи. Дубли кадров между флоу — это нормально.
2. **Во «Флоу фичей» — только сценарии, пройденные до конца после покупки.** Попытки до покупки, упёршиеся в пейвол, идут в «02 Пейволы» как точка входа пейвола (экран до → пейвол → что после закрытия).
3. **Анимации и переходы не схлопывать**: появление крестика на пейволе, анимации онбординга, промежуточные модалки — отдельными кадрами.
4. **Схлопывать изменения только цифр/счётчиков/процентов/табов**: загрузка 10% → 50% → 90% = один кадр «Загрузка»; растущий счётчик = один кадр.
5. **Пейвол**: обязательно кадр с активным **Yearly** (или самым длинным планом), если он был на видео.
6. Системные экраны iOS (разрешения, удаление, App Store, Настройки) — часть флоу, подписывай что это.
7. Подписи — по-русски, коротко, с дословными ключевыми словами UI: «Пейвол → появляется крестик», «Диалог “Delete?”», «Результат: Cleared 310 MB».
8. Номера папок — по порядку появления в приложении (онбординг → вкладки слева направо → фичи по порядку на экране).

## Шаги
1. Прочитай `portfolio.yaml` (если работаешь в репозитории PM-OS), возьми `drive_folder_path` и `drive_folder_id` приложения.
2. Зависимости: `python3 -c "import cv2"`; если нет — `pip install opencv-python-headless --break-system-packages`.
3. Скрипты `cut.py`, `sheet.py`, `place.py` лежат рядом с этим SKILL.md. Если их нет (скилл установлен в Claude без файлов) — сохрани копии из раздела «Скрипты» в рабочую папку.
4. **Существующая структура.** Узнай, есть ли уже `<приложение>/User Flow` в Drive, и получи полный список папок и файлов:
   - компьютер связан и стоит Google Drive для desktop → `device_list_dir` (recursive) по `~/Library/CloudStorage/GoogleDrive-<email>/Мой диск/<drive_folder_path>/User Flow`;
   - иначе → коннектор Google Drive (`search_files` по родителю).
   Сохрани список в `existing.txt` — он нужен для разметки. Если папки нет — это первое видео.
5. **Нарезка** каждого видео в свою папку (V1, V2 … по порядку записи):
   ```bash
   python3 cut.py "<видео>" work/raw/V1 --ext jpg
   ```
   Длинное видео (>5 мин) запускай в фоне; ~1 мин видео ≈ 30 с обработки.
6. **Контактные листы** для просмотра:
   ```bash
   python3 sheet.py work/raw/V1 work/sheets/V1
   ```
   Просмотри **все** листы (Read по картинке). При сомнении открой отдельный кадр крупно. Пока смотришь, веди заметки: номер кадра → что на экране, куда ведёт, до или после покупки.
7. **План разметки** `work/plan.json` (формат — в описании `place.py`): для каждого флоу путь папки и список кадров `{src, n, caption}` по правилам выше.
   **Если User Flow уже существует (докидываем видео):**
   - флоу, которого ещё нет → новая папка со следующим свободным номером в нужном разделе (не переименовывай и не перенумеровывай существующие папки);
   - флоу, который уже есть, и новое видео показывает **то же самое** → пропусти;
   - флоу уже есть, но новое видео показывает **другой вариант** (другой пейвол, новые шаги, изменённый текст/цена) → новая папка рядом: `NN <флоу> — вариант <ГГГГ-ММ-ДД>`; в старую папку не дописывай;
   - для главного экрана в начале флоу можно брать кадр из нового видео.
   Ничего в Drive не удаляй.
8. **Раскладка**:
   ```bash
   python3 place.py work/plan.json "work/User Flow"
   ```
   Проверь итог: число папок и файлов, просмотри 2–3 папки (первый кадр — главный экран у фич, у пейволов есть Yearly).
9. **Загрузка в Drive** — только содержимое `work/User Flow` (без raw, листов, json):
   - **Компьютер связан + Drive для desktop**: скопируй `work/User Flow` в `/mnt/user-data/outputs/User Flow`, затем `device_commit_files` пачками по 50: `stagedPath` = файл в `/mnt/user-data/outputs/User Flow/...`, `devicePath` = `~/Library/CloudStorage/GoogleDrive-<email>/Мой диск/<drive_folder_path>/User Flow/<тот же относительный путь>`. Существующие файлы не перезаписывай (новые имена не пересекаются, если соблюдён шаг 7).
   - **Компьютер не связан**: создай недостающие папки коннектором Google Drive (`create_file`, mimeType папки, родитель по цепочке от `drive_folder_id`). Файлы ≤ 30 штук — загрузи `create_file` (`base64Content`, `contentMimeType: image/jpeg`, `disableConversionToGoogleType: true`). Больше — запакуй `work/User Flow` в zip (частями до 30 МБ, структура папок сохранена), отправь через SendUserFile и скажи, куда распаковать; добавь, что со связанным компьютером и Drive для desktop это происходит автоматически.
   - Доступ к Drive и GitHub уже выдан — не запрашивай его повторно.
10. Удали рабочие файлы (`work/raw`, `work/sheets`, `/mnt/user-data/outputs/User Flow`) после успешной загрузки. В git ничего не коммить.

## Формат результата
Коротко, по-русски:
- сколько видео и скриншотов обработано, сколько флоу получилось (по разделам: онбординг / пейволы / меню / фичи);
- при докидывании: какие папки добавлены новыми, какие флоу пропущены как уже существующие, какие появились как варианты;
- ссылка на папку User Flow в Drive (или zip и куда его распаковать);
- одной строкой — что не удалось разметить уверенно (если было).

## Куда сохранять
- Google Drive → `<drive_folder_path приложения>/User Flow/…` (структура выше).
- В репозиторий ничего не сохранять.

## Скрипты
Копии файлов на случай, если рядом со SKILL.md их нет. Сохрани каждый под указанным именем.

### cut.py

```python
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
```

### sheet.py

```python
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
```

### place.py

```python
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
```
