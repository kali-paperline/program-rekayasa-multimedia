#!/usr/bin/env python3
"""
MEDIA NORMALIZER - EASY VERSION

Fungsi:
- Scan folder secara recursive
- Foto -> PNG
- GIF animasi -> GIF
- Video -> MP4 (720p short side)
- Rename otomatis
- Progress bar untuk video
"""

# =====================================================
# 1. IMPORT
# =====================================================

import os
import re
import shutil
import subprocess
from pathlib import Path

import cv2
import ffmpeg
from PIL import Image


# =====================================================
# 2. KONFIGURASI GLOBAL
# =====================================================

TARGET_SHORT_SIDE = 720

Image.MAX_IMAGE_PIXELS = None  # disable limit

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".gif"}
VIDEO_EXT = {".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv", ".webm", ".ts"}

FINAL_IMAGE = {".png", ".gif"}
FINAL_VIDEO = {".mp4"}


# =====================================================
# 3. UTIL UMUM
# =====================================================

def natural_sort(path: Path):
    """Sort file: 1,2,10 (bukan 1,10,2)"""
    return [
        int(x) if x.isdigit() else x.lower()
        for x in re.split(r"(\d+)", path.stem)
    ]


def make_even_size(img: Image.Image) -> Image.Image:
    """Pastikan width & height genap"""
    w, h = img.size
    nw = w if w % 2 == 0 else w + 1
    nh = h if h % 2 == 0 else h + 1

    if (nw, nh) == (w, h):
        return img

    canvas = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
    canvas.paste(img, (0, 0))
    img.close()
    return canvas


def resize_image(img: Image.Image) -> Image.Image:
    """Resize image jika short side > 720"""
    w, h = img.size
    short = min(w, h)

    if short <= TARGET_SHORT_SIDE:
        return make_even_size(img)

    scale = TARGET_SHORT_SIDE / short
    new_w = round(w * scale)
    new_h = round(h * scale)

    img = img.resize((new_w, new_h), Image.LANCZOS)
    return make_even_size(img)


# =====================================================
# 4. CEK SHORT SIDE
# =====================================================

def image_short_side(path: Path) -> int:
    with Image.open(path) as im:
        return min(im.size)


def gif_short_side(path: Path) -> int:
    with Image.open(path) as im:
        sides = []
        for i in range(im.n_frames):
            im.seek(i)
            sides.append(min(im.size))
        return min(sides)


def video_short_side(path: Path) -> int:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return min(w, h)


# =====================================================
# 5. IMAGE & GIF CONVERTER
# =====================================================

def convert_image_to_png(src: Path, dst: Path):
    im = Image.open(src)
    im = im.convert("RGBA")
    im = resize_image(im)
    im.save(dst, "PNG")
    im.close()


def convert_gif(src: Path, dst: Path):
    im = Image.open(src)

    frames = []
    durations = []

    for i in range(im.n_frames):
        im.seek(i)
        frame = im.convert("RGBA")
        frame = resize_image(frame)
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


# =====================================================
# 6. VIDEO ENCODER + PROGRESS
# =====================================================

def get_video_info(path: Path):
    """Ambil durasi, width, height"""
    probe = ffmpeg.probe(str(path))
    duration = float(probe["format"]["duration"])

    for s in probe["streams"]:
        if s["codec_type"] == "video":
            return duration, int(s["width"]), int(s["height"])

    return 0, 0, 0


def encode_video(src: Path, dst: Path):
    duration, w, h = get_video_info(src)
    short = min(w, h)

    scale_filter = None
    crf = 23

    if short > TARGET_SHORT_SIDE:
        ratio = TARGET_SHORT_SIDE / short
        new_w = int((w * ratio + 1) // 2 * 2)
        new_h = int((h * ratio + 1) // 2 * 2)
        scale_filter = f"scale={new_w}:{new_h}"
        crf = 20

    stream = (
        ffmpeg
        .input(str(src))
        .output(
            str(dst),
            vcodec="libx264",
            crf=crf,
            preset="fast",
            acodec="aac",
            audio_bitrate="192k",
            vf=scale_filter,
            movflags="+faststart"
        )
        .global_args(
            "-progress", "pipe:1",
            "-nostats",
            "-hide_banner"
        )
    )

    process = subprocess.Popen(
        stream.compile(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        if line.startswith("out_time_ms="):
            cur = float(line.split("=")[1]) / 1_000_000
            percent = min(cur / duration, 1.0)
            bar = int(percent * 30)
            print(f"\r[{('='*bar).ljust(30)}] {int(percent*100):3d}%", end="")

        if line.strip() == "progress=end":
            break

    process.wait()
    print()


# =====================================================
# 7. SCAN FOLDER
# =====================================================

def scan_recursive(root: Path):
    result = {}

    for dirpath, _, files in os.walk(root):
        folder = Path(dirpath)

        media = [
            folder / f for f in files
            if (folder / f).suffix.lower() in IMAGE_EXT | VIDEO_EXT
        ]

        if media:
            result[folder] = sorted(media, key=natural_sort)

    return result


# =====================================================
# 8. MAIN PROCESS
# =====================================================

def process_all(root: Path):
    folders = scan_recursive(root)

    converted = skipped = errors = 0

    for folder, files in folders.items():
        print(f"\n📂 {folder}")
        counter = {}

        for file in files:
            try:
                ext = file.suffix.lower()

                if ext == ".gif":
                    short = gif_short_side(file)
                    target_ext = ".gif"

                elif ext in IMAGE_EXT:
                    short = image_short_side(file)
                    target_ext = ".png"

                else:
                    short = video_short_side(file)
                    target_ext = ".mp4"

                counter.setdefault(target_ext, 1)
                output = folder / f"{counter[target_ext]}{target_ext}"

                # SKIP CONVERT (hanya rename)
                if ext == target_ext and short <= TARGET_SHORT_SIDE:
                    if file.name != output.name:
                        shutil.move(file, output)
                        print(f"[RENAME] {file.name} → {output.name}")
                        converted += 1
                    else:
                        skipped += 1

                    counter[target_ext] += 1
                    continue

                temp = folder / f"_temp{target_ext}"

                if target_ext == ".png":
                    convert_image_to_png(file, temp)
                elif target_ext == ".gif":
                    convert_gif(file, temp)
                else:
                    encode_video(file, temp)

                file.unlink()
                shutil.move(temp, output)
                print(f"[CONVERT] {file.name} → {output.name}")

                counter[target_ext] += 1
                converted += 1

            except Exception as e:
                print(f"[ERROR] {file.name} : {e}")
                errors += 1

    print("\n" + "="*50)
    print(f"CONVERTED : {converted}")
    print(f"SKIPPED   : {skipped}")
    print(f"ERRORS    : {errors}")
    print("="*50)


# =====================================================
# 9. ENTRY POINT
# =====================================================

if __name__ == "__main__":
    process_all(Path(os.getcwd()))
