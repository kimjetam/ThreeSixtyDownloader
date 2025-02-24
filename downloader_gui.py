import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import subprocess
from scraper import get_element_text  # Import function from scraper.py
import json

CONFIG_FILE = "config.json"

def save_output_folder():
    """Save the current output folder to a config file."""
    config = {"output_folder": output_folder_var.get()}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
    append_output("Output folder saved!\n")

def load_output_folder():
    """Load the last saved output folder from a config file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            output_folder_var.set(config.get("output_folder", default_folder))
        except Exception as e:
            append_output(f"Error loading config: {str(e)}\n")

def select_output_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        output_folder_var.set(folder_selected)

def on_url_change(*args):
    execute_button.config(state=tk.NORMAL if url_entry.get().strip() else tk.DISABLED)
    fetch_button.config(state=tk.NORMAL if url_entry.get().strip() else tk.DISABLED)

def clear_output():
    output_text.config(state="normal")
    output_text.delete("1.0", tk.END)
    output_text.config(state="disabled")

def append_output(text):
    output_text.config(state="normal")
    output_text.insert(tk.END, text)
    output_text.see(tk.END)
    output_text.config(state="disabled")

def show_completion_popup():
    messagebox.showinfo("Operation Completed", "The process has finished successfully.")
    execute_button.config(state=tk.NORMAL)

def fetch_title():
    fetch_button.config(state=tk.DISABLED)
    execute_button.config(state=tk.DISABLED)
    append_output(f"Fetching title...\n")

    def process():
        url = url_var.get().strip()
        if not url:
            append_output("Error: URL is empty.\n")
            fetch_button.config(state=tk.NORMAL)
            return

        try:
            title = get_element_text(url, "h1")
            output_filename_var.set(title + ".mp4")
            append_output(f"Fetched Title: {title}\n")
        except Exception as e:
            append_output(f"Error: {str(e)}\n")

        fetch_button.config(state=tk.NORMAL)
        execute_button.config(state=tk.NORMAL)

    threading.Thread(target=process, daemon=True).start()

def execute_logic():
    execute_button.config(state=tk.DISABLED)
    clear_output()

    def process():
        url = url_entry.get().strip()
        output_folder = output_folder_var.get().strip()
        filename = output_filename_var.get().strip()
        rep_idx_label = rep_idx_var.get()
        rep_idx = rep_idx_mapping[rep_idx_label]
        overwrite = overwrite_var.get()

        if not filename.endswith(".mp4"):
            filename += ".mp4"

        output_file_path = os.path.join(output_folder, filename)
        mpd_path = os.path.join(output_folder, "index.mpd")

        if os.path.exists(output_file_path) and not overwrite:
            append_output(f"File {filename} already exists. Overwrite is disabled.\n")
            execute_button.config(state=tk.NORMAL)
            return

        append_output(f"Running script with URL: {url}\n")
        try:
            process = subprocess.Popen(
                ["python", "mpd_builder.py", "--url", url, "--output_dir", output_folder],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )

            for line in iter(process.stdout.readline, ""):
                append_output(line)
            process.wait()
            
            if process.returncode != 0:
                append_output(f"mpd_builder failed with exit code {process.returncode}\n")
                execute_button.config(state=tk.NORMAL)
                return
            
            process2 = subprocess.Popen(
                ["python", "video_builder.py", "--rep_idx", rep_idx, "--output_dir", output_folder, "--mpd_path", mpd_path, "--filename", filename, "--auto_overwrite"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )

            for line in iter(process2.stdout.readline, ""):
                append_output(line)
            
            process2.wait()

            if process2.returncode != 0:
                append_output(f"video_builder failed with exit code {process2.returncode}\n")
                execute_button.config(state=tk.NORMAL)
            else:
                root.after(0, show_completion_popup)
        except Exception as e:
            append_output(f"Execution failed: {str(e)}\n")
            execute_button.config(state=tk.NORMAL)

    threading.Thread(target=process, daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("Three Sixty Downloader")
root.geometry("900x500")

# Variables
default_folder = os.getcwd()
default_filename = "output.mp4"
rep_idx_mapping = {"1080p": "0", "720p": "1", "360p": "2"}
url_var = tk.StringVar()
url_var.trace_add("write", on_url_change)
output_folder_var = tk.StringVar(value=default_folder)
output_filename_var = tk.StringVar(value=default_filename)
rep_idx_var = tk.StringVar(value="360p")
overwrite_var = tk.BooleanVar(value=False)

# Layout Frames
left_frame = tk.Frame(root, padx=10, pady=10)
left_frame.grid(row=0, column=0, sticky="nsew")
right_frame = tk.Frame(root, padx=10, pady=10)
right_frame.grid(row=0, column=1, sticky="nsew")
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

# Left Panel - Inputs
tk.Label(left_frame, text="Input URL:").pack(anchor="w")
url_entry = tk.Entry(left_frame, textvariable=url_var, width=50)
url_entry.pack(fill="x", pady=2)
fetch_button = tk.Button(left_frame, text="Fetch Title", command=fetch_title, state=tk.DISABLED)
fetch_button.pack(pady=2)

tk.Label(left_frame, text="Output Folder:").pack(anchor="w")
output_folder_entry = tk.Entry(left_frame, textvariable=output_folder_var, width=50, state="readonly")
output_folder_entry.pack(fill="x", pady=2)

# Create a frame to hold both buttons
button_frame = tk.Frame(left_frame)
button_frame.pack(fill="x", pady=2)

# Add buttons inside the frame
tk.Button(button_frame, text="Browse", command=select_output_folder).pack(side="left", padx=2)
tk.Button(button_frame, text="Save", command=save_output_folder).pack(side="left", padx=2)

tk.Label(left_frame, text="Output Filename:").pack(anchor="w")
output_filename_entry = tk.Entry(left_frame, textvariable=output_filename_var, width=50)
output_filename_entry.pack(fill="x", pady=2)

tk.Label(left_frame, text="Select Video Quality:").pack(anchor="w")
rep_idx_dropdown = tk.OptionMenu(left_frame, rep_idx_var, *rep_idx_mapping.keys())
rep_idx_dropdown.pack(fill="x", pady=2)

overwrite_checkbox = tk.Checkbutton(left_frame, text="Overwrite Existing Video File", variable=overwrite_var)
overwrite_checkbox.pack()

execute_button = tk.Button(left_frame, text="Download", command=execute_logic, state=tk.DISABLED)
execute_button.pack(pady=5)

# Right Panel - Output Log
tk.Label(right_frame, text="Output Log:").pack()

output_frame = tk.Frame(right_frame)
output_frame.pack(fill="both", expand=True)

output_text = tk.Text(output_frame, wrap=tk.WORD, state="disabled", height=15)
output_text.grid(row=0, column=0, sticky="nsew")

scrollbar = tk.Scrollbar(output_frame, command=output_text.yview)
scrollbar.grid(row=0, column=1, sticky="ns")

output_text.config(yscrollcommand=scrollbar.set)

output_frame.grid_columnconfigure(0, weight=1)
output_frame.grid_rowconfigure(0, weight=1)

clear_button = tk.Button(right_frame, text="Clear Output", command=clear_output)
clear_button.pack(pady=5)
load_output_folder()
root.mainloop()
