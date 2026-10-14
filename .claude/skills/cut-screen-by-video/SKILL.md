---
name: cut-screen-by-video
description: Нарезает загруженную запись экрана на скриншоты (кадр сохраняется, когда меняется хотя бы один элемент экрана) и кладёт их в Google Drive в папку приложения, подпапку «Скриншоты». Используй, когда я загружаю видео и говорю «нарежь на скриншоты», «порежь видео», «скриншоты из видео», или вызываю /cut-screen-by-video.
---

# cut-screen-by-video: нарезка видео на скриншоты

## Когда использовать
- Я загрузил запись экрана (.mov, .mp4) и прошу нарезать её на скриншоты.
- Нужно разобрать флоу приложения или конкурента по кадрам.
- Когда НЕ использовать: если нужен один конкретный кадр по таймкоду — просто вытащи его ffmpeg-ом.

## Входные данные
| Параметр | Обязателен | Откуда взять / по умолчанию |
|---|---|---|
| Видео | да | загруженные файлы (`/mnt/user-data/uploads/` или вложения чата); если видео несколько — обрабатывай все по порядку |
| Приложение | да | из моего сообщения или контекста; ищи в `portfolio.yaml` (если файла нет — спроси название) |
| Папка в Drive | нет | `<drive_folder_path приложения>/Скриншоты/<ГГГГ-ММ-ДД> <имя видео без расширения>`; если я назвал другую папку — клади туда |
| Формат | нет | jpg, качество 90 (png — если я попрошу) |

Если приложение не понятно, спроси одним вопросом. Остальное не уточняй — бери значения по умолчанию.

## Шаги
1. Прочитай `portfolio.yaml` (если работаешь в репозитории PM-OS), найди приложение, возьми `drive_folder_path` и `drive_folder_id`.
2. Проверь зависимости: `python3 -c "import cv2"`. Если нет — `pip install opencv-python-headless --break-system-packages`.
3. Скрипт нарезки: используй `cut.py`, лежащий рядом с этим SKILL.md. Если его нет (скилл установлен в Claude без файлов), сохрани копию из раздела «Скрипт» ниже в рабочую папку.
4. Для каждого видео:
   ```bash
   python3 cut.py "<видео>" "/mnt/user-data/outputs/screens/<имя видео>" --ext jpg
   ```
   Скрипт игнорирует статус-бар (часы, батарея), сохраняет кадр, когда экран устоялся и отличается от предыдущего сохранённого, а при непрерывном движении (видео, анимация) — не чаще раза в 3 секунды. Имена файлов: `001_00-02.74.jpg` = номер_минуты-секунды. Рядом пишется `_index.json`.
   Длинное видео (>5 мин) запускай в фоне и не трогай до завершения; ~1 минута видео ≈ 30 секунд обработки.
5. Быстрая проверка: посмотри 3–4 кадра (первый, средний, последний). Если кадров подозрительно много (>15 на минуту видео) или мало (<2 на минуту), подстрой `MINPIX` / `STABLE` в скрипте и перезапусти.
6. Положи скриншоты в Drive, в папку из «Входных данных» (её создаёт сам Drive при копировании, если её нет). Способы по приоритету:
   - **Компьютер связан и стоит Google Drive для desktop** (есть инструменты `mcp__remote-devices__*`): найди папку диска через `device_list_dir` в `~/Library/CloudStorage/` (папка `GoogleDrive-<email>/Мой диск` или `My Drive`), затем `device_commit_files` пачками по 50 файлов: `stagedPath` = файл из `/mnt/user-data/outputs/...`, `devicePath` = `~/Library/CloudStorage/GoogleDrive-<email>/Мой диск/<путь папки>/<файл>`. Drive синхронизирует сам.
   - **Компьютер не связан**: создай папку коннектором Google Drive (`create_file` с mimeType папки, родитель — `drive_folder_id` приложения; промежуточные папки тоже создай, если их нет). Если скриншотов ≤ 20 — загрузи их туда через `create_file` (`base64Content`, `contentMimeType: image/jpeg`, `disableConversionToGoogleType: true`). Если больше — запакуй в zip (частями до 30 МБ), отправь мне через SendUserFile и скажи, в какую папку их положить, плюс что после связывания компьютера с Drive для desktop это будет происходить автоматически.
   - Доступ к Drive и GitHub у тебя уже есть — не запрашивай его повторно.
7. Не коммить скриншоты в git.

## Формат результата
Коротко, по-русски:
- сколько скриншотов из какого видео (и длительность видео);
- ссылка на папку в Drive (или zip и куда его положить);
- если были сомнительные места (много кадров из-за проигрывания видео, повороты экрана) — одной строкой.

## Куда сохранять
- Скриншоты: Google Drive → `<drive_folder_path приложения>/Скриншоты/<ГГГГ-ММ-ДД> <имя видео>/`.
- В репозиторий ничего не сохранять.

## Скрипт (cut.py)
Копия `cut.py` на случай, если файла рядом нет:

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
