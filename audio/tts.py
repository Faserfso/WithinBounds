#!/usr/bin/env python3
"""Озвучивает главы нейросетью Silero (CPU) в MP3.

Пример: python3 audio/tts.py --voices xenia,eugene ru/01-*.md
Нужны: torch, num2words, pandoc, ffmpeg. Модель Silero распространяется
по лицензии CC BY-NC-SA 4.0, то есть только для некоммерческого использования.
"""
import argparse
import os
import re
import subprocess
import tempfile
import wave

import torch
from num2words import num2words

MODEL_URL = "https://models.silero.ai/models/tts/ru/v4_ru.pt"
RATE = 48000
PANDOC = os.environ.get("PANDOC", "pandoc")


def words(n, **kw):
    return num2words(int(n), lang="ru", **kw)


def normalize(t):
    t = t.replace("\\-", "-")
    t = re.sub(r"^\s*-\s+", "", t)  # тире в начале реплики
    t = re.sub(r"\b(\d{1,2}):(\d{2})\b",
               lambda m: words(m[1]) + " " + ("ноль " + words(m[2][1]) if m[2][0] == "0" and m[2] != "00" else
                                              "ровно" if m[2] == "00" else words(m[2])), t)
    t = re.sub(r"\+?(\d+),(\d)\s*°",
               lambda m: f"{words(m[1])} и {words(m[2])} десятых градуса", t)
    t = re.sub(r"\+?(\d+)\s*°", lambda m: words(m[1]) + " градусов", t)
    t = re.sub(r"(\d+),(\d+)", lambda m: f"{words(m[1])} целых {words(m[2])}", t)
    t = re.sub(r"(\d+)\s*%", lambda m: words(m[1]) + " процентов", t)
    t = re.sub(r"\d+", lambda m: words(m[0]), t)
    t = t.replace('"', "").replace("*", "").replace("«", "").replace("»", "")
    t = re.sub(r"[^\w\s.,!?:;\-ёЁ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def chunks(text, limit=800):
    """Silero принимает до ~1000 символов, режем по предложениям."""
    out, cur = [], ""
    for s in re.split(r"(?<=[.!?…])\s+", text):
        if len(cur) + len(s) + 1 > limit and cur:
            out.append(cur)
            cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        out.append(cur)
    return out


def paragraphs(md_path):
    src = open(md_path, encoding="utf-8").read()
    title = re.match(r"#\s*\d+\.\s*(.+)", src).group(1).strip()
    body = src.split("\n", 1)[1]
    body = re.sub(r"^\s*\*[^*\n]+\*\s*\n", "", body)  # штамп времени не читаем
    plain = subprocess.run([PANDOC, "-f", "markdown-smart", "-t", "plain", "--wrap=none"],
                           input=body, capture_output=True, text=True, check=True).stdout
    paras = [p for p in (normalize(x) for x in plain.split("\n\n")) if p]
    return [normalize(title)] + paras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--voices", default="xenia")
    ap.add_argument("--out", default="build/audio")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    torch.set_num_threads(os.cpu_count() or 2)
    model_path = os.path.join(tempfile.gettempdir(), "silero_v4_ru.pt")
    if not os.path.exists(model_path):
        torch.hub.download_url_to_file(MODEL_URL, model_path)
    model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
    pause = torch.zeros(int(RATE * 0.45))
    for voice in a.voices.split(","):
        for f in a.files:
            slug = os.path.basename(f)[:-3]
            parts = []
            for i, p in enumerate(paragraphs(f)):
                for c in chunks(p):
                    parts.append(model.apply_tts(text=c, speaker=voice, sample_rate=RATE,
                                                 put_accent=True, put_yo=True))
                parts.append(pause if i else torch.zeros(RATE))
            audio = (torch.cat(parts) * 32767).clamp(-32768, 32767).to(torch.int16).numpy()
            wav = os.path.join(a.out, f"{slug}-{voice}.wav")
            with wave.open(wav, "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(audio.tobytes())
            mp3 = wav[:-4] + ".mp3"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-b:a", "64k", mp3], check=True)
            os.remove(wav)
            print(f"{mp3}: {len(audio) / RATE / 60:.1f} мин")


if __name__ == "__main__":
    main()
