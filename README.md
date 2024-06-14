# Quick Update
OpenIFS has created its first image with the .ifs format even tho the image has messed up colors and is distorted it does somehow work ,the image will be added as a another file named '1stimage.ifs' in the zip 'OpenIFS1st.zip', and because i'm seeing progress of this format being better and better i'm probably going to be developing it as much as i can and because in poland its almost summer vacation i will be spending a lot of time making progress

# OpenIFS
OpenIFS is a FOSS image format which can be encrypted with a password or without one its not based on any other image format and its color palette is RGB, its a pretty advanced project of mine so its gonna be hard

# This Image Format and its Properties are still being developed
## Issues
- when trying to convert with or without encryption this error (lets call it error 256) shows up in terminal and i still do not know how to fix it: main.py:61: RuntimeWarning: overflow encountered in scalar subtract
  delta = tuple(((p - pp + 256) % 256) for p, pp in zip(pixel, prev_pixel))

# TODO:
- Fix conversion error 256
- Give the program a better GUI
- Make .ifs images smaller in size 1080p .ifs image compared to .png: .png = 72.89 kB, .ifs = 2.111 MiB (without encryption), .ifs = 5.001 MiB (with encryption)

# LIbraries to install
- PyQt5
- cryptography
- zlib
- opencv-python-headless
- numpy
