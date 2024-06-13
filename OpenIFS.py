import sys
import struct
import random
import cv2
import numpy as np
import zlib
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QVBoxLayout, QWidget, QToolBar, QAction, QInputDialog, QLineEdit, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QPalette, QColor
from PyQt5.QtCore import Qt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os

# Key derivation function
def derive_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

# Encrypt data using Camellia with padding
def encrypt(data, password):
    salt = os.urandom(16)
    key = derive_key(password, salt)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.Camellia(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad the data to a multiple of the block size
    padded_data = data + b'\x00' * (16 - len(data) % 16)

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return salt + iv + encrypted_data

# Decrypt data using Camellia with padding
def decrypt(encrypted_data, password):
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    encrypted_data = encrypted_data[32:]
    key = derive_key(password, salt)
    cipher = Cipher(algorithms.Camellia(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

    # Remove padding from the decrypted data
    unpadded_data = decrypted_data.rstrip(b'\x00')
    return unpadded_data

# Delta encoding
def delta_encode(pixels):
    deltas = []
    prev_pixel = pixels[0]
    for pixel in pixels:
        delta = tuple(((p - pp + 256) % 256) for p, pp in zip(pixel, prev_pixel))
        deltas.append(delta)
        prev_pixel = pixel
    return deltas

# Delta decoding
def delta_decode(deltas):
    pixels = []
    prev_pixel = (0, 0, 0)
    for delta in deltas:
        pixel = tuple((d + pp) % 256 for d, pp in zip(delta, prev_pixel))
        pixels.append(pixel)
        prev_pixel = pixel
    return pixels

# Convert image to format
def convert_image_to_format(image, password=None, delete_metadata=False):
    # Convert image to numpy array
    pixels = np.array(image)
    height, width, channels = pixels.shape

    # Flatten the pixel array
    flat_pixels = pixels.reshape(-1, channels)

    # Delta encode the pixels
    encoded_pixels = delta_encode(flat_pixels)

    # Flatten the delta-encoded pixels
    flat_encoded_pixels = [value for pixel in encoded_pixels for value in pixel]

    # Compress the data
    compressed_data = zlib.compress(bytes(flat_encoded_pixels))

    # Encrypt the data if a password is provided
    if password:
        encrypted_data = encrypt(compressed_data, password)
    else:
        encrypted_data = compressed_data

    # Create a header with metadata
    metadata = {
        "width": width,
        "height": height,
        "channels": channels,
        "delete_metadata": delete_metadata
    }
    metadata_bytes = json.dumps(metadata).encode()

    # Combine the header and the encrypted data
    return metadata_bytes + b'---' + encrypted_data

# Convert format to image
def convert_format_to_image(data, password=None):
    # Split the metadata and the encrypted data
    metadata_bytes, encrypted_data = data.split(b'---', 1)
    metadata = json.loads(metadata_bytes.decode())

    width = metadata["width"]
    height = metadata["height"]
    channels = metadata["channels"]
    delete_metadata = metadata["delete_metadata"]

    # Decrypt the data if a password is provided
    if password:
        compressed_data = decrypt(encrypted_data, password)
    else:
        compressed_data = encrypted_data

    # Decompress the data
    flat_encoded_pixels = list(zlib.decompress(compressed_data))

    # Convert the flat list of encoded pixels to a list of tuples
    encoded_pixels = [tuple(flat_encoded_pixels[i:i+channels]) for i in range(0, len(flat_encoded_pixels), channels)]

    # Delta decode the pixels
    decoded_pixels = delta_decode(encoded_pixels)

    # Reshape the flat pixel array to the original shape
    pixels = np.array(decoded_pixels, dtype=np.uint8).reshape(height, width, channels)

    # Create an image from the pixel data
    return pixels

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Format Converter")
        self.resize(800, 600)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        self.setCentralWidget(self.image_label)

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        open_action = QAction("Open Image", self)
        open_action.triggered.connect(self.load_image)
        toolbar.addAction(open_action)

        open_format_action = QAction("Open IFS", self)
        open_format_action.triggered.connect(self.load_format_dialog)
        toolbar.addAction(open_format_action)

        convert_action = QAction("Convert to Format", self)
        convert_action.triggered.connect(self.convert_to_format)
        toolbar.addAction(convert_action)

        self.setStyleSheet("QToolBar { background: #333; border: none; }"
                           "QToolBar QToolButton { background: #444; color: white; }"
                           "QToolBar QToolButton:hover { background: #555; }")

        self.image = None

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.bmp)")
        if file_path:
            self.image = cv2.imread(file_path)
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.display_image(self.image)

    def load_format_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open IFS Image", "", "IFS Images (*.ifs)")
        if file_path:
            self.load_format(file_path)

    def load_format(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                data = file.read()
            password, ok = QInputDialog.getText(self, 'Password', 'Enter password for decryption (optional):', QLineEdit.Password)
            if ok:
                try:
                    image_data = convert_format_to_image(data, password if password else None)
                    self.image = image_data
                    self.display_image(self.image)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")

    def display_image(self, image):
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qimage).scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def convert_to_format(self):
        if self.image is not None:
            password, ok = QInputDialog.getText(self, 'Password', 'Enter password for encryption (optional):', QLineEdit.Password)
            if ok:
                delete_metadata = QMessageBox.question(self, 'Delete Metadata', 'Do you want to delete remaining metadata?', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes

                try:
                    data = convert_image_to_format(self.image, password if password else None, delete_metadata)
                    save_path, _ = QFileDialog.getSaveFileName(self, "Save Image Format", "", "Image Format (*.ifs)")
                    if save_path:
                        if not save_path.endswith('.ifs'):
                            save_path += '.ifs'
                        with open(save_path, 'wb') as file:
                            file.write(data)
                        QMessageBox.information(self, "Success", "Image successfully converted and saved!")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to convert image: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
