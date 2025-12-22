#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict

import cv2
import ffmpeg
from PIL import Image

# ================= CONFIG =================

TARGET_SHORT_SIDE = 720
Image.MAX_IMAGE_PIXELS = None

IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}
VIDEO_FORMATS = {'.mp4', '.mkv', '.mov', '.avi', '.ts', '.flv', '.wmv', '.webm'}

ALLOWED_IMAGE = {'.png', '.gif'}
ALLOWED_VIDEO = {'.mp4'}

# ================= UTIL =================

def alphanum_key(p: Path):
    return [int(x) if x.isdigit() else x.lower()
            for x in re.split(r'(\d+)', p.stem)]

def force_even(img: Image.Image) -> Image.Image:
    w, h = img.size
    nw, nh = w + (w % 2), h + (h % 2)
    if (nw, nh) == (w, h):
        return img
    out = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
    out.paste(img, (0, 0))
    img.close()
    return out

def resize_keep_aspect(img: Image.Image) -> Image.Image:
    w, h = img.size
    short = min(w, h)
    if short <= TARGET_SHORT_SIDE:
        return force_even(img)

    scale = TARGET_SHORT_SIDE / short
    nw, nh = round(w * scale), round(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    return force_even(img)

# ================= SIZE CHECK =================

def short_side_image(p: Path) -> int:
    with Image.open(p) as im:
        return min(im.size)

def short_side_gif(p: Path) -> int:
    with Image.open(p) as im:
        sides = []
        for i in range(im.n_frames):
            im.seek(i)
            sides.append(min(im.size))
        return min(sides)

def short_side_video(p: Path) -> int:
    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        return 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return min(w, h)

# ================= IMAGE CONVERT =================

def convert_image(src: Path, dst: Path):
    im = Image.open(src)
    im = im.convert("RGBA") if im.mode != "RGBA" else im
    im = resize_keep_aspect(im)
    im.save(dst, "PNG")
    im.close()

def convert_gif(src: Path, dst: Path):
    im = Image.open(src)
    frames, durations = [], []

    for i in range(im.n_frames):
        im.seek(i)
        f = im.convert("RGBA")
        f = resize_keep_aspect(f)
        frames.append(f)
        durations.append(im.info.get("duration", 100))

    frames[0].save(
        dst,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=im.info.get("loop", 0),
        disposal=2
    )

    im.close()
    for f in frames:
        f.close()

# ================= VIDEO =================

def get_video_info(path: Path):
    probe = ffmpeg.probe(str(path))
    dur = float(probe["format"]["duration"])
    for s in probe["streams"]:
        if s["codec_type"] == "video":
            return dur, int(s["width"]), int(s["height"])
    return 0, 0, 0

def encode_video(src: Path, dst: Path):
    dur, w, h = get_video_info(src)
    short = min(w, h)

    vf = None
    crf = 23

    if short > TARGET_SHORT_SIDE:
        scale = TARGET_SHORT_SIDE / short
        nw = int((w * scale + 1) // 2 * 2)
        nh = int((h * scale + 1) // 2 * 2)
        vf = f"scale={nw}:{nh}"
        crf = 20

    stream = ffmpeg.input(str(src))
    stream = ffmpeg.output(
        stream,
        str(dst),
        vcodec="libx264",
        crf=crf,
        preset="fast",
        acodec="aac",
        audio_bitrate="192k",
        vf=vf if vf else None,
        movflags="+faststart"
    ).global_args(
        "-progress", "pipe:1",
        "-nostats",
        "-hide_banner"
    )

    process = subprocess.Popen(
        stream.compile(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    cur = 0
    for line in process.stdout:
        line = line.strip()
        if line.startswith("out_time_ms="):
            t = float(line.split("=")[1]) / 1_000_000
            cur = min(t / dur, 1.0)
            bar = int(cur * 30)
            print(f"\r[{('='*bar).ljust(30)}] {int(cur*100):3d}%", end="")

        if line == "progress=end":
            break

    process.wait()
    print()

# ================= SCAN =================

def scan(root: Path) -> Dict[Path, List[Path]]:
    result = {}
    for dp, _, files in os.walk(root):
        p = Path(dp)
        fl = sorted(
            [p / f for f in files if (p / f).suffix.lower() in IMAGE_FORMATS | VIDEO_FORMATS],
            key=alphanum_key
        )
        if fl:
            result[p] = fl
    return result

# ================= MAIN =================

def process(root: Path):
    groups = scan(root)
    conv = skip = err = 0

    for folder, files in groups.items():
        print(f"\n[{folder}]")
        counter = {}

        for f in files:
            try:
                ext = f.suffix.lower()

                if ext == ".gif":
                    short, tgt = short_side_gif(f), ".gif"
                elif ext in IMAGE_FORMATS:
                    short, tgt = short_side_image(f), ".png"
                else:
                    short, tgt = short_side_video(f), ".mp4"

                counter.setdefault(tgt, 1)
                out = folder / f"{counter[tgt]}{tgt}"

                if ext == tgt and short <= TARGET_SHORT_SIDE:
                    if f.name != out.name:
                        shutil.move(f, out)
                        print(f"[REN] {f.name} → {out.name}")
                        conv += 1
                    else:
                        skip += 1
                    counter[tgt] += 1
                    continue

                tmp = folder / f"__tmp{tgt}"

                if tgt == ".png":
                    convert_image(f, tmp)
                elif tgt == ".gif":
                    convert_gif(f, tmp)
                else:
                    encode_video(f, tmp)

                f.unlink()
                shutil.move(tmp, out)
                print(f"[CON] {f.name} → {out.name}")
                counter[tgt] += 1
                conv += 1

            except Exception as e:
                print(f"[ERR] {f.name}: {e}")
                err += 1

    print("\n" + "="*50)
    print(f"CONVERT : {conv}")
    print(f"SKIP    : {skip}")
    print(f"ERROR   : {err}")
    print("="*50)

if __name__ == "__main__":
    process(Path(os.getcwd()))
