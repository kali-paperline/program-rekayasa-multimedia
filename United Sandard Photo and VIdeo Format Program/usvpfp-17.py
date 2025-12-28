# UNITED STANDARD VIDEO & PHOTO FORMAT PROGRAM (PYTHON 3)
# 1 IMPORT LIBRARY
# 1.1 IMPORT BUILD-IN LIBRARY
import os
import pathlib
import re
# 1.2 IMPORT EXTERNAL LIBRARY
try:	
	import ffmpeg
	from PIL import Image
# 1.3 ERROR MODULE NOT FOUND HANDLING
except ModuleNotFoundError:
	print("[!] Module Not Found Error, try \"pip install ffmpeg-python pillow\"")
# 2 DEFINE VARIABLE
# 2.1 DEFINE FOLDER AND RESOLUTION VARIABLE
DEFAULT_WORKING_DIRECTORY     = pathlib.Path('.')
DEFAULT_SHORT_SIDE_RESOLUTION = 720 # 1080 FOR BETTER RESOLUTION
# 2.2 DEFINE FILE FORMAT VARIABLE
SCAN_PHOTO_FORMAT             = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.gif'}
SCAN_VIDEO_FORMAT             = {'.mp4',  '.mkv', '.mov', '.avi',  '.flv',  '.wmv', '.webm', '.ts'}
SCAN_ALL_FORMAT               = SCAN_PHOTO_FORMAT | SCAN_VIDEO_FORMAT
# 3 DEFINE FUNCTION
# 3.1 SCAN WORKING DIRECTORY FUNCTION
def ScanDirectoryWithPathlib(ROOT_PATH):
	SCAN_RESULT ={}
	# 3.1.1 RECURSIVE SCAN WITH PATHLIB
	try:
		for FILE in ROOT_PATH.rglob('*'):
			try:
				# 3.1.2 FILTER NO FILE IN PATH
				if not FILE.is_file():
					continue
				# 3.1.3 FILTER NOT IN CONTEXT FILE
				if not FILE.suffix.lower() in SCAN_ALL_FORMAT:
					continue
				# 3.1.4 INSERT FILE INTO SCAN RESULT
				SCAN_RESULT.setdefault(FILE.parent, []).append(FILE)
			# 3.1.5 ERROR FILE PREMISSION DENIED HANDLING 
			except PermissionError:
				print("[!] File %s Permission Denied Error" % FILE[-64:])
	# 3.1.6 ERROR ROOT DIRECTORY PREMISSION DENIED HANDLING 
	except PermissionError:
		print("[!] Root Directory Permission Denied Error")
		return SCAN_RESULT
	# 3.1.7 RETURN SECTION
	return SCAN_RESULT
# 3.2 CONVERT PHOTO WITH PILLOW
def ConvertPhotoWithPillow(INPUT_PATH, OUTPUT_PATH):
	# 3.2.1 OPEN IMAGE FILE WITH PILLOW IMAGE
	try:
		INPUT_IMAGE_FILE = Image.open(INPUT_PATH)
	# 3.2.2 ERROR FILE NOT FOUND HANDLING
	except FileNotFoundError:
		print("[!] File %s Not Found Error" % INPUT_PATH[-64:])
		# 3.2.3 RETURN ERROR FILE NOT FOUND
		return 3
	# 3.2.4 ERROR PERMISSION DENIED HANDLING
	except PermissionError:
		print("[!] File %s Permission Denied Error" % INPUT_PATH[-64:])
		# 3.2.5 RETURN ERROR PERMISSION DENIED
		return 3
	# 3.2.6 GET IMAGE RESOLUTION
	try:
		ORIGINAL_WIDTH, ORIGINAL_HEIGHT = INPUT_IMAGE_FILE.size
	except AttributeError:
		# 3.2.7 RETURN ERROR ATRIBUTE
		return 3
	# 3.2.8 MAKE RESIZE SCALE
	IMAGE_SHORT_SIDE_RESOLUTION = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)
	RESIZE_SCALE                = DEFAULT_SHORT_SIDE_RESOLUTION / IMAGE_SHORT_SIDE_RESOLUTION
	NEW_WIDTH                   = int(ORIGINAL_WIDTH * RESIZE_SCALE)
	NEW_HEIGHT                  = int(ORIGINAL_HEIGHT * RESIZE_SCALE)
	# 3.2.9 FILTER STANDARD FILE
	if IMAGE_SHORT_SIDE_RESOLUTION <= DEFAULT_SHORT_SIDE_RESOLUTION:
		# 3.2.10 RETURN SKIP FILE STANDARD
		return 2
	# 3.2.11 CHECK IF FILE IS GIF
	if getattr(INPUT_IMAGE_FILE, "is_animated", False):
		FRAME_LIST    = []
		DURATION_LIST = []
		# 3.2.12 FRAME LOOPING
		for FRAME_INDEX in range(INPUT_IMAGE_FILE.n_frames):
			INPUT_IMAGE_FILE.seek(FRAME_INDEX)
			# 3.2.13 RESIZE FRAME
			RESIZED_FRAME = INPUT_IMAGE_FILE.copy().resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS)
			# 3.2.14 INSERT RESIZED FRAME TO FRAME LIST
			FRAME_LIST.append(RESIZED_FRAME)
			# 3.2.15 ADD FRAME DURATION TO DURATION LIST
			try:
				DURATION_LIST.append(INPUT_IMAGE_FILE.info.get('duration', 100))
			# 3.2.16 ERROR NO HURATION HANDLING
			except AttributeError:
				DURATION_LIST.append(100)
		# 3.2.17 SAVE ERSIZED GIF TO TOUPUT PATH
		FRAME_LIST[0].save(OUTPUT_PATH, save_all=True, append_images=FRAME_LIST[1:], duration=DURATION_LIST, loop=INPUT_IMAGE_FILE.info.get('loop', 0), optimize=False)
		# 3.2.18 RETURN GIF SUCCESS
		return 1
	# 3.2.18 NON GIF PHOTO RESIZE
	else:
		INPUT_IMAGE_FILE.resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS).save(OUTPUT_PATH)
		# 3.2.19 RETURN PHOTO SUCCESS
		return 1
# 3.3 CONVERT VIDEO WITH FFMPEG
def ConvertVideoWithFFMPEG(INPUT_PATH, OUTPUT_PATH):
	# 3.3.1 OPEN VIDEO FILE WITH FFPROBE
	try:
		PROBE_VIDEO = ffmpeg.probe(str(INPUT_PATH))
	# 3.3.2 ERROR FILE NOT FOUND HANDLING
	except FileNotFoundError:
		print("[!] File %s Not Found Error" % INPUT_PATH[-64:])
		# 3.3.3 RETURN ERROR FILE NOT FOUND
		return 3
	# 3.2.4 ERROR PERMISSION DENIED HANDLING
	except PermissionError:
		print("[!] File %s Permission Denied Error" % INPUT_PATH[-64:])
		# 3.3.5 RETURN ERROR PERMISSION DENIED
		return 3
	# 3.3.6 ERROR FFMPEG HANDLING
	except ffmpeg.Error:
		print("[!] File %s FFMPEG Error" % INPUT_PATH[-64:])
		# 3.3.7 RETURN ERROR FROM FFMPEG
		return 3
	# 3.3.8 GET VIDEO INFORMATION
	try:
		VIDEO_STREAM = None
		# 3.3.9 GET VIDEO STREAM INFORMATION
		for STREAM in PROBE_VIDEO['streams']:
			if STREAM['codec_type'] == 'video':
				VIDEO_STREAM = STREAM
				break
		# 3.3.10 FILTER STREAM FILE
		if VIDEO_STREAM is None:
			# 3.3.11 RETURN NO VIDEO STREAM
			return 3
		# 3.3.12 GET VIDEO RESOLUTION
		VIDEO_SHORT_SIDE = min(int(VIDEO_STREAM['width']), int(VIDEO_STREAM['height']))
		# 3.3.13 FILTER STANDARD FILE
		if VIDEO_SHORT_SIDE <= DEFAULT_SHORT_SIDE_RESOLUTION:
			# 3.3.14 RETURN SKIP STANDARD FILE
			return 2
		# 3.3.15 MAKE RESIZE SCALE
		RESIZE_SCALE = DEFAULT_SHORT_SIDE_RESOLUTION / VIDEO_SHORT_SIDE
		NEW_WIDTH    = int(VIDEO_STREAM['width'] * RESIZE_SCALE)
		NEW_HEIGHT   = int(VIDEO_STREAM['height'] * RESIZE_SCALE)
		# 3.3.16 ROUNDING RESIZE SCALE
		NEW_WIDTH    = NEW_WIDTH // 2 * 2
		NEW_HEIGHT   = NEW_HEIGHT // 2 * 2
		# 3.3.17 FFMPEG COMMAND
		(
			ffmpeg
			.input(str(INPUT_PATH))
			.filter("scale", NEW_WIDTH, NEW_HEIGHT)
			.output(str(OUTPUT_PATH), vcodec="libx264", acodec="copy", crf=18, preset="slow")
			.run(overwrite_output=True, quiet=True)
		)
		# 3.3.18 RETURN VIDEO SUCCESS
		return 1
	# 3.3.19 ERROR FFMEPG HANDLING
	except ffmpeg.Error:
		print("[!] File %s FFMPEG Error" % INPUT_PATH[-64:])
		# 3.3.20 RETURN FFMPEG ERROR
		return 3
	# 3.3.21 ERROR PERMISSION DENIED HANDLING
	except PermissionError as e:
		print(f" ! Tidak ada izin menulis: {OUTPUT_PATH}")
		# 3.3.22 RETURN PERMISSION DENIED ERROR
		return 3
# 3.4 CONVERTION AND RENAME LOGIC
def SortAndConvertAndRenameLogic(SCAN_FILE_LIST):
	SORT_RESULT = {}
	# 3.4.1 LOOPING SORT
	for FOLDER_NAME, FILE_LIST in SCAN_FILE_LIST.items():
		TEMPORARY_SORT = []
		# 3.4.2 LOOPING PER PATH
		for FILE in FILE_LIST:
			# 3.4.3 SPLIT FILE NAME WITH REGULAR EXPRESSION
			PART_NAME = re.split(r'(\d+)', FILE.name)
			SORT_KEY  = []
			# 3.4.4 LOOPING PER FILE NAME PART
			for PART in PART_NAME:
				# 3.4.5 INSERT FILE PART NAME TO SORT KEY
				if PART.isdigit():
					SORT_KEY.append(int(PART))
				else:
					SORT_KEY.append(PART.lower())
			# 3.4.6 INSERT FILE SORT KEY TO TEMPORARY SORT
			TEMPORARY_SORT.append((SORT_KEY, FILE))
			# 3.4.7 SORT TEMPORARY SORT
		TEMPORARY_SORT.sort()
		# 3.4.8 LOOPING TEMPORARY SORT
		for FILE in TEMPORARY_SORT:
			# 3.4.9 INSERT FILE TO SORT RESULT
			SORT_RESULT.setdefault(FOLDER_NAME, []).append(FILE[1])
	# 3.4.10 LOOPING CONVERT AND RENAME
	for FOLDER_NAME, FILE_LIST in SORT_RESULT.items():
		PHOTO_COUNT = GIF_COUNT = VIDEO_COUNT = 0
		# 3.4.11 PRINT CURRENT FOLDER
		print("[+] %s" % FOLDER_NAME)
		# 3.4.12 LOOPING PER FILE
		for FILE in FILE_LIST:
			# 3.4.13 FILTER GIF FILE
			if FILE.suffix.lower() == '.gif':
				# 3.4.14 GIF FILE OUTPUT NAME
				OUTPUT_PATH = FILE.parent / ('%s.gif' % GIF_COUNT)
				# 3.4.15 FILTER DIGIT NAME GIF FILE
				if FILE.stem.isdigit():
					# 3.4.16 TEMPORARY GIF FILE NAME
					TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)
					# 3.4.17 RENAME DIGIT FILE TO TEMPORARY FILE
					try:
						os.rename(FILE, TEMP_FILE)
					# 3.4.18 ERROR PERMISSION DENIED HANDLING
					except PermissionError:
						print("[!] File %s Permission Denied Error" % FILE.name[-64:])
						continue
					# 3.4.19 ERROR FILE NOT FOUND ERROR
					except FileNotFoundError:
						print("[!] File %s File Not Found Error" % FILE.name[-64:])
						continue
					# 3.4.20 CONVERT GIF
					CONVERTION_RESULT = ConvertPhotoWithPillow(TEMP_FILE, OUTPUT_PATH)
					# 3.4.21 CONVERTION RESULT SUCCESS
					if CONVERTION_RESULT == 1:
						# 3.4.22 REMOVE TEMP FILE
						try:
							os.remove(TEMP_FILE)
						# 3.4.23 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.24 ERROR FILE NOT FOUND HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.25 PRINT SUCCESS GIF FILE
						print(" + [+] %s --- %s --- %s" % (FILE.name[-64:], TEMP_FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.26 ADD GIF COUNT
						GIF_COUNT += 1
					# 3.4.27 CONVERTION RESULT SKIP
					elif CONVERTION_RESULT == 2:
						# 3.4.28 RENAME TEMP FILE BACK
						try:
							os.rename(TEMP_FILE, OUTPUT_PATH)
						# 3.4.29 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.30 ERROR FILE NOT FOUND ERROR HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.31 PRINT SKIP GIF FILE
						print(" + [+] %s >>> %s >>> %s" % (FILE.name[-64:], TEMP_FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.32 ADD GIF COUNT
						GIF_COUNT += 1
					# 3.4.33 CONVERTION RESULT ERROR
					else:
						# 3.4.34 RENAME TEMP FILE BACK
						try:
							os.rename(TEMP_FILE, FILE)
						# 3.4.35 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.36 ERROR FILE NOT FOUND ERROR HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % TEMP_FILE.name[-64:])
							continue
				# 3.4.37 FILTER NON DIGIT NAME GIF FILE
				else:
					# 3.4.38 CONVERT GIF FILE
					CONVERTION_RESULT = ConvertPhotoWithPillow(FILE, OUTPUT_PATH)
					# 3.4.39 CONVERTION RESULT SUCCESS
					if CONVERTION_RESULT == 1:
						# 3.4.40 REMOVE ORIGINAL FILE
						try:
							os.remove(FILE)
						# 3.4.41 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % FILE.name[-64:])
							continue
						# 3.4.42 ERROR FILE NOT FOUND HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % FILE.name[-64:])
							continue
						# 3.4.43 PRINT SUCCESS GIF FILE
						print(" + [+] %s --- %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.44 ADD GIF COUNT	
						GIF_COUNT += 1
					# 3.4.45 CONVERTION RESULT SKIP
					elif CONVERTION_RESULT == 2:
						# 3.4.46 RENAME FILE SKIP
						try:
							os.rename(FILE, OUTPUT_PATH)
						# 3.4.47 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % FILE.name[-64:])
							continue
						# 3.4.48 ERROR FILE NOT FOUND HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % FILE.name[-64:])
							continue
						# 3.4.49 PRINT SKIP GIF FILE
						print(" + [+] %s >>> %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.50 ADD GIF COUNT
						GIF_COUNT += 1
					# 3.4.51 CONVERTION RESULT ERROR
					else:
						# 3.4.52 PRINT ERROR GIF FILE
						print(" + [+] %s XXX %s" % (FILE.name[-64:], FILE.name[-64:]))
			# 3.4.53 FILETER PHOTO FILE
			elif FILE.suffix.lower() in SCAN_PHOTO_FORMAT:
				# 3.4.54 PHOTO FILE OUTPUT NAME
				OUTPUT_PATH = FILE.parent / ('%s.png' % PHOTO_COUNT)
				# 3.4.55 FILTER DIGIT NAME PHOTO FILE
				if FILE.stem.isdigit():
					# 3.4.56 TEMPORARY PHOTO FILE NAME
					TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)
					# 3.4.57 RENAME DIGIT FILE TO TEMPORARY FILE
					try:
						os.rename(FILE, TEMP_FILE)
					# 3.4.58 ERROR PERMISSION DENIED HANDLING
					except PermissionError:
						print("[!] File %s Permission Denied Error" % FILE.name[-64:])
						continue
					# 3.4.59 ERROR FILE NOT FOUND ERROR
					except FileNotFoundError:
						print("[!] File %s File Not Found Error" % FILE.name[-64:])
						continue
					# 3.4.60 CONVERT PHOTO
					CONVERTION_RESULT = ConvertPhotoWithPillow(TEMP_FILE, OUTPUT_PATH)
					# 3.4.61 CONVERTION RESULT SUCCESS
					if CONVERTION_RESULT == 1:
						# 3.4.62 REMOVE TEMP FILE
						try:
							os.remove(TEMP_FILE)
						# 3.4.63 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.64 ERROR FILE NOT FOUND HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.65 PRINT SUCCESS PHOTO FILE
						print(" + [+] %s --- %s --- %s" % (FILE.name[-64:], TEMP_FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.66 ADD PHOTO COUNT
						PHOTO_COUNT += 1
					# 3.4.67 CONVERTION RESULT SKIP
					elif CONVERTION_RESULT == 2:
						# 3.4.68 RENAME TEMP FILE BACK
						try:
							os.rename(TEMP_FILE, OUTPUT_PATH)
						# 3.4.69 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.70 ERROR FILE NOT FOUND ERROR HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.71 PRINT SKIP PHOTO FILE
						print(" + [+] %s >>> %s >>> %s" % (FILE.name[-64:], TEMP_FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.72 ADD GIF COUNT
						PHOTO_COUNT += 1
					# 3.4.73 CONVERTION RESULT ERROR
					else:
						# 3.4.74 RENAME TEMP FILE BACK
						try:
							os.rename(TEMP_FILE, FILE)
						# 3.4.75 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.76 ERROR FILE NOT FOUND ERROR HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % TEMP_FILE.name[-64:])
							continue
				# 3.4.77 FILTER NON DIGIT NAME PHOTO FILE
				else:
					# 3.4.78 CONVERT PHOTO FILE
					CONVERTION_RESULT = ConvertPhotoWithPillow(FILE, OUTPUT_PATH)
					# 3.4.79 CONVERTION RESULT SUCCESS
					if CONVERTION_RESULT == 1:
						# 3.4.80 REMOVE ORIGINAL FILE
						try:
							os.remove(FILE)
						# 3.4.81 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % FILE.name[-64:])
							continue
						# 3.4.82 ERROR FILE NOT FOUND HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % FILE.name[-64:])
							continue
						# 3.4.83 PRINT SUCCESS PHOTO FILE
						print(" + [+] %s --- %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.84 ADD PHOTO COUNT	
						PHOTO_COUNT += 1
					# 3.4.85 CONVERTION RESULT SKIP
					elif CONVERTION_RESULT == 2:
						# 3.4.86 RENAME FILE SKIP
						try:
							os.rename(FILE, OUTPUT_PATH)
						# 3.4.87 ERROR PERMISSION DENIED ERROR
						except PermissionError:
							print("[!] File %s Permission Denied Error" % FILE.name[-64:])
							continue
						# 3.4.88 ERROR FILE NOT FOUND HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % FILE.name[-64:])
							continue
						# 3.4.89 PRINT SKIP PHOTO FILE
						print(" + [+] %s >>> %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.90 ADD PHOTO COUNT
						PHOTO_COUNT += 1
					# 3.4.91 CONVERTION RESULT ERROR
					else:
						# 3.4.92 PRINT ERROR GIF FILE
						print(" + [+] %s XXX %s" % (FILE.name[-64:], FILE.name[-64:]))
			# 3.4.93 FILETER VIDEO FILE
			elif FILE.suffix.lower() in SCAN_VIDEO_FORMAT:
				# 3.4.94 VIDEO FILE OUTPUT NAME
				OUTPUT_PATH = FILE.parent / ('%s.mp4' % VIDEO_COUNT)
				# 3.4.95 FILTER DIGIT NAME VIDEO FILE
				if FILE.stem.isdigit():
					# 3.4.96 TEMPORARY VIDEO FILE NAME
					TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)
					# 3.4.97 RENAME DIGIT FILE TO TEMPORARY FILE
					try:
						os.rename(FILE, TEMP_FILE)
					# 3.4.98 ERROR PERMISSION DENIED HANDLING
					except PermissionError:
						print("[!] File %s Permission Denied Error" % FILE.name[-64:])
						continue
					# 3.4.99 ERROR FILE NOT FOUND ERROR
					except FileNotFoundError:
						print("[!] File %s File Not Found Error" % FILE.name[-64:])
						continue
					# 3.4.100 CONVERT VIDEO
					CONVERTION_RESULT = ConvertVideoWithFFMPEG(TEMP_FILE, OUTPUT_PATH)
					# 3.4.101 CONVERTION RESULT SUCCESS
					if CONVERTION_RESULT == 1:
						# 3.4.102 REMOVE TEMP FILE
						try:
							os.remove(TEMP_FILE)
						# 3.4.103 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.104 ERROR FILE NOT FOUND HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.105 PRINT SUCCESS VIDEO FILE
						print(" + [+] %s --- %s --- %s" % (FILE.name[-64:], TEMP_FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.106 ADD VIDEO COUNT
						VIDEO_COUNT += 1
					# 3.4.107 CONVERTION RESULT SKIP
					elif CONVERTION_RESULT == 2:
						# 3.4.108 RENAME TEMP FILE BACK
						try:
							os.rename(TEMP_FILE, OUTPUT_PATH)
						# 3.4.109 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.110 ERROR FILE NOT FOUND ERROR HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.111 PRINT SKIP VIDEO FILE
						print(" + [+] %s >>> %s >>> %s" % (FILE.name[-64:], TEMP_FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.112 ADD GIF COUNT
						VIDEO_COUNT += 1
					# 3.4.113 CONVERTION RESULT ERROR
					else:
						# 3.4.114 RENAME TEMP FILE BACK
						try:
							os.rename(TEMP_FILE, FILE)
						# 3.4.115 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % TEMP_FILE.name[-64:])
							continue
						# 3.4.116 ERROR FILE NOT FOUND ERROR HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % TEMP_FILE.name[-64:])
							continue
				# 3.4.117 FILTER NON DIGIT NAME VIDEO FILE
				else:
					# 3.4.118 CONVERT VIDEO FILE
					CONVERTION_RESULT = ConvertVideoWithFFMPEG(FILE, OUTPUT_PATH)
					# 3.4.119 CONVERTION RESULT SUCCESS
					if CONVERTION_RESULT == 1:
						# 3.4.120 REMOVE ORIGINAL FILE
						try:
							os.remove(FILE)
						# 3.4.121 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % FILE.name[-64:])
							continue
						# 3.4.122 ERROR FILE NOT FOUND HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % FILE.name[-64:])
							continue
						# 3.4.123 PRINT SUCCESS VIDEO FILE
						print(" + [+] %s --- %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.124 ADD VIDEO COUNT	
						VIDEO_COUNT += 1
					# 3.4.125 CONVERTION RESULT SKIP
					elif CONVERTION_RESULT == 2:
						# 3.4.126 RENAME FILE SKIP
						try:
							os.rename(FILE, OUTPUT_PATH)
						# 3.4.127 ERROR PERMISSION DENIED HANDLING
						except PermissionError:
							print("[!] File %s Permission Denied Error" % FILE.name[-64:])
							continue
						# 3.4.128 ERROR FILE NOT FOUND HANDLING
						except FileNotFoundError:
							print("[!] File %s File Not Found Error" % FILE.name[-64:])
							continue
						
						# 3.4.129 PRINT SKIP VIDEO FILE
						print(" + [+] %s >>> %s" % (FILE.name[-64:], OUTPUT_PATH.name[-64:]))
						# 3.4.130 ADD VIDEO COUNT
						VIDEO_COUNT += 1
					# 3.4.131 CONVERTION RESULT ERROR
					else:
						# 3.4.132 PRINT ERROR VIDEO FILE
						print(" + [+] %s XXX %s" % (FILE.name[-64:], FILE.name[-64:]))
# 4 MAIN PROGRAM
# 4.1 MAIN PROGRAM FUNCTION
def Main():
	# 4.1.1 CHECK DIRECTORY EXIST
	try:
		if not DEFAULT_WORKING_DIRECTORY.exists():
			print("[!] Direktori Tidak Ditemukan")
			return
		# 4.1.2 CHECK DIRECTORY IS DIRECTORY
		if not DEFAULT_WORKING_DIRECTORY.is_dir():
			print("[!] Direktori Tidak Valid")
			return
		# 4.1.3 START SCAN DIRECTORY
		print("[*] Scan Directory %s" % str(DEFAULT_WORKING_DIRECTORY.resolve())[-64:])
		SCAN_DIRECTORY_RESULT = ScanDirectoryWithPathlib(DEFAULT_WORKING_DIRECTORY)
		# 4.1.4 FILTER SCAN RESULT CONTENT
		if not SCAN_DIRECTORY_RESULT:
			print("[!] Empty Directory")
			return
		# 4.1.5 SORT, CONVERT, AND RENAME FILE
		SortAndConvertAndRenameLogic(SCAN_DIRECTORY_RESULT)
		# 4.1.6 PRINT ALL OPERATION END
		print("[*] All Operation Finish, Exit")
	# 4.1.6 ERROR KEYBOARD INTERRUPT HANDLING
	except KeyboardInterrupt:
		print("[!] Keyboard Interrupt")
		return
# 4.2 START PROGRAM
if __name__ == '__main__':
	Main()
# 4.3 END OF FILE