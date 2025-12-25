import time
import os
from PIL import Image

def show_question_image(image_path, window_name="Question Image", duration=15):
    """
    Safely display an image on macOS without using OpenCV GUI.
    Uses PIL's Image.show() which delegates to the OS default viewer,
    avoiding OpenCV's imshow crashes in non-main threads.
    """
    try:
        img = Image.open(image_path)
    except Exception:
        print("❌ Could not load image:", image_path)
        return

    # Show in the OS default image viewer (non-blocking)
    try:
        img.show(title=window_name)
        print(f"🖼️ Showing image: {image_path} (close the viewer when done)")
    except Exception as e:
        print("❌ Could not display image:", e)
        return

    # Optional: keep a small sleep to mirror previous behavior
    start = time.time()
    while time.time() - start < duration:
        time.sleep(0.25)
