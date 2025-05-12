#GUI
import os
import glob
import cv2
from defisheye import Defisheye
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, time, sys

# Defisheye settings
dtype = 'linear'
format = 'circular'
fov = 180
pfov = 120

# Function to process one image side
def process_side(image_half, output_path):
    cv2.imwrite(output_path, image_half)
    obj = Defisheye(output_path, dtype=dtype, format=format, fov=fov, pfov=pfov)
    obj.convert(outfile=output_path)

# Function to process one image
def process_image(entry, progress_callback):
    image = cv2.imread(entry)
    if image is None:
        print(f"Failed to read: {entry}")
        return

    height, width, _ = image.shape
    mid = width // 2
    left_image = image[:, :mid]
    right_image = image[:, mid:]

    filepath, filename = os.path.split(entry)
    base, ext = os.path.splitext(filename)

    output_left = os.path.join(filepath, f"left_{base}{ext}")
    output_right = os.path.join(filepath, f"right_{base}{ext}")

    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(process_side, left_image, output_left)
        executor.submit(process_side, right_image, output_right)

    # Notify GUI to update progress
    progress_callback()

# GUI setup
class App:
    def __init__(self, root):
        self.root = root
        root.title("Undistort Sensor Images")

        self.label = tk.Label(root, text="Select a folder with .png images:")
        self.label.pack(pady=10)

        self.button = tk.Button(root, text="Choose Directory", command=self.start_processing)
        self.button.pack(pady=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=20)

        self.status = tk.Label(root, text="")
        self.status.pack()

    def start_processing(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        entries = glob.glob(os.path.join(folder, "*.png"))
        if not entries:
            messagebox.showerror("No Images", "No .png files found in the selected directory.")
            return

        self.progress["maximum"] = len(entries)
        self.progress["value"] = 0
        self.status.config(text="Processing...")

        # Run processing in a background thread
        threading.Thread(target=self.process_all_images, args=(entries,)).start() 

    def process_all_images(self, entries):
        total = len(entries)
        self.progress["maximum"] = total
        completed = 0
    
        def update_progress(future):
            nonlocal completed
            completed += 1
            self.progress["value"] = completed
            self.root.update_idletasks()
    
            if completed == total:
                self.status.config(text="Done!")
    
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            for entry in entries:
                future = executor.submit(process_image, entry, lambda: None)
                future.add_done_callback(update_progress)

        self.status.config(text="Done!")

# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
