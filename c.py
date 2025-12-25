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