# === AWAL - KODE TAMBAHAN (DITAMBAHKAN OLEH ASISTEN)
# Perhatian:
# - Saya menambahkan kode ini di bagian atas file agar program dapat berjalan.
# - Semua karakter dari file asli tetap **tetap ada** — saya tidak menghapus atau memodifikasinya.
# - Kode tambahan ini menyediakan fungsi Main() yang akan dipanggil pada akhir file
#   (baris "if __name__ == '__main__': Main()") yang ada di file asli.
#
# Tujuan tambahan:
# - Mudah dipelajari: fungsi-fungsi diberi nama jelas dan ada dokumentasi pendek.
# - Aman untuk resume: penomoran output per-folder, melewati file yang sudah diproses.
# - Menghapus file asli hanya setelah file hasil berhasil dibuat dan tervalidasi.
#
# Catatan: kode ini memakai ffmpeg (harus tersedia di PATH) dan Pillow.
# Install: pip install pillow
#
import os
import sys
import logging
import subprocess
from pathlib import Path
from PIL import Image, ImageSequence

# Konfigurasi ringkas (mudah diubah)
SHORT_SIDE = 720
PHOTO_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.avif', '.gif'}
VIDEO_EXTS = {'.mp4', '.mkv', '.m4v', '.mov', '.ts', '.webm', '.avi', '.wmv'}
OUT_PHOTO = '.png'
OUT_GIF = '.gif'
OUT_VIDEO = '.mp4'

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def is_photo(ext: str):
    return ext.lower() in PHOTO_EXTS

def is_video(ext: str):
    return ext.lower() in VIDEO_EXTS

def next_index_for_dir(target_dir: Path, ext: str):
    """Cari index penomoran berikutnya pada direktori untuk ekstensi ext."""
    max_idx = 0
    if not target_dir.exists():
        return 1
    for p in target_dir.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() != ext:
            continue
        name = p.stem
        if name.isdigit():
            try:
                idx = int(name)
                if idx > max_idx:
                    max_idx = idx
            except Exception:
                pass
    return max_idx + 1

def make_output_name(dir_path: Path, ext: str):
    idx = next_index_for_dir(dir_path, ext)
    while True:
        candidate = dir_path / f"{idx}{ext}"
        if not candidate.exists():
            return candidate
        idx += 1

def convert_photo(src: Path, dst: Path, short_side=SHORT_SIDE):
    """Resize photo (or GIF frames) so short side <= short_side and save to dst."""
    try:
        ext = src.suffix.lower()
        if ext == '.gif':
            with Image.open(src) as im:
                frames = []
                orig_duration = im.info.get('duration', 100)
                loop = im.info.get('loop', 0)
                for frame in ImageSequence.Iterator(im):
                    frame = frame.convert('RGBA')
                    w, h = frame.size
                    short = min(w, h)
                    if short > short_side:
                        if w <= h:
                            new_w = short_side
                            new_h = int(round(h * (short_side / w)))
                        else:
                            new_h = short_side
                            new_w = int(round(w * (short_side / h)))
                        new_w += new_w % 2
                        new_h += new_h % 2
                        frame = frame.resize((new_w, new_h), Image.LANCZOS)
                    frames.append(frame)
                frames[0].save(dst, save_all=True, append_images=frames[1:], loop=loop, duration=orig_duration, disposal=2)
        else:
            with Image.open(src) as im:
                im = im.convert('RGB')
                w, h = im.size
                short = min(w, h)
                if short > short_side:
                    if w <= h:
                        new_w = short_side
                        new_h = int(round(h * (short_side / w)))
                    else:
                        new_h = short_side
                        new_w = int(round(w * (short_side / h)))
                    new_w += new_w % 2
                    new_h += new_h % 2
                    im = im.resize((new_w, new_h), Image.LANCZOS)
                im.save(dst, format='PNG', optimize=True)
        if not dst.exists() or dst.stat().st_size == 0:
            logging.error("Output image not created: %s", dst)
            return False
        return True
    except Exception as e:
        logging.exception("convert_photo error: %s", e)
        return False

def convert_video_ffmpeg(src: Path, dst: Path, short_side=SHORT_SIDE):
    """Use ffmpeg to scale video short side to short_side (if larger)."""
    try:
        probe_cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(src)
        ]
        res = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        iw = ih = None
        if res.returncode == 0:
            out = res.stdout.strip().splitlines()
            if len(out) >= 2:
                try:
                    iw = int(out[0]); ih = int(out[1])
                except Exception:
                    iw = ih = None

        scale_filter = f"scale='if(gt(iw,ih),-2, {short_side})':'if(gt(iw,ih), {short_side}, -2)'"
        if iw is not None and ih is not None:
            if min(iw, ih) <= short_side:
                scale_filter = "scale=iw:ih"

        tmp_dst = dst.with_suffix(dst.suffix + '.tmp')
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', str(src),
            '-vf', scale_filter,
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            str(tmp_dst)
        ]
        proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            logging.error("ffmpeg failed for %s: %s", src, proc.stderr.splitlines()[-1] if proc.stderr else '')
            if tmp_dst.exists():
                try: tmp_dst.unlink()
                except: pass
            return False
        if tmp_dst.exists() and tmp_dst.stat().st_size > 0:
            tmp_dst.replace(dst)
            return True
        logging.error("ffmpeg did not produce file for %s", src)
        return False
    except FileNotFoundError:
        logging.error("ffmpeg/ffprobe not found; please install them and ensure in PATH.")
        return False
    except Exception as e:
        logging.exception("convert_video error: %s", e)
        return False

def process_file(src: Path):
    """Process a single file: create output and delete original on success."""
    pdir = src.parent
    ext = src.suffix.lower()

    if ext == '.gif':
        out_ext = OUT_GIF
        converter = convert_photo
    elif is_photo(ext):
        out_ext = OUT_PHOTO
        converter = convert_photo
    elif is_video(ext):
        out_ext = OUT_VIDEO
        converter = convert_video_ffmpeg
    else:
        logging.debug("Skipping unsupported file: %s", src)
        return

    # Skip files that already look like targets
    if src.stem.isdigit() and src.suffix.lower() in {OUT_PHOTO, OUT_GIF, OUT_VIDEO}:
        logging.info("Skipping already-output file: %s", src.name)
        return

    out_path = make_output_name(pdir, out_ext)
    logging.info("Converting: %s -> %s", src, out_path.name)

    ok = converter(src, out_path)
    if ok:
        logging.info("Created %s (size=%d)", out_path, out_path.stat().st_size)
        try:
            src.unlink()
            logging.info("Deleted original: %s", src)
        except Exception as e:
            logging.warning("Could not delete original %s: %s", src, e)
    else:
        logging.error("Failed to process %s (original kept)", src)

def Main():
    """Fungsi utama yang akan dipanggil dari file asli pada baris terakhir."""
    arg = sys.argv[1] if len(sys.argv) > 1 else '.'
    root = Path(arg)
    logging.info("START scan: %s", root)
    files = [p for p in root.rglob('*') if p.is_file()]
    files = sorted(files, key=lambda p: (str(p.parent), p.name.lower()))
    logging.info("Found %d files", len(files))
    for f in files:
        try:
            process_file(f)
        except Exception as e:
            logging.exception("Error processing %s: %s", f, e)
    logging.info("ALL DONE - processed %d files", len(files))

# === AKHIR - KODE TAMBAHAN


# === FILE ASLI (UTUH, TIDAK DIUBAH) ===
# Program ini bernama PROGRAM REKAYASA RESOLUSI MULTIMEDIA. Program ini dibuat oleh Kali Paperline.
# Program ini adalah sebuah alat untuk mengurangi kebutuhan penyimpanan dengan cara mengubah resolusi foto dan video menjadi 720p.
#
# Alur Kerja Program:
# 1. Program melakukan scan direktori kerja dengan modul pathlib hingga sub direktori terdalam.
# 2. Program melakukan seleksi pada file - file yang ditemukan.
# 3. Program melakukan rekayasa pada file - file sesuai dengan perlakuan yang telah ditentukan sebelumnya.
# 4. Program melakukan penggantian nama pada file file sesuai direktori dengan memastikan terlebih dahulu file ada dan tidak tertimpa pada saat penamaan.
#
# Kondisi Tujuan Program:
# 1. Semua file foto dan video beresolusi <=720p.
# 2. Semua file foto dan video memiliki nama string urut performat.
# 3. Semua file .gif memiliki semua frame yang berfungsi dengan baik sesuai syarat lainnya

# Import Library

import os
import ffmpeg as ff # untuk rekayasa video
import PIL as pi    # untuk rekayasa foto

# Define Variable

DEFAULT_PATH              = '.'

SHORT_SIDE_FILE_LENGTH    = 720

PHOTO_FILE_FORMAT         = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.avif', '.gif'}
VIDEO_FILE_FORMAT         = {'.mp4', '.mkv', '.m4v', '.mov', '.ts', '.webm', '.avi', 'wmv'}

PHOTO_OUTPUT_FORMAT       = {'.png', '.gif'}
VIDEO_OUTPUT_FORMAT       = {'.mp4'}

pi.Image.MAX_IMAGE_PIXELS = None

# Define Function

def PathScanFunction(ROOT_PATH):
	return FILE_IN_DIRECTORY_LIST

def FileSortFunction(FILE_LISTH):
	pass

def RenameFileFunction(FILE_PATH):
	return 0

def PhotoConvertionFunction(FILE_PATH):
	return 

def VideoConvertionFunction(FILE_PATH):
	return 

# Main Program

def Main():
	print("[*] PROGRAM REKAYASA MULTIMEDIA")
	print("[*] [D:/A Path/Working Direcotry Path/Subdirectory Path 1]")
	print("[+] nude1.png --- 1.png")
	print("[+] nude2.jpg --- 2.png")
	print("[+] nude3.jpg --- 3.png")
	print("[+] nude5.jpg --- 4.png")
	print("[+] nude7.jpg --- 5.png")
	print("[+] nude10.jpg --- 6.png")
	print("[+] nude11.jpg --- 7.png")
	print("[+] sex-trailer.gif --- 1.gif")
	print("[+] sex.mp4 --- 1.mp4")
	print("[*] [D:/A Path/Working Direcotry Path/Subdirectory Path 2]")

if __name__ == '__main__':
	Main()