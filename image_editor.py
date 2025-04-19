#import cv2
import numpy as np
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import Qt

class ImageEditor(QLabel):
    def __init__(self, editor_lbl: QLabel, image_path: str):
        super().__init__(editor_lbl)
        self.editor_lbl = editor_lbl
        self.image_path = image_path
        self.image = cv2.imread(image_path)  # Original image
        self.lab_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2LAB)  # Convert to Lab color space
        self.selected_mask = None  # Mask for the selected region
        self.display_image()

        # Enable events
        self.editor_lbl.setFocusPolicy(Qt.StrongFocus)
        self.editor_lbl.setMouseTracking(True)
        self.editor_lbl.mousePressEvent = self.mouse_press_event
        self.editor_lbl.keyPressEvent = self.key_press_event

    def display_image(self, img=None):
        """Displays an image in editor_lbl, scaling it while maintaining aspect ratio."""
        image_to_display = img if img is not None else self.image

        if image_to_display is None:
            print("Error: Image not loaded.")
            return

        rgb_image = cv2.cvtColor(image_to_display, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb_image.shape
        bytes_per_line = 3 * width
        q_img = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        self.editor_lbl.setPixmap(pixmap)
        self.editor_lbl.setScaledContents(True)

    def map_click_to_image(self, x, y):
        """Maps the mouse click from editor_lbl coordinates to the actual image coordinates."""
        pixmap = self.editor_lbl.pixmap()
        if pixmap is None:
            return None, None

        lbl_w, lbl_h = self.editor_lbl.width(), self.editor_lbl.height()
        img_w, img_h = self.image.shape[1], self.image.shape[0]

        # Scale factors to map QLabel clicks to the actual image
        scale_x = img_w / lbl_w
        scale_y = img_h / lbl_h

        mapped_x = int(x * scale_x)
        mapped_y = int(y * scale_y)

        if mapped_x >= img_w or mapped_y >= img_h:
            return None, None

        return mapped_x, mapped_y

    def mouse_press_event(self, event):
        """Handles mouse click events to select a region by color."""
        lbl_x, lbl_y = event.pos().x(), event.pos().y()
        img_x, img_y = self.map_click_to_image(lbl_x, lbl_y)

        if img_x is None or img_y is None:
            print(f"Clicked outside image bounds: ({lbl_x}, {lbl_y})")
            return

        print(f"Clicked at: ({img_x}, {img_y}) - Selecting region by color")

        mask = self.flood_fill_lab(img_x, img_y)

        if mask is not None:
            self.selected_mask = mask
            self.overlay_mask(mask)  # Show selection before deletion
        else:
            print("Failed to generate mask.")

    def flood_fill_lab(self, x, y):
        """Performs improved flood fill using Lab color space for accurate selection."""
        h, w = self.image.shape[:2]
        mask = np.zeros((h, w), np.uint8)  # Initialize mask

        seed_color = self.lab_image[y, x].astype(np.int16)  # Get clicked color in Lab space
        print(f"Seed Color (Lab): {seed_color}")

        # Parameters
        tolerance = 20  # Adjust for better selection
        queue = [(x, y)]
        visited = set()

        while queue:
            cx, cy = queue.pop(0)
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))

            # Check bounds
            if cx < 0 or cy < 0 or cx >= w or cy >= h:
                continue

            # Get current pixel color in Lab space
            pixel_color = self.lab_image[cy, cx].astype(np.int16)

            # Compute Euclidean distance in Lab color space
            diff = np.linalg.norm(pixel_color - seed_color)

            if diff < tolerance:  # If within tolerance, mark as selected
                mask[cy, cx] = 255

                # Add 4-connected neighboring pixels
                queue.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])

        print(f"Generated mask shape: {mask.shape}")
        return mask

    def overlay_mask(self, mask):
        """Overlays the selected mask on the displayed image."""
        overlay = self.image.copy()
        overlay[mask == 255] = [0, 0, 255]  # Highlight selection in red (BGR)
        self.display_image(overlay)  # Show overlay before deletion

    def key_press_event(self, event):
        """Handles keyboard events for deletion and deselection."""
        if event.key() == Qt.Key_Delete:
            if self.selected_mask is None:
                print("No regions selected.")
                return

            self.image[self.selected_mask == 255] = 255  # Fill selected region with white
            print("Deleted selected region.")

            self.selected_mask = None
            self.display_image()  # Refresh image after deletion
            QApplication.processEvents()  # Immediate UI refresh

        elif event.key() == Qt.Key_Escape:
            """Deselects the current selection without deleting."""
            if self.selected_mask is not None:
                print("Deselected current selection.")
                self.selected_mask = None
                self.display_image()  # Remove overlay

    def enter_edit_mode(self):
        """Called when edit mode is entered."""
        print("Entered edit mode.")
        self.display_image()
        self.editor_lbl.setFocus()  # Ensure label captures keyboard events
