import sys
import subprocess
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from image_editor import ImageEditor  # Import ImageEditor

class BackgroundRemovalThread(QThread):
    """Thread for processing multiple images to keep UI responsive."""
    progress_signal = pyqtSignal(int)

    def __init__(self, images):
        super().__init__()
        self.images = images

    def run(self):
        total_images = len(self.images)
        for index, img_path in enumerate(self.images):
            subprocess.run(["python", "remove_background.py", img_path])
            progress = int(((index + 1) / total_images) * 100)
            self.progress_signal.emit(progress)  # Emit progress update
        self.progress_signal.emit(100)  # Ensure progress is 100% at the end

class RackDetectionApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(RackDetectionApp, self).__init__()
        uic.loadUi('remove_background.ui', self)  # Load UI file

        self.selected_images = []  # Store selected image paths
        self.output_images = {}  # Store output image paths
        self.editor = None  # Image editor instance
        self.thread = None  # Background processing thread

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(300, 400, 400, 25)  # Adjust position and size
        self.progress_bar.setVisible(False)  # Hide initially

        # Connect label click events
        self.browse_lbl.mousePressEvent = lambda event: self.browse_images(event)
        self.remove_bg_lbl.mousePressEvent = lambda event: self.run_background_removal(event)
        self.view_lbl.mousePressEvent = lambda event: self.display_images(event)
        self.reset_lbl.mousePressEvent = lambda event: self.reset_images(event)
        self.edit_mode_lbl.mousePressEvent = lambda event: self.enter_edit_mode(event)

    def browse_images(self, event):
        """Opens file dialog to browse multiple images and stores the paths in a list."""
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Images", "",
                                                     "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
                                                     options=options)
        if file_paths:
            self.selected_images = file_paths  # Store image paths
            print("Selected Images:", self.selected_images)
            self.path_lbl.setText("; ".join(file_paths))  # Display selected paths

    def run_background_removal(self, event):
        """Runs another Python script for each selected image with a progress bar."""
        if not self.selected_images:
            print("Please select images first.")
            return

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # Create and start the processing thread
        self.thread = BackgroundRemovalThread(self.selected_images)
        self.thread.progress_signal.connect(self.progress_bar.setValue)
        self.thread.finished.connect(self.on_processing_complete)
        self.thread.start()

    def on_processing_complete(self):
        """Hides the progress bar when processing is complete."""
        self.progress_bar.setVisible(False)
        print("Processing complete!")

    def enter_edit_mode(self, event):
        """Clears input/output labels and enters edit mode for the first output image."""
        self.input_image_lbl.clear()
        self.output_lbl.clear()

        if not self.output_images:
            print("No output images available for editing.")
            return

        first_output_image = list(self.output_images.values())[0]

        # Initialize the editor
        self.editor = ImageEditor(self.editor_lbl, first_output_image)
        self.editor.enter_edit_mode()

    def display_images(self, event):
        """Displays the first selected input image and its processed output image."""
        if not self.selected_images:
            print("No images selected to display.")
            return

        # Load and display input images
        input_pixmap = QPixmap(self.selected_images[0])  # Show the first image
        self.input_image_lbl.setPixmap(input_pixmap)
        self.input_image_lbl.setScaledContents(True)

        # Load corresponding output images
        self.output_images.clear()
        for img_path in self.selected_images:
            output_image_name = img_path.split("/")[-1]  # Extract filename
            output_image_path = f"output_images/{output_image_name}"  # Assuming output is saved in 'output_images/'
            self.output_images[img_path] = output_image_path

        output_pixmap = QPixmap(self.output_images[self.selected_images[0]])
        if output_pixmap.isNull():
            print("Output image not found.")
        else:
            self.output_lbl.setPixmap(output_pixmap)
            self.output_lbl.setScaledContents(True)
            self.output_lbl.setStyleSheet("background-color: black;")
        print(f"Displayed input image: {self.selected_images[0]}")
        print(f"Displayed output image: {self.output_images[self.selected_images[0]]}")

    def reset_images(self, event):
        """Clears images from input_image_lbl and output_lbl."""
        self.input_image_lbl.clear()
        self.output_lbl.clear()
        self.selected_images = []  # Reset selected images
        self.output_images.clear()
        self.output_lbl.setStyleSheet("background-color: transparent;")
        print("Images reset successfully.")
        self.path_lbl.setText("...")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = RackDetectionApp()
    main_window.show()
    sys.exit(app.exec_())
