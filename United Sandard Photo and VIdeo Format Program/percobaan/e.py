import ffmpeg as ff
import os
import pathlib as pl
import PIL as pi
import shutil as sh

DEFAULT_WORKING_DIRECTORY = pl.Path('.')

SHORT_SIDE_TARGET       = 720

PHOTO_INPUT_EXTENSIONS  = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.avif', '.gif'}
VIDEO_INPUT_EXTENSIONS  = {'.mp4', '.mkv', '.m4v', '.mov', '.ts', '.webm', '.avi', '.wmv'}

PHOTO_OUTPUT_EXT_STATIC = '.png'
PHOTO_OUTPUT_EXT_GIF    = '.gif'
VIDEO_OUTPUT_EXT        = '.mp4'

Image.MAX_IMAGE_PIXELS = None

