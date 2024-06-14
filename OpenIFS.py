import sys
import struct
import cv2
import numpy as np
import bz2
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QVBoxLayout, QWidget, QToolBar, QAction, QMessageBox, QInputDialog, QDialog, QDialogButtonBox, QComboBox, QVBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap, QImage, QPalette, QColor
from PyQt5.QtCore import Qt

# Delta encoding
def delta_encode(pixels):
    deltas = []
    prev_pixel = (0, 0, 0)
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
def convert_image_to_format(image, delete_metadata=False):
    # Convert image to numpy array
    pixels = np.array(image)
    height, width, channels = pixels.shape

    # Flatten the pixel array
    flat_pixels = pixels.reshape(-1, channels)

    # Delta encode the pixels
    encoded_pixels = delta_encode(flat_pixels)

    # Flatten the delta-encoded pixels
    flat_encoded_pixels = [value for pixel in encoded_pixels for value in pixel]

    # Compress the data using bz2
    compressed_data = bz2.compress(bytes(flat_encoded_pixels))

    # Create a header with metadata
    metadata = {
        "width": width,
        "height": height,
        "channels": channels,
        "delete_metadata": delete_metadata
    }
    metadata_bytes = json.dumps(metadata).encode()

    # Combine the header and the compressed data
    return metadata_bytes + b'---' + compressed_data

# Convert format to image
def convert_format_to_image(data):
    # Split the metadata and the compressed data
    metadata_bytes, compressed_data = data.split(b'---', 1)
    metadata = json.loads(metadata_bytes.decode())

    width = metadata["width"]
    height = metadata["height"]
    channels = metadata["channels"]
    delete_metadata = metadata["delete_metadata"]

    # Decompress the data using bz2
    flat_encoded_pixels = list(bz2.decompress(compressed_data))

    # Convert the flat list of encoded pixels to a list of tuples
    encoded_pixels = [tuple(flat_encoded_pixels[i:i+channels]) for i in range(0, len(flat_encoded_pixels), channels)]

    # Delta decode the pixels
    decoded_pixels = delta_decode(encoded_pixels)

    # Reshape the flat pixel array to the original shape
    pixels = np.array(decoded_pixels, dtype=np.uint8).reshape(height, width, channels)

    # Create an image from the pixel data
    return pixels

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Image")
        
        self.layout = QVBoxLayout(self)
        
        self.format_combo = QComboBox(self)
        self.format_combo.addItems(["png", "jpg", "jpeg", "jfif", "gif", "webp"])
        self.layout.addWidget(self.format_combo)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.layout.addWidget(self.button_box)
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def get_format(self):
        return self.format_combo.currentText()

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

        convert_action = QAction("Convert to IFS", self)
        convert_action.triggered.connect(self.convert_to_format)
        toolbar.addAction(convert_action)

        export_action = QAction("Export to Standard Format", self)
        export_action.triggered.connect(self.export_to_standard_format)
        toolbar.addAction(export_action)

        self.setStyleSheet("QToolBar { background: #333; border: none; }"
                           "QToolBar QToolButton { background: #444; color: white; border: none; }"
                           "QToolBar QToolButton:hover { background: #444; border: none; }")

        self.image = None

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.jfif *.gif *.webp *.bmp)")
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
            image_data = convert_format_to_image(data)
            self.image = image_data
            self.display_image(self.image)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")

    def display_image(self, image):
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qimage).scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def convert_to_format(self):
        if self.image is not None:
            delete_metadata, _ = QInputDialog.getItem(self, "Metadata", "Delete remaining metadata?", ["Yes", "No"], 0, False)
            delete_metadata = True if delete_metadata == "Yes" else False

            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "IFS Images (*.ifs)")
            if file_path:
                if not file_path.endswith('.ifs'):
                    file_path += '.ifs'
                try:
                    data = convert_image_to_format(self.image, delete_metadata)
                    with open(file_path, 'wb') as file:
                        file.write(data)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to convert image: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

    def export_to_standard_format(self):
        if self.image is not None:
            dialog = ExportDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                selected_format = dialog.get_format()
                file_path, _ = QFileDialog.getSaveFileName(self, "Export Image", "", f"Images (*.{selected_format})")
                if file_path:
                    if not file_path.endswith(f'.{selected_format}'):
                        file_path += f'.{selected_format}'
                    try:
                        cv2.imwrite(file_path, cv2.cvtColor(self.image, cv2.COLOR_RGB2BGR))
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to export image: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
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
