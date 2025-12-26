#!/usr/bin/env python3
"""
con-res-7-fixed.py

FIX:
- GIF animasi tidak lagi collapse jadi 1 frame
- GIF diproses pakai Pillow (AMAN disposal & duration)
- Imageio TIDAK dipakai untuk GIF
- Resolusi output selalu genap
"""

import os
import shutil
import re
import subprocess
from pathlib import Path
from typing import List, Dict

from PIL import Image
import cv2

# ================== KONFIGURASI ==================

Image.MAX_IMAGE_PIXELS = None

TARGET_SHORT_SIDE = 720

IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.gif'}
VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.ts', '.m4v'}

ALLOWED_IMAGE_FORMATS = {'.png', '.gif'}
ALLOWED_VIDEO_FORMATS = {'.mp4'}

# ================== SORT NATURAL ==================

def alphanum_key(path: Path):
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r'(\d+)', path.stem)]

def sort_files_naturally(files: List[Path]) -> List[Path]:
    return sorted(files, key=alphanum_key)

# ================== IMAGE UTILS ==================

def force_even_size(img: Image.Image) -> Image.Image:
    w, h = img.size
    nw = w + (w % 2)
    nh = h + (h % 2)
    if (nw, nh) == (w, h):
        return img
    new = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
    new.paste(img, (0, 0))
    img.close()
    return new

def resize_keep_aspect(img: Image.Image, target: int) -> Image.Image:
    w, h = img.size
    short = min(w, h)
    if short <= target:
        return force_even_size(img)

    scale = target / short
    nw = round(w * scale)
    nh = round(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    return force_even_size(img)

# ================== SIZE CHECK ==================

def short_side_image(p: Path) -> int:
    with Image.open(p) as im:
        return min(im.size)

def short_side_gif(p: Path) -> int:
    with Image.open(p) as im:
        sides = []
        for i in range(im.n_frames):
            im.seek(i)
            sides.append(min(im.size))
        return min(sides) if sides else 0

def short_side_video(p: Path) -> int:
    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        cap.release()
        return 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return min(w, h)

# ================== CONVERTER ==================

def convert_image_to_png(src: Path, dst: Path):
    im = Image.open(src)
    im = im.convert("RGBA") if im.mode != "RGBA" else im
    im = resize_keep_aspect(im, TARGET_SHORT_SIDE)
    im.save(dst, "PNG")
    im.close()

def convert_gif(src: Path, dst: Path):
    im = Image.open(src)

    frames = []
    durations = []

    for i in range(im.n_frames):
        im.seek(i)
        frame = im.convert("RGBA")
        frame = resize_keep_aspect(frame, TARGET_SHORT_SIDE)
        frames.append(frame)
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

def convert_video(src: Path, dst: Path):
    cap = cv2.VideoCapture(str(src))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    short = min(w, h)
    if short > TARGET_SHORT_SIDE:
        vf = (
            f"scale='if(gt(iw,ih),-2,{TARGET_SHORT_SIDE})':"
            f"'if(gt(ih,iw),-2,{TARGET_SHORT_SIDE})',"
            "scale=ceil(iw/2)*2:ceil(ih/2)*2"
        )
    else:
        vf = "scale=ceil(iw/2)*2:ceil(ih/2)*2"

    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(dst)
    ]

    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode())

# ================== SCANNER ==================

def find_media(root: Path) -> Dict[Path, List[Path]]:
    result = {}
    for dp, _, fn in os.walk(root):
        p = Path(dp)
        files = sort_files_naturally(
            [p / f for f in fn if (p / f).suffix.lower() in IMAGE_FORMATS | VIDEO_FORMATS]
        )
        if files:
            result[p] = files
    return result

# ================== MAIN ==================

def process(root: Path):
    media_dirs = find_media(root)

    skp = con = err = 0

    for d, files in media_dirs.items():
        print(f"[{d}]")
        counter = {}

        for f in files:
            try:
                ext = f.suffix.lower()

                if ext == ".gif":
                    short = short_side_gif(f)
                    tgt = ".gif"
                elif ext in IMAGE_FORMATS:
                    short = short_side_image(f)
                    tgt = ".png"
                else:
                    short = short_side_video(f)
                    tgt = ".mp4"

                # valid & small
                if ext in ALLOWED_IMAGE_FORMATS | ALLOWED_VIDEO_FORMATS and short <= TARGET_SHORT_SIDE:
                    counter.setdefault(tgt, 1)
                    new = d / f"{counter[tgt]}{tgt}"
                    counter[tgt] += 1
                    if f.name != new.name:
                        shutil.move(f, new)
                        print(f"[CON] {f.name} -> {new.name}")
                        con += 1
                    else:
                        skp += 1
                    continue

                tmp = d / f"temp_{f.stem}{tgt}"

                if tgt == ".png":
                    convert_image_to_png(f, tmp)
                elif tgt == ".gif":
                    convert_gif(f, tmp)
                else:
                    convert_video(f, tmp)

                counter.setdefault(tgt, 1)
                final = d / f"{counter[tgt]}{tgt}"
                counter[tgt] += 1

                f.unlink(missing_ok=True)
                shutil.move(tmp, final)
                print(f"[CON] {f.name} -> {final.name}")
                con += 1

            except Exception as e:
                print(f"[ERR] {f.name}: {e}")
                err += 1

        print("")

    print("=" * 60)
    print(f"SKIP: {skp}")
    print(f"CONV: {con}")
    print(f"ERR : {err}")
    print("=" * 60)

# ================== ENTRY ==================

if __name__ == "__main__":
    process(Path(os.getcwd()))
