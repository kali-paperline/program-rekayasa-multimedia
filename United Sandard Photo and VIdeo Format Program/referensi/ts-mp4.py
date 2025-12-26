import os
import subprocess

def convert_ts_to_mp4(input_file, output_file):
    """
    Konversi file .ts ke .mp4 menggunakan ffmpeg.
    Jika audio tidak kompatibel, ubah ke AAC.
    """
    try:
        # Coba konversi cepat tanpa re-encode
        command_copy = ["ffmpeg", "-y", "-i", input_file, "-c", "copy", output_file]
        subprocess.run(command_copy, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ Berhasil convert (copy): {output_file}")
    except subprocess.CalledProcessError:
        # Jika gagal (biasanya karena codec audio tidak cocok), ubah audio ke AAC
        command_aac = ["ffmpeg", "-y", "-i", input_file, "-c:v", "copy", "-c:a", "aac", output_file]
        subprocess.run(command_aac, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ Berhasil convert (re-encode audio): {output_file}")

def auto_scan_and_convert():
    """
    Scan folder tempat script berada dan convert semua file .ts ke .mp4
    """
    current_dir = os.getcwd()
    ts_files = [f for f in os.listdir(current_dir) if f.lower().endswith(".ts")]

    if not ts_files:
        print("⚠️ Tidak ada file .ts ditemukan di direktori ini.")
        return

    print(f"🔍 Ditemukan {len(ts_files)} file .ts. Memulai konversi...\n")

    for ts_file in ts_files:
        base_name = os.path.splitext(ts_file)[0]
        mp4_file = f"{base_name}.mp4"
        convert_ts_to_mp4(ts_file, mp4_file)

    print("\n🎉 Semua file selesai dikonversi!")

if __name__ == "__main__":
    auto_scan_and_convert()
