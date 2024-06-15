![Logo](logo.png)

# About OpenIFS
OpenIFS is a FOSS image format which is created with the thought about quality without sacrificing a lot of space its not based on any other image format and its color palette is RGB, its a pretty advanced project of mine so its gonna be hard

# This Image Format and its Features are still being developed

# Fixes to do/fixed/removed/added
- added option to convert from .ifs to formats like .webp .png .jpg .jpeg .jfif .gif 
- fixed compatibility with older .ifs images so the 1st ever image created by OpenIFS (OpenIFS1st.zip) is still avalible to open and maybe if you want you can convert it to a .png and have it as a distorted wallpaper???
- removed whole encryption, it could have been a cool feature but it had so many issues so i said fuck it and just did not make it anymore
- somehow fixed but not fixed conversion error 256 so OpenIFS converts in the best quality it can but the error even tho it does pop up in the terminal, nothing is wrong so maybe my python is just fucked
- removed the annoying ass meta and exif data window for removal of it and replaced it with just a question if you want to remove metadta cuz exif data and its removal is not suppoted by OpenCV
- Forgot to add that the image which at first .png had 211kB in .ifs is actually 77kB without losing quality, 134kB less!!!

# All Known Errors
- Conversion error 256: RuntimeWarning: overflow encountered in scalar subtract
  delta = tuple(((p - pp + 256) % 256) for p, pp in zip(pixel, prev_pixel))

# TODO:
- Give the program a better GUI

# Libraries to install
- PyQt5
- bz2
- opencv-python-headless
- numpy
