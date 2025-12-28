# Import Library
try:
	import ffmpeg         # Video Manipulation
	from PIL import Image # Photo Manipulation
	import os             # File Manipulation
	import pathlib        # Directory Manipulation
	import re             # Name Manipulation

except ModuleNotFoundError:
	print("Missing Module Not Found")
	exit()

except Exception:
	print("Unknown Error")
	exit()

# Define Variable

DEFAULT_WORKING_DIRECTORY     = pathlib.Path('.')
DEFAULT_SHORT_SIDE_RESOLUTION = 720

SCAN_PHOTO_FORMAT             = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.gif'}
SCAN_VIDEO_FORMAT             = {'.mp4',  '.mkv', '.mov', '.avi',  '.flv',  '.wmv', '.webm', '.ts'}
SCAN_ALL_FORMAT               = SCAN_PHOTO_FORMAT | SCAN_VIDEO_FORMAT

# Define Function

def ScanDirectoryWithPathlib(WORKING_PATH):
	SCAN_RESULT = {}

	try:
		for FILE in WORKING_PATH.rglob('*'):
			try:
				if not FILE.is_file():
					continue

				if not FILE.suffix.lower() in SCAN_ALL_FORMAT:
					continue

				SCAN_RESULT.setdefault(FILE.parent, []).append(FILE)

			except PermissionError as e:
				print(f" ! Tidak ada izin akses: {FILE}")
				continue

			except OSError as e:
				print(f" ! Error OS pada file: {FILE} - {e}")
				continue

	except PermissionError as e:
		print(f" ! Tidak ada izin akses ke direktori: {WORKING_PATH}")

	except Exception as e:
		print(f" ! Error saat scanning: {e}")

	return SCAN_RESULT

def ConvertPhotoWithPillow(INPUT_PATH, OUTPUT_PATH):
	try:
		IMAGE_FILE = Image.open(INPUT_PATH)
		
	except FileNotFoundError as e:
		print(f" ! File tidak ditemukan: {INPUT_PATH}")
		return 3
		
	except PermissionError as e:
		print(f" ! Tidak ada izin membaca: {INPUT_PATH}")
		return 3
		
	except Exception as e:
		print(f" ! Error membuka gambar: {INPUT_PATH} - {e}")
		return 3

	try:
		ORIGINAL_WIDTH, ORIGINAL_HEIGHT = IMAGE_FILE.size
		IMAGE_SHORT_SIDE_RESOLUTION     = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)

		if IMAGE_SHORT_SIDE_RESOLUTION <= DEFAULT_SHORT_SIDE_RESOLUTION:
			return 2

		RESIZE_SCALE = DEFAULT_SHORT_SIDE_RESOLUTION / IMAGE_SHORT_SIDE_RESOLUTION

		NEW_WIDTH  = int(ORIGINAL_WIDTH * RESIZE_SCALE)
		NEW_HEIGHT = int(ORIGINAL_HEIGHT * RESIZE_SCALE)

		try:
			HAS_ANIMATION = IMAGE_FILE.is_animated

		except AttributeError:
			HAS_ANIMATION = False

		if HAS_ANIMATION:
			FRAME         = []
			DURATION_LIST = []

			for FRAME_INDEX in range(IMAGE_FILE.n_frames):
				IMAGE_FILE.seek(FRAME_INDEX)

				RESIZED_FRAME = IMAGE_FILE.copy().resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS)
				FRAME.append(RESIZED_FRAME)

				try:
					DURATION = IMAGE_FILE.info.get('duration', 100)
					DURATION_LIST.append(DURATION)

				except Exception as e:
					DURATION_LIST.append(100)

			FRAME[0].save(OUTPUT_PATH, save_all=True, append_images=FRAME[1:], duration=DURATION_LIST, loop=IMAGE_FILE.info.get('loop', 0), optimize=False)
			return 1
	
		else:
			IMAGE_CONV = IMAGE_FILE.resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS)
			IMAGE_CONV.save(OUTPUT_PATH)
			return 1

	except OSError as e:
		print(f" ! Error menyimpan file: {OUTPUT_PATH} - {e}")
		return 3
		
	except Exception as e:
		print(f" ! Error konversi gambar: {e}")
		return 3


def ConvertVideoWithFFMPEG(INPUT_PATH, OUTPUT_PATH):
	try:
		PROBE_VIDEO = ffmpeg.probe(str(INPUT_PATH))

	except ffmpeg.Error as e:
		print(f" ! Error probe video: {INPUT_PATH}")
		return 3

	except FileNotFoundError as e:
		print(f" ! FFmpeg atau file tidak ditemukan: {INPUT_PATH}")
		return 3
		
	except Exception as e:
		print(f" ! Error saat probe: {e}")
		return 3

	try:
		VIDEO_STREAM = None
		
		for STREAM in PROBE_VIDEO['streams']:
			if STREAM['codec_type'] == 'video':
				VIDEO_STREAM = STREAM
				break
		
		if VIDEO_STREAM is None:
			print(f" ! Tidak ada video stream di: {INPUT_PATH}")
			return 3
		
		ORIGINAL_WIDTH = int(VIDEO_STREAM['width'])
		ORIGINAL_HEIGHT = int(VIDEO_STREAM['height'])
		VIDEO_SHORT_SIDE = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)
		
		if VIDEO_SHORT_SIDE <= DEFAULT_SHORT_SIDE_RESOLUTION:
			return 2
		
		RESIZE_SCALE = DEFAULT_SHORT_SIDE_RESOLUTION / VIDEO_SHORT_SIDE
		NEW_WIDTH = int(ORIGINAL_WIDTH * RESIZE_SCALE)
		NEW_HEIGHT = int(ORIGINAL_HEIGHT * RESIZE_SCALE)
		
		NEW_WIDTH = NEW_WIDTH // 2 * 2
		NEW_HEIGHT = NEW_HEIGHT // 2 * 2
		
		(
			ffmpeg
			.input(str(INPUT_PATH))
			.filter("scale", NEW_WIDTH, NEW_HEIGHT)
			.output(
				str(OUTPUT_PATH),
				vcodec="libx264",
				acodec="copy",
				crf=18,
				preset="slow"
			)
			.run(overwrite_output=True, quiet=True)
		)
		return 1
		
	except ffmpeg.Error as e:
		print(f" ! Error konversi FFmpeg: {INPUT_PATH}")
		return 3

	except PermissionError as e:
		print(f" ! Tidak ada izin menulis: {OUTPUT_PATH}")
		return 3

	except Exception as e:
		print(f" ! Error konversi video: {e}")
		return 3

def ConvertionAndRenameLogic(SCANNED_FILE_LIST):
	# SORTING FILE LIST SECTION
	SORT_RESULT = {}

	for FOLDER_NAME, FILE_LIST in SCANNED_FILE_LIST.items():
		TEMPORARY_SORT = []

		for FILE in FILE_LIST:
			PART_NAME = re.split(r'(\d+)', FILE.name)
			SORT_KEY  = []

			for PART in PART_NAME:
				if PART.isdigit():
					SORT_KEY.append(int(PART))
				else:
					SORT_KEY.append(PART.lower())

			TEMPORARY_SORT.append((SORT_KEY, FILE))

		TEMPORARY_SORT.sort()

		for FILE in TEMPORARY_SORT:
			SORT_RESULT.setdefault(FOLDER_NAME, []).append(FILE[1])

	# CONVERTION LOGIC SECTION
	for FOLDER_NAME, FILE_LIST in SORT_RESULT.items():
		PHOTO_COUNT = 1
		GIF_COUNT   = 1
		VIDEO_COUNT = 1

		print("[+] [%-.64s]" % FOLDER_NAME)

		for FILE in FILE_LIST:
			try:
				# GIF CONVERTION SECTION
				if FILE.suffix.lower() == '.gif':
					OUTPUT_PATH = FILE.parent / ('%s.gif' % GIF_COUNT)

					if FILE.stem.isdigit():
						TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)

						try:
							os.rename(FILE, TEMP_FILE)
						except (PermissionError, FileNotFoundError, OSError) as e:
							print(" ! Error rename %s ke %s: %s" % (FILE.name, TEMP_FILE.name, e))
							continue

						CONVERTION_RESULT = ConvertPhotoWithPillow(TEMP_FILE, OUTPUT_PATH)

						if CONVERTION_RESULT == 1:
							try:
								os.remove(TEMP_FILE)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error hapus %s: %s" % (TEMP_FILE.name, e))
								continue

							print(" - %.64s --- %.64s --- %.64s" % (FILE.name, TEMP_FILE.name, OUTPUT_PATH.name))
							GIF_COUNT += 1

						elif CONVERTION_RESULT == 2:
							try:
								os.rename(TEMP_FILE, OUTPUT_PATH)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error rename %s ke %s: %s" % (TEMP_FILE.name, OUTPUT_PATH.name, e))
								continue

							print(" - %.64s >>> %.64s >>> %.64s" % (FILE.name, TEMP_FILE.name, OUTPUT_PATH.name))
							GIF_COUNT += 1

						else:
							try:
								os.rename(TEMP_FILE, FILE)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error kembalikan %s ke %s: %s" % (TEMP_FILE.name, FILE.name, e))

							print(" - %.64s ||| %.64s ||| %.64s" % (FILE.name, TEMP_FILE.name, FILE.name))

					else:
						CONVERTION_RESULT = ConvertPhotoWithPillow(FILE, OUTPUT_PATH)

						if CONVERTION_RESULT == 1:
							try:
								os.remove(FILE)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error hapus %s: %s" % (FILE.name, e))
								continue

							print(" - %.64s --- %.64s" % (FILE.name, OUTPUT_PATH.name))
							GIF_COUNT += 1

						elif CONVERTION_RESULT == 2:
							print(" - %.64s >>> %.64s" % (FILE.name, OUTPUT_PATH.name))
							GIF_COUNT += 1

						else:
							print(" - %.64s ||| %.64s" % (FILE.name, FILE.name))

				# PHOTO CONVERTION SECTION
				elif FILE.suffix.lower() in SCAN_PHOTO_FORMAT:
					OUTPUT_PATH = FILE.parent / ('%s.png' % PHOTO_COUNT)

					if FILE.stem.isdigit():
						TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)

						try:
							os.rename(FILE, TEMP_FILE)
						except (PermissionError, FileNotFoundError, OSError) as e:
							print(" ! Error rename %s ke %s: %s" % (FILE.name, TEMP_FILE.name, e))
							continue

						CONVERTION_RESULT = ConvertPhotoWithPillow(TEMP_FILE, OUTPUT_PATH)

						if CONVERTION_RESULT == 1:
							try:
								os.remove(TEMP_FILE)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error hapus %s: %s" % (TEMP_FILE.name, e))
								continue

							print(" - %.64s --- %.64s --- %.64s" % (FILE.name, TEMP_FILE.name, OUTPUT_PATH.name))
							PHOTO_COUNT += 1

						elif CONVERTION_RESULT == 2:
							try:
								os.rename(TEMP_FILE, OUTPUT_PATH)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error rename %s ke %s: %s" % (TEMP_FILE.name, OUTPUT_PATH.name, e))
								continue

							print(" - %.64s >>> %.64s >>> %.64s" % (FILE.name, TEMP_FILE.name, OUTPUT_PATH.name))
							PHOTO_COUNT += 1

						else:
							try:
								os.rename(TEMP_FILE, FILE)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error kembalikan %s ke %s: %s" % (TEMP_FILE.name, FILE.name, e))

							print(" - %.64s ||| %.64s ||| %.64s" % (FILE.name, TEMP_FILE.name, FILE.name))

					else:
						CONVERTION_RESULT = ConvertPhotoWithPillow(FILE, OUTPUT_PATH)

						if CONVERTION_RESULT == 1:
							try:
								os.remove(FILE)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error hapus %s: %s" % (FILE.name, e))
								continue

							print(" - %.64s --- %.64s" % (FILE.name, OUTPUT_PATH.name))
							PHOTO_COUNT += 1

						elif CONVERTION_RESULT == 2:
							print(" - %.64s >>> %.64s" % (FILE.name, OUTPUT_PATH.name))
							PHOTO_COUNT += 1

						else:
							print(" - %.64s ||| %.64s" % (FILE.name, FILE.name))
				
				# VIDEO CONVERTION SECTION
				elif FILE.suffix.lower() in SCAN_VIDEO_FORMAT:
					OUTPUT_PATH = FILE.parent / ('%s.mp4' % VIDEO_COUNT)

					if FILE.stem.isdigit():
						TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)

						try:
							os.rename(FILE, TEMP_FILE)
						except (PermissionError, FileNotFoundError, OSError) as e:
							print(" ! Error rename %s ke %s: %s" % (FILE.name, TEMP_FILE.name, e))
							continue

						CONVERTION_RESULT = ConvertVideoWithFFMPEG(TEMP_FILE, OUTPUT_PATH)

						if CONVERTION_RESULT == 1:
							try:
								os.remove(TEMP_FILE)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error hapus %s: %s" % (TEMP_FILE.name, e))
								continue

							print(" - %.64s --- %.64s --- %.64s" % (FILE.name, TEMP_FILE.name, OUTPUT_PATH.name))
							VIDEO_COUNT += 1

						elif CONVERTION_RESULT == 2:
							try:
								os.rename(TEMP_FILE, OUTPUT_PATH)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error rename %s ke %s: %s" % (TEMP_FILE.name, OUTPUT_PATH.name, e))
								continue

							print(" - %.64s >>> %.64s >>> %.64s" % (FILE.name, TEMP_FILE.name, OUTPUT_PATH.name))
							VIDEO_COUNT += 1

						else:
							try:
								os.rename(TEMP_FILE, FILE)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error kembalikan %s ke %s: %s" % (TEMP_FILE.name, FILE.name, e))

							print(" - %.64s ||| %.64s ||| %.64s" % (FILE.name, TEMP_FILE.name, FILE.name))

					else:
						CONVERTION_RESULT = ConvertVideoWithFFMPEG(FILE, OUTPUT_PATH)

						if CONVERTION_RESULT == 1:
							try:
								os.remove(FILE)
							except (PermissionError, FileNotFoundError, OSError) as e:
								print(" ! Error hapus %s: %s" % (FILE.name, e))
								continue

							print(" - %.64s --- %.64s" % (FILE.name, OUTPUT_PATH.name))
							VIDEO_COUNT += 1

						elif CONVERTION_RESULT == 2:
							print(" - %.64s >>> %.64s" % (FILE.name, OUTPUT_PATH.name))
							VIDEO_COUNT += 1

						else:
							print(" - %.64s ||| %.64s" % (FILE.name, FILE.name))

			except Exception as e:
				print(" ! Error tidak terduga pada file %s: %s" % (FILE.name, e))
				continue

# MAIN PROGRAM

def Main():
	try:
		if not DEFAULT_WORKING_DIRECTORY.exists():
			print(f"Error: Direktori {DEFAULT_WORKING_DIRECTORY} tidak ditemukan")
			return

		if not DEFAULT_WORKING_DIRECTORY.is_dir():
			print(f"Error: {DEFAULT_WORKING_DIRECTORY} bukan direktori")
			return

		SCAN_RESULT = ScanDirectoryWithPathlib(DEFAULT_WORKING_DIRECTORY)

		if not SCAN_RESULT:
			print("No Files In Here To The Deepest Directory")
			print("All Operation End, Exit")
			return

		ConvertionAndRenameLogic(SCAN_RESULT)
		print("All Operation End, Exit")

	except KeyboardInterrupt:
		print("\n\n ! Program dihentikan oleh user (Ctrl+C)")
		
	except Exception as e:
		print(f"\n ! Error fatal: {e}")

if __name__ == '__main__':
	Main()