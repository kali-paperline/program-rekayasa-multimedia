# PROGRAM REKAYASA RESOLUSI MULTIMEDIA
# Versi: Tambahan "skip jika sudah sesuai" + tanpa lambda dan tanpa comprehensions rumit.
# Kegunaan:
#  - scan direktori (rekursif)
#  - pilih file foto/video sesuai ekstensi
#  - resize foto/video supaya short side <= 720
#  - skip bila file sudah memenuhi resolusi dan format output
#  - simpan foto (png untuk foto statis, gif untuk animated gif)
#  - simpan video (mp4)
#  - rename output berurutan dalam tiap folder (1.png, 2.png, 1.mp4, dst.)
#
# Persyaratan: ffmpeg terinstal dan dapat diakses via PATH untuk konversi video.
# Cara pakai:
#   python c.py /path/to/working/directory [--dry-run] [--no-skip]
# Contoh:
#   python c.py . --dry-run
#   python c.py /home/user/Videos --no-skip

import os
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageSequence
import ffmpeg

# ----------------------------
# Konstanta dan format file
# ----------------------------
DEFAULT_WORKING_DIRECTORY = Path('.')

SHORT_SIDE_TARGET = 720

PHOTO_INPUT_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.avif', '.gif'}
VIDEO_INPUT_EXTENSIONS = {'.mp4', '.mkv', '.m4v', '.mov', '.ts', '.webm', '.avi', '.wmv'}

PHOTO_OUTPUT_EXT_STATIC = '.png'
PHOTO_OUTPUT_EXT_GIF = '.gif'
VIDEO_OUTPUT_EXT = '.mp4'

Image.MAX_IMAGE_PIXELS = None  # disable decompression bomb protection (hati-hati)

# ----------------------------
# Helper sederhana
# ----------------------------

def make_even(number):
    """Pastikan bilangan bulat genap (beberapa encoder membutuhkan dimensi genap)."""
    integer = int(number)
    if integer % 2 == 1:
        return integer - 1
    return integer

def safe_print(message):
    """Print langsung flush agar realtime di console."""
    print(message, flush=True)

def is_photo_path(path_obj):
    return path_obj.suffix.lower() in PHOTO_INPUT_EXTENSIONS

def is_video_path(path_obj):
    return path_obj.suffix.lower() in VIDEO_INPUT_EXTENSIONS

# ----------------------------
# Scan direktori
# ----------------------------

def PathScanFunction(root_path):
    """
    Kembalikan list Path untuk semua file media yang ditemukan (rekursif).
    """
    if not isinstance(root_path, Path):
        root_path = Path(root_path)
    found_files = []
    iterator = root_path.rglob('*')
    for entry in iterator:
        if entry.is_file():
            suffix_lower = entry.suffix.lower()
            if suffix_lower in PHOTO_INPUT_EXTENSIONS or suffix_lower in VIDEO_INPUT_EXTENSIONS:
                found_files.append(entry)
    return found_files

# ----------------------------
# Sorting (tanpa lambda)
# ----------------------------

def FileSortFunction(file_list):
    """
    Urutkan list Path secara deterministik menurut string path (case-insensitive).
    Tidak menggunakan lambda atau comprehension.
    """
    pairs = []
    i = 0
    while i < len(file_list):
        p = file_list[i]
        pairs.append((str(p).lower(), p))
        i = i + 1
    pairs.sort()  # tuple akan di-sort berdasarkan elemen pertama (string path)
    sorted_list = []
    j = 0
    while j < len(pairs):
        sorted_list.append(pairs[j][1])
        j = j + 1
    return sorted_list

# ----------------------------
# Rename aman
# ----------------------------

def get_next_available_filename(directory, base_index, extension):
    """
    Cari nama yang tidak menimpa file lain: mulai dari base_index
    """
    index = int(base_index)
    while True:
        candidate = directory / (str(index) + extension)
        if not candidate.exists():
            return candidate, index
        index = index + 1

def RenameFileFunction(temp_created_file, target_directory, target_extension, start_index):
    """
    Pindahkan file sementara ke nama final berurut di folder. Kembalikan (final_path, used_index).
    """
    if not isinstance(target_directory, Path):
        target_directory = Path(target_directory)
    final_path, used_index = get_next_available_filename(target_directory, start_index, target_extension)
    shutil.move(str(temp_created_file), str(final_path))
    return final_path, used_index

# ----------------------------
# Photo conversion (dengan opsi skip)
# ----------------------------

def PhotoConvertionFunction(input_path, output_directory, start_photo_index, start_gif_index, dry_run=False, skip_if_ok=True):
    """
    Proses foto:
    - Jika animated GIF -> resize frame by frame lalu simpan GIF.
    - Jika foto statis -> simpan sebagai PNG.
    - Jika file sudah memiliki short side <= target dan format output sudah sesuai -> skip (jika skip_if_ok True).
    Return:
      - (final_path_or_marker, used_index_or_None, type_str)
      - jika skip: return ('skipped', None, 'skipped')
    """
    input_path = Path(input_path)
    output_directory = Path(output_directory)
    suffix = input_path.suffix.lower()

    try:
        image = Image.open(str(input_path))
    except Exception as e:
        safe_print(f"[!] Gagal membuka gambar: {input_path} -> {e}")
        return None, None, None

    width, height = image.size
    short_side = width if width < height else height

    if short_side <= SHORT_SIDE_TARGET:
        # kondisi short side sudah sesuai
        if suffix == '.gif':
            if skip_if_ok and suffix == PHOTO_OUTPUT_EXT_GIF:
                safe_print(f"[i] GIF sudah sesuai (resolusi & format). Skip: {input_path.name}")
                return 'skipped', None, 'skipped'
            # kalau bukan .gif output, kita tetap akan menyimpan ulang sebagai .gif
        else:
            if skip_if_ok and suffix == PHOTO_OUTPUT_EXT_STATIC:
                safe_print(f"[i] Foto statis sudah sesuai (resolusi & format). Skip: {input_path.name}")
                return 'skipped', None, 'skipped'
            # kalau bukan .png output, kita tetap akan menyimpan ulang sebagai .png

    # hitung ukuran target (jika perlu scale)
    if short_side <= SHORT_SIDE_TARGET:
        scale_ratio = 1.0
    else:
        scale_ratio = SHORT_SIDE_TARGET / float(short_side)

    new_width = make_even(round(width * scale_ratio))
    new_height = make_even(round(height * scale_ratio))

    # Proses GIF
    if suffix == '.gif':
        safe_print(f"[i] Memproses GIF: {input_path.name} -> ({new_width}x{new_height})")
        frames = []
        durations = []
        loop_value = 0
        try:
            for frame in ImageSequence.Iterator(image):
                frame_converted = frame.convert('RGBA')
                resized_frame = frame_converted.resize((new_width, new_height), Image.LANCZOS)
                frames.append(resized_frame)
                try:
                    durations.append(frame.info.get('duration', 100))
                except Exception:
                    durations.append(100)
            loop_value = image.info.get('loop', 0)
        except Exception as e:
            safe_print(f"[!] Gagal memproses frame GIF: {input_path} -> {e}")
            return None, None, None

        tmp_name = output_directory / (".tmp_converted_" + input_path.stem + PHOTO_OUTPUT_EXT_GIF)
        if dry_run:
            safe_print(f"[dry-run] akan menulis GIF ke: {tmp_name}")
            return tmp_name, start_gif_index, 'gif'

        try:
            first_frame = frames[0].convert('P', palette=Image.ADAPTIVE)
            additional_frames = []
            k = 1
            while k < len(frames):
                additional_frames.append(frames[k].convert('P', palette=Image.ADAPTIVE))
                k = k + 1
            first_frame.save(
                str(tmp_name),
                save_all=True,
                append_images=additional_frames,
                loop=loop_value,
                duration=durations,
                disposal=2,
                optimize=False
            )
        except Exception as e:
            safe_print(f"[!] Gagal menyimpan GIF: {tmp_name} -> {e}")
            try:
                if tmp_name.exists():
                    tmp_name.unlink()
            except Exception:
                pass
            return None, None, None

        final_path, used_index = RenameFileFunction(tmp_name, output_directory, PHOTO_OUTPUT_EXT_GIF, start_gif_index)
        safe_print(f"[+] GIF disimpan sebagai: {final_path.name}")
        return final_path, used_index, 'gif'

    # Proses foto statis (non-gif)
    safe_print(f"[i] Memproses foto statis: {input_path.name} -> ({new_width}x{new_height})")
    tmp_name = output_directory / (".tmp_converted_" + input_path.stem + PHOTO_OUTPUT_EXT_STATIC)
    if dry_run:
        safe_print(f"[dry-run] akan menulis foto PNG ke: {tmp_name}")
        return tmp_name, start_photo_index, 'photo'

    try:
        converted = image.convert('RGB')
        resized = converted.resize((new_width, new_height), Image.LANCZOS)
        resized.save(str(tmp_name), format='PNG', optimize=True)
    except Exception as e:
        safe_print(f"[!] Gagal menyimpan foto PNG: {tmp_name} -> {e}")
        try:
            if tmp_name.exists():
                tmp_name.unlink()
        except Exception:
            pass
        return None, None, None

    final_path, used_index = RenameFileFunction(tmp_name, output_directory, PHOTO_OUTPUT_EXT_STATIC, start_photo_index)
    safe_print(f"[+] Foto disimpan sebagai: {final_path.name}")
    return final_path, used_index, 'photo'

# ----------------------------
# Video conversion (dengan opsi skip)
# ----------------------------

def probe_video_resolution(file_path):
    """Kembalikan (width, height) atau (None, None) jika gagal."""
    try:
        probe = ffmpeg.probe(str(file_path))
        streams = probe.get('streams', [])
        video_stream = None
        i = 0
        while i < len(streams):
            if streams[i].get('codec_type') == 'video':
                video_stream = streams[i]
                break
            i = i + 1
        if video_stream is None:
            return None, None
        width = int(video_stream.get('width'))
        height = int(video_stream.get('height'))
        return width, height
    except ffmpeg.Error as e:
        safe_print(f"[!] ffprobe error untuk {file_path}: {e}")
        return None, None
    except Exception as e:
        safe_print(f"[!] Gagal probing video {file_path}: {e}")
        return None, None

def VideoConvertionFunction(input_path, output_directory, start_video_index, dry_run=False, skip_if_ok=True):
    """
    Ubah resolusi video sehingga short side <= SHORT_SIDE_TARGET dan simpan sebagai MP4.
    Jika short side <= target dan ekstensi .mp4 dan skip_if_ok True -> skip.
    Return (final_path_or_marker, used_index_or_None).
    """
    input_path = Path(input_path)
    output_directory = Path(output_directory)

    width, height = probe_video_resolution(input_path)
    if width is None or height is None:
        safe_print(f"[!] Tidak dapat menentukan resolusi video: {input_path}. Lewati.")
        return None, None

    short_side = width if width < height else height

    if short_side <= SHORT_SIDE_TARGET and skip_if_ok:
        if input_path.suffix.lower() == VIDEO_OUTPUT_EXT:
            safe_print(f"[i] Video sudah sesuai (resolusi & format). Skip: {input_path.name}")
            return 'skipped', None

    # Hitung target dimension
    if short_side <= SHORT_SIDE_TARGET:
        target_width = make_even(width)
        target_height = make_even(height)
    else:
        scale_ratio = SHORT_SIDE_TARGET / float(short_side)
        target_width = make_even(round(width * scale_ratio))
        target_height = make_even(round(height * scale_ratio))

    safe_print(f"[i] Proses video: {input_path.name} -> ({target_width}x{target_height})")

    tmp_name = output_directory / (".tmp_converted_" + input_path.stem + VIDEO_OUTPUT_EXT)
    if dry_run:
        safe_print(f"[dry-run] akan menulis video mp4 ke: {tmp_name}")
        return tmp_name, start_video_index

    try:
        input_stream = ffmpeg.input(str(input_path))
        video_stream = input_stream.video.filter('scale', target_width, target_height)
        audio_stream = input_stream.audio

        output_kwargs = {
            'vcodec': 'libx264',
            'preset': 'medium',
            'crf': '23',
            'acodec': 'aac',
            'movflags': '+faststart'
        }

        if audio_stream is None:
            ffmpeg_output = ffmpeg.output(video_stream, str(tmp_name), **output_kwargs)
        else:
            ffmpeg_output = ffmpeg.output(video_stream, audio_stream, str(tmp_name), **output_kwargs)

        ffmpeg_output = ffmpeg_output.overwrite_output()
        ffmpeg_output.run(quiet=False)
    except ffmpeg.Error as e:
        safe_print(f"[!] ffmpeg gagal untuk {input_path} -> {e}")
        try:
            if tmp_name.exists():
                tmp_name.unlink()
        except Exception:
            pass
        return None, None
    except Exception as e:
        safe_print(f"[!] Kesalahan saat memproses video {input_path} -> {e}")
        try:
            if tmp_name.exists():
                tmp_name.unlink()
        except Exception:
            pass
        return None, None

    final_path, used_index = RenameFileFunction(tmp_name, output_directory, VIDEO_OUTPUT_EXT, start_video_index)
    safe_print(f"[+] Video disimpan sebagai: {final_path.name}")
    return final_path, used_index

# ----------------------------
# Main workflow
# ----------------------------

def process_directory(root_directory, dry_run=False, skip_if_ok=True):
    """
    Proses semua file dalam root_directory (rekursif).
    Untuk tiap folder: counters terpisah untuk foto (.png), gif (.gif), video (.mp4).
    File yang 'skipped' tidak akan diubah atau di-rename.
    """
    root_directory = Path(root_directory)
    safe_print(f"[*] Memindai: {root_directory}")

    found_files = PathScanFunction(root_directory)
    sorted_files = FileSortFunction(found_files)

    # group per folder
    folder_map = {}
    idx = 0
    while idx < len(sorted_files):
        p = sorted_files[idx]
        folder = p.parent
        if folder not in folder_map:
            folder_map[folder] = []
        folder_map[folder].append(p)
        idx = idx + 1

    # proses tiap folder
    for folder in folder_map:
        safe_print(f"[>] Memproses folder: {folder}")
        photo_index = 1
        gif_index = 1
        video_index = 1

        if not folder.exists():
            safe_print(f"[!] Folder tidak ditemukan: {folder} (lewati)")
            continue

        files_in_folder = folder_map[folder]
        i = 0
        while i < len(files_in_folder):
            file_path = files_in_folder[i]
            try:
                if is_photo_path(file_path):
                    result_path, used_index, type_str = PhotoConvertionFunction(
                        file_path, folder, photo_index, gif_index, dry_run=dry_run, skip_if_ok=skip_if_ok
                    )
                    if result_path is None:
                        safe_print(f"[!] Gagal memproses foto: {file_path.name}")
                    elif result_path == 'skipped':
                        # tidak increment counter, karena tidak menghasilkan file baru
                        pass
                    else:
                        if type_str == 'photo':
                            photo_index = used_index + 1
                        elif type_str == 'gif':
                            gif_index = used_index + 1

                elif is_video_path(file_path):
                    result_path, used_index = VideoConvertionFunction(
                        file_path, folder, video_index, dry_run=dry_run, skip_if_ok=skip_if_ok
                    )
                    if result_path is None:
                        safe_print(f"[!] Gagal memproses video: {file_path.name}")
                    elif result_path == 'skipped':
                        pass
                    else:
                        video_index = used_index + 1
                else:
                    safe_print(f"[!] Type file tidak dikenal: {file_path}")
            except Exception as e:
                safe_print(f"[!] Exception saat memproses {file_path}: {e}")
            i = i + 1

    safe_print("[*] Selesai memproses semua folder.")

def Main():
    safe_print("[*] PROGRAM REKAYASA MULTIMEDIA - Versi dengan Skip")
    work_path = DEFAULT_WORKING_DIRECTORY
    dry_run_flag = False
    skip_flag = True  # default: skip file yang sudah sesuai

    # parsing arg sederhana
    if len(sys.argv) >= 2:
        arg1 = sys.argv[1]
        if arg1 in ('--dry-run', '-n'):
            dry_run_flag = True
        elif arg1 == '--no-skip':
            skip_flag = False
        else:
            work_path = Path(arg1)

    if len(sys.argv) >= 3:
        arg2 = sys.argv[2]
        if arg2 in ('--dry-run', '-n'):
            dry_run_flag = True
        elif arg2 == '--no-skip':
            skip_flag = False

    safe_print(f"[*] Working directory: {work_path.resolve()}")
    if dry_run_flag:
        safe_print("[*] Mode: DRY RUN (tidak menulis file, hanya simulasi)")
    if not skip_flag:
        safe_print("[*] Skip disabled: program akan memproses/menulis ulang file walau resolusi sudah <= target")

    try:
        process_directory(work_path, dry_run=dry_run_flag, skip_if_ok=skip_flag)
    except Exception as e:
        safe_print(f"[!] Error di Main: {e}")

if __name__ == '__main__':
    Main()
