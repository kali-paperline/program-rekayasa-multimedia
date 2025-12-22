# Program ini bernama PROGRAM REKAYASA RESOLUSI MULTIMEDIA. Program ini dibuat oleh Kali Paperline.
# Program ini adalah sebuah alat untuk mengurangi kebutuhan penyimpanan dengan cara mengubah resolusi foto dan video menjadi 720p.
#
# Alur Kerja Program:
# 1. Program melakukan scan direktori kerja dengan modul pathlib hingga sub direktori terdalam.
# 2. Program melakukan seleksi pada file - file yang ditemukan.
# 3. Program melakukan rekayasa pada file - file sesuai dengan perlakuan yang telah ditentukan sebelumnya.
#
# Kondisi Tujuan Program:
# 1. Semua file foto dan video beresolusi <=720p.
# 2. Semua file foto dan video memiliki nama string urut.
# 3. Semua file .gif memiliki semua frame yang berfungsi dengan baik sesuai syarat lainnya
#
# Pustaka Python 3 yang digunakan:
# 1. ffmpeg
# 2. os
# 3. PIL
# 4. time
# 5. subprocess
# 6. sys

