# PROGRAM REKAYASA VIDEO
# ================================================================

import os
import sys as sy
import subprocess as sp
import time as ti
import ffmpeg as ff

# DEFINE GLOBAL VARIABLE
# ----------------------------------------------------------------

DEFAULT_DIRECTORY_PATH = '.'
VIDEO_FILE_LIST        = []
VALID_VIDEO_EXTENSION  = ['.mp4', '.mkv', '.mov', '.ts', '.wmv', '.flv']

# DEFINE PROGRAM FUNCITON
# ----------------------------------------------------------------

def get_file_in_directory(DIRECTORY_PATH):
	global VIDEO_FILE_LIST

	print("[*] \033[34mMENCARI\033[0m file video di direktori ini")

	for FILE_IN_DIRECTORY in os.listdir(DIRECTORY_PATH):
		PATH_FILE_IN_DIRECTORY = os.path.join(DIRECTORY_PATH, FILE_IN_DIRECTORY)

		if os.path.isfile(PATH_FILE_IN_DIRECTORY):
			FILE_NAME, FILE_EXTENSION = os.path.splitext(FILE_IN_DIRECTORY)

			if FILE_EXTENSION.lower() in VALID_VIDEO_EXTENSION:
				VIDEO_FILE_LIST.append(PATH_FILE_IN_DIRECTORY)

	print("[*] \033[32mDITEMUKAN\033[0m %d file video di direktori ini" % len(VIDEO_FILE_LIST))

	return VIDEO_FILE_LIST

def get_video_file_information(INPUT_PATH):
	try:
		PROBE        = ff.probe(INPUT_PATH)
		DURATION     = float(PROBE["format"]["duration"])
		INDEX        = 0
		TOTAL_STREAM = len(PROBE["streams"])
		WIDTH        = 0
		HEIGHT       = 0

		while INDEX < TOTAL_STREAM:
			STREAM = PROBE["streams"][INDEX]

			if "codec_type" in STREAM:
				if STREAM["codec_type"] == "video":
					if "width" in STREAM:
						WIDTH    = int(STREAM["width"])

					if "height" in STREAM:
						HEIGHT   = int(STREAM["height"])

					break

			INDEX = INDEX + 1

		return DURATION, WIDTH, HEIGHT

	except:
		print("[!] \033[31mGAGAL\033[0m mendapatkan durasi video")

		return 0

def create_scale_filter(VIDEO_WIDTH, VIDEO_HEIGHT):
	if VIDEO_WIDTH == 0 or VIDEO_HEIGHT == 0:
		return None

	VIDEO_SHORT_SIDE = min(VIDEO_WIDTH, VIDEO_HEIGHT)
	VIDEO_LONG_SIDE  = max(VIDEO_WIDTH, VIDEO_HEIGHT)

	if VIDEO_SHORT_SIDE <= 720:
		return None

	SCALE_RATIO    = 720 / VIDEO_SHORT_SIDE
	NEW_SHORT_SIDE = 720
	NEW_LONG_SIDE  = int(VIDEO_LONG_SIDE * SCALE_RATIO)

	if NEW_SHORT_SIDE % 2 != 0:
		NEW_SHORT_SIDE = NEW_SHORT_SIDE + 1

	if NEW_LONG_SIDE % 2 != 0:
		NEW_LONG_SIDE = NEW_LONG_SIDE + 1

	if VIDEO_WIDTH < VIDEO_HEIGHT:
		return "scale=%s:%s" % (NEW_SHORT_SIDE, NEW_LONG_SIDE)

	else:
		return "scale=%s:%s" % (NEW_LONG_SIDE, NEW_SHORT_SIDE)

def show_bar_process(PROCESS_PRECENT, MODE_BAR=1, BAR_WIDTH=50):
	FILLED_BAR = int(BAR_WIDTH * PROCESS_PRECENT)
	EMPTY_BAR  = BAR_WIDTH - FILLED_BAR
	if MODE_BAR == 1:
		FULL_BAR   = "|%s%s|" % ("\033[33m█\033[0m"*FILLED_BAR, "░"*EMPTY_BAR)

	elif MODE_BAR == 2:
		FULL_BAR   = "|%s%s|" % ("\033[32m█\033[0m"*FILLED_BAR, "░"*EMPTY_BAR)

	elif MODE_BAR == 3:
		FULL_BAR   = "|%s%s|" % ("\033[31m█\033[0m"*FILLED_BAR, "░"*EMPTY_BAR)

	return FULL_BAR

def encode_with_ffmpeg(INPUT_PATH, OUTPUT_PATH):
	VIDEO_FILE_DURATION, VIDEO_FILE_WIDTH, VIDEO_FILE_HEIGHT = get_video_file_information(INPUT_PATH)
	SCALE_FILTER                                             = create_scale_filter(VIDEO_FILE_WIDTH, VIDEO_FILE_HEIGHT)
	VIDEO_NAME                                               = os.path.basename(INPUT_PATH)

	if VIDEO_FILE_DURATION <= 0:
		print("[!] \033[31mGAGAL\033[0m mendapatkan durasi video %s" % INPUT_PATH)

		return

	if SCALE_FILTER:
		FFMPEG_COMMAND = (
			ff
			.input(INPUT_PATH)
			.output(
				OUTPUT_PATH,
				vcodec='libx264',
				crf=20,
				preset='slower',
				acodec='aac',
				audio_bitrate='192k',
				vf=SCALE_FILTER
			)
			.global_args('-movflags', '+faststart')
			.global_args('-progress', 'pipe:1')
			.global_args('-nostats')
			.global_args('-hide_banner')
			.compile()
		)

	else:
		FFMPEG_COMMAND = (
			ff
			.input(INPUT_PATH)
			.output(
				OUTPUT_PATH,
				vcodec='libx264',
				crf=23,
				preset='slower',
				acodec='aac',
				audio_bitrate='192k'
			)
			.global_args('-movflags', '+faststart')
			.global_args('-progress', 'pipe:1')
			.global_args('-nostats')
			.global_args('-hide_banner')
			.compile()
		)

	FFMPEG_PROCESS = sp.Popen(
		FFMPEG_COMMAND,
		stdout=sp.PIPE,
		stderr=sp.STDOUT,
		universal_newlines=True,
		encoding="utf-8",
		errors="replace",
		bufsize=1
		)

	CURRENT_TIME = 0

	for PROCESS_PROGRESS_LINE in FFMPEG_PROCESS.stdout:
		PROCESS_PROGRESS_LINE = PROCESS_PROGRESS_LINE.strip()

		if PROCESS_PROGRESS_LINE == "progress=end":
			PROGRESS_BAR = show_bar_process(1.0, MODE_BAR=2)
			sy.stdout.write(
				"\r[+] 100%% %s %-50.50s - %s/%s" %
				(
					PROGRESS_BAR,
					VIDEO_NAME,
					ti.strftime("%H:%M:%S", ti.gmtime(VIDEO_FILE_DURATION)),
					ti.strftime("%H:%M:%S", ti.gmtime(VIDEO_FILE_DURATION))
				)
			)
			sy.stdout.flush()
			break

		if PROCESS_PROGRESS_LINE.startswith("out_time_ms="):
			VALUE_PROGRESS    = PROCESS_PROGRESS_LINE.split("=")[1]

			if VALUE_PROGRESS == "N/A":
				continue

			OUTPUT_MILICESOND = float(VALUE_PROGRESS)
			CURRENT_TIME      = OUTPUT_MILICESOND / 1_000_000.0
			PROGRESS_PERCENT  = min(CURRENT_TIME / VIDEO_FILE_DURATION, 1.0)
			PROGRESS_BAR      = show_bar_process(PROGRESS_PERCENT)
			PERCENT_TEXT      = "%03d%%" % int(PROGRESS_PERCENT * 100)

			sy.stdout.write(
				"\r[+] %s %s %-50.50s - %s/%s" %
				(
					PERCENT_TEXT,
					PROGRESS_BAR,
					VIDEO_NAME,
					ti.strftime("%H:%M:%S", ti.gmtime(CURRENT_TIME)),
					ti.strftime("%H:%M:%S", ti.gmtime(VIDEO_FILE_DURATION))
				)
			)
			sy.stdout.flush()
	FFMPEG_PROCESS.wait()
	print()

# MAIN PROGRAM
# ----------------------------------------------------------------

def main():
	print("[ PROGRAM REKAYASA VIDEO ]")
	print("================================================================")

	print("[*] \033[34mMENSCAN\033[0m direktori: %s" % os.path.abspath(DEFAULT_DIRECTORY_PATH))
	get_file_in_directory(DEFAULT_DIRECTORY_PATH)

	if not VIDEO_FILE_LIST:
		print("[!] \033[31mKOSONG\033[0m direktori ini.")
		return

	print("[*] \033[34mMENG-ENCODE\033[0m semua file video")

	sy.stdout.reconfigure(encoding='utf-8', line_buffering=True)

	for VIDEO in VIDEO_FILE_LIST:
		VIDEO_FOLDER, VIDEO_FILENAME = os.path.split(VIDEO)
		VIDEO_NAME, VIDEO_EXTENSION  = os.path.splitext(VIDEO_FILENAME)
		OUTPUT_FILE                  = os.path.join(VIDEO_FOLDER, "%s-720p%s" % (VIDEO_NAME, VIDEO_EXTENSION))

		encode_with_ffmpeg(VIDEO, OUTPUT_FILE)

	print("[*] \033[32mSELESAI\033[0m memproses semua file")

if __name__ == '__main__':
	main()