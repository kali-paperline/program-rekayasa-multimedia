# PROGRAM REKAYASA RESOLUSI MULTIMEDIA
# Versi lengkap, mudah dibaca, tanpa lambda dan tanpa comprehensions rumit.
# Fungsi:
#  - scan direktori (rekursif)
#  - pilih file foto/video sesuai ekstensi
#  - resize foto/video supaya short side <= 720
#  - simpan foto (png untuk gambar statis, gif untuk animated gif)
#  - simpan video (mp4)
#  - rename output berurutan dalam tiap folder (1.png, 2.png, 1.mp4, dst.)
#
# Ketentuan: butuh ffmpeg binary terinstal agar konversi video berjalan.
# Usage:
#   python c.py /path/to/working/directory
# atau tinggal jalankan tanpa argumen (akan pakai direktori saat ini)

import os
import shutil
import sys
from pathlib import Path

# PIL untuk gambar
from PIL import Image, ImageSequence

# ffmpeg-python untuk video (perlu ffmpeg di PATH)
import ffmpeg

# ----------------------------
# Konstanta dan format file
# ----------------------------
DEFAULT_WORKING_DIRECTORY = Path('.')

# panjang sisi pendek maksimal (720p short side)
SHORT_SIDE_TARGET = 720

# Format input file (ekstensi dalam huruf kecil)
PHOTO_INPUT_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.avif', '.gif'}
VIDEO_INPUT_EXTENSIONS = {'.mp4', '.mkv', '.m4v', '.mov', '.ts', '.webm', '.avi', '.wmv'}

# Output format preferensi (ext termasuk titik)
PHOTO_OUTPUT_EXT_STATIC = '.png'   # untuk foto statis
PHOTO_OUTPUT_EXT_GIF = '.gif'      # untuk animated gif
VIDEO_OUTPUT_EXT = '.mp4'          # video akan disimpan sebagai mp4

# Hentikan batas proteksi decompression bomb (PIL)
Image.MAX_IMAGE_PIXELS = None

# ----------------------------
# Utility sederhana
# ----------------------------

def make_even(number):
    """Pastikan bilangan bulat genap (ffmpeg kadang butuh dimensi genap)."""
    integer = int(number)
    if integer % 2 == 1:
        return integer - 1
    return integer

def safe_print(message):
    """Wrapper print sederhana."""
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
    Kembalikan list Path untuk semua file media (foto/video) yang ditemukan
    di root_path dan subfolder-nya.
    """
    if not isinstance(root_path, Path):
        root_path = Path(root_path)
    found_files = []
    # gunakeun rglob untuk rekursif
    for entry in root_path.rglob('*'):
        if entry.is_file():
            suffix_lower = entry.suffix.lower()
            if suffix_lower in PHOTO_INPUT_EXTENSIONS or suffix_lower in VIDEO_INPUT_EXTENSIONS:
                found_files.append(entry)
    return found_files

# ----------------------------
# Sorting (urutkan berdasarkan nama)
# ----------------------------

def FileSortFunction(file_list):
    """
    Urutkan list Path berdasarkan path string (deterministik).
    Tidak menggunakan list comprehension.
    """
    # buat salinan list agar tidak merubah input
    sorted_list = list(file_list)
    sorted_list.sort(key=lambda p: str(p).lower())
    return sorted_list

# ----------------------------
# Rename/penamaan aman
# ----------------------------

def get_next_available_filename(directory, base_index, extension):
    """
    Cari nama yang tidak menimpa file lain:
    mulai dari base_index, kembalikan Path(directory / f"{index}{extension}")
    """
    index = int(base_index)
    while True:
        candidate = directory / (str(index) + extension)
        if not candidate.exists():
            return candidate, index
        index = index + 1

def RenameFileFunction(temp_created_file, target_directory, target_extension, start_index):
    """
    Pindahkan/rename temporary file ke nama akhir yang aman berupa angka berurut.
    Mengembalikan Path target final dan index yang dipakai.
    """
    if not isinstance(target_directory, Path):
        target_directory = Path(target_directory)
    # cari nama bebas
    final_path, used_index = get_next_available_filename(target_directory, start_index, target_extension)
    # pindahkan
    shutil.move(str(temp_created_file), str(final_path))
    return final_path, used_index

# ----------------------------
# Photo conversion (PIL)
# ----------------------------

def PhotoConvertionFunction(input_path, output_directory, start_photo_index, start_gif_index, dry_run=False):
    """
    Proses foto:
      - jika GIF (animated) -> proses frame by frame dan simpan gif dengan ukuran short side <= 720
      - jika foto statis -> resize short side <=720 dan simpan sebagai PNG
    Mengembalikan tuple (new_path, used_index, type_str)
      type_str = 'photo' atau 'gif'
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

    # jika short side sudah <= target, kita tetap menyimpan ulang dalam format tujuan
    if short_side <= SHORT_SIDE_TARGET:
        scale_ratio = 1.0
    else:
        scale_ratio = SHORT_SIDE_TARGET / float(short_side)

    new_width = make_even(round(width * scale_ratio))
    new_height = make_even(round(height * scale_ratio))

    if suffix == '.gif':
        # Animated GIF: iterasi frame, ubah ukuran tiap frame, simpan dengan save_all
        safe_print(f"[i] Memproses GIF: {input_path} -> short side {short_side} -> ({new_width}x{new_height})")
        frames = []
        durations = []
        loop_value = 0
        try:
            for frame in ImageSequence.Iterator(image):
                frame_converted = frame.convert('RGBA')
                resized_frame = frame_converted.resize((new_width, new_height), Image.LANCZOS)
                frames.append(resized_frame)
                try:
                    # durasi per frame jika ada
                    durations.append(frame.info.get('duration', 100))
                except Exception:
                    durations.append(100)
            loop_value = image.info.get('loop', 0)
        except Exception as e:
            safe_print(f"[!] Gagal memproses frame GIF: {input_path} -> {e}")
            return None, None, None

        # Buat temporary file di folder tujuan
        tmp_name = output_directory / (".tmp_converted_" + input_path.stem + PHOTO_OUTPUT_EXT_GIF)
        if dry_run:
            safe_print(f"[dry-run] akan menulis GIF ke: {tmp_name}")
            return tmp_name, start_gif_index, 'gif'

        try:
            # simpan semua frame
            first_frame = frames[0].convert('P', palette=Image.ADAPTIVE)
            additional_frames = []
            i = 1
            while i < len(frames):
                additional_frames.append(frames[i].convert('P', palette=Image.ADAPTIVE))
                i = i + 1
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
            # hapus tmp bila ada
            try:
                if tmp_name.exists():
                    tmp_name.unlink()
            except Exception:
                pass
            return None, None, None

        # rename ke nama akhir (urut)
        final_path, used_index = RenameFileFunction(tmp_name, output_directory, PHOTO_OUTPUT_EXT_GIF, start_gif_index)
        safe_print(f"[+] GIF disimpan sebagai: {final_path.name}")
        return final_path, used_index, 'gif'

    else:
        # Gambar statis
        safe_print(f"[i] Memproses foto statis: {input_path} -> short side {short_side} -> ({new_width}x{new_height})")
        tmp_name = output_directory / (".tmp_converted_" + input_path.stem + PHOTO_OUTPUT_EXT_STATIC)
        if dry_run:
            safe_print(f"[dry-run] akan menulis foto PNG ke: {tmp_name}")
            return tmp_name, start_photo_index, 'photo'

        try:
            converted = image.convert('RGB')
            resized = converted.resize((new_width, new_height), Image.LANCZOS)
            # simpan PNG
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
# Video conversion (ffmpeg-python)
# ----------------------------

def probe_video_resolution(file_path):
    """Mengembalikan tuple (width, height) atau (None, None) jika gagal."""
    try:
        probe = ffmpeg.probe(str(file_path))
        # cari stream video pertama
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

def VideoConvertionFunction(input_path, output_directory, start_video_index, dry_run=False):
    """
    Ubah resolusi video sehingga short side <= SHORT_SIDE_TARGET dan simpan sebagai MP4.
    Return (final_path, used_index).
    """
    input_path = Path(input_path)
    output_directory = Path(output_directory)

    width, height = probe_video_resolution(input_path)
    if width is None or height is None:
        safe_print(f"[!] Tidak dapat menentukan resolusi video: {input_path}. Lewati.")
        return None, None

    short_side = width if width < height else height

    if short_side <= SHORT_SIDE_TARGET:
        safe_print(f"[i] Video sudah short side <= {SHORT_SIDE_TARGET}: {input_path} ({width}x{height})")
        # kita tetap re-mux/convert untuk memastikan format mp4 (optional).
        target_width = make_even(width)
        target_height = make_even(height)
    else:
        scale_ratio = SHORT_SIDE_TARGET / float(short_side)
        target_width = make_even(round(width * scale_ratio))
        target_height = make_even(round(height * scale_ratio))

    safe_print(f"[i] Proses video: {input_path} -> ({target_width}x{target_height})")

    tmp_name = output_directory / (".tmp_converted_" + input_path.stem + VIDEO_OUTPUT_EXT)
    if dry_run:
        safe_print(f"[dry-run] akan menulis video mp4 ke: {tmp_name}")
        return tmp_name, start_video_index

    try:
        # input stream
        input_stream = ffmpeg.input(str(input_path))
        # scale filter, tetap menjaga aspect ratio karena kita hitung ukuran target sendiri
        video_stream = input_stream.video.filter('scale', target_width, target_height)
        # audio stream (jika ada) - biarkan ffmpeg menangani audio (copy bila compat)
        audio_stream = input_stream.audio

        # siapkan output, gunakan libx264 + aac agar kompatibel
        output_kwargs = {
            'vcodec': 'libx264',
            'preset': 'medium',
            'crf': '23',
            'acodec': 'aac',
            'movflags': '+faststart'
        }

        # jika audio tidak ada, panggil tanpa audio_stream
        if audio_stream is None:
            ffmpeg_output = ffmpeg.output(video_stream, str(tmp_name), **output_kwargs)
        else:
            ffmpeg_output = ffmpeg.output(video_stream, audio_stream, str(tmp_name), **output_kwargs)

        # overwrite jika tmp ada
        ffmpeg_output = ffmpeg_output.overwrite_output()
        # jalankan
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

    # rename ke nama akhir
    final_path, used_index = RenameFileFunction(tmp_name, output_directory, VIDEO_OUTPUT_EXT, start_video_index)
    safe_print(f"[+] Video disimpan sebagai: {final_path.name}")
    return final_path, used_index

# ----------------------------
# Main workflow
# ----------------------------

def process_directory(root_directory, dry_run=False):
    """
    Proses semua file dalam root_directory (rekursif).
    Untuk setiap folder, kita akan membuat counters terpisah untuk:
      - foto statis (.png)
      - gif (.gif)
      - video (.mp4)
    """
    root_directory = Path(root_directory)
    safe_print(f"[*] Memindai: {root_directory}")

    # ambil semua file media
    found_files = PathScanFunction(root_directory)
    sorted_files = FileSortFunction(found_files)

    # group file per folder: kita akan iterasi berdasarkan folder agar counter reset tiap folder
    # buat dict mapping folder -> list files
    folder_map = {}
    for p in sorted_files:
        folder = p.parent
        if folder not in folder_map:
            folder_map[folder] = []
        folder_map[folder].append(p)

    # iterasi tiap folder
    for folder in folder_map:
        safe_print(f"[>] Memproses folder: {folder}")
        # counters mulai dari 1
        photo_index = 1
        gif_index = 1
        video_index = 1

        # pastikan folder ada
        if not folder.exists():
            safe_print(f"[!] Folder tidak ditemukan: {folder} (lewati)")
            continue

        files_in_folder = folder_map[folder]
        i = 0
        while i < len(files_in_folder):
            file_path = files_in_folder[i]
            try:
                if is_photo_path(file_path):
                    result_path, used_index, type_str = PhotoConvertionFunction(file_path, folder, photo_index, gif_index, dry_run=dry_run)
                    if result_path is not None:
                        if type_str == 'photo':
                            photo_index = used_index + 1
                            # optionally hapus original file jika ingin menghemat storage
                            # os.remove(file_path)
                        elif type_str == 'gif':
                            gif_index = used_index + 1
                    else:
                        safe_print(f"[!] Gagal memproses foto: {file_path.name}")
                elif is_video_path(file_path):
                    result_path, used_index = VideoConvertionFunction(file_path, folder, video_index, dry_run=dry_run)
                    if result_path is not None:
                        video_index = used_index + 1
                    else:
                        safe_print(f"[!] Gagal memproses video: {file_path.name}")
                else:
                    safe_print(f"[!] Type file tidak dikenal: {file_path}")
            except Exception as e:
                safe_print(f"[!] Exception saat memproses {file_path}: {e}")
            i = i + 1

    safe_print("[*] Selesai memproses semua folder.")

def Main():
    safe_print("[*] PROGRAM REKAYASA MULTIMEDIA - Versi Lengkap")
    # arg pertama adalah path, opsional
    work_path = DEFAULT_WORKING_DIRECTORY
    dry_run_flag = False

    if len(sys.argv) >= 2:
        arg1 = sys.argv[1]
        if arg1 in ('--dry-run', '-n'):
            dry_run_flag = True
        else:
            work_path = Path(arg1)

    if len(sys.argv) >= 3:
        if sys.argv[2] in ('--dry-run', '-n'):
            dry_run_flag = True

    safe_print(f"[*] Working directory: {work_path.resolve()}")
    if dry_run_flag:
        safe_print("[*] Mode: DRY RUN (tidak menulis file, hanya simulasi)")

    try:
        process_directory(work_path, dry_run=dry_run_flag)
    except Exception as e:
        safe_print(f"[!] Error di Main: {e}")

if __name__ == '__main__':
    Main()
