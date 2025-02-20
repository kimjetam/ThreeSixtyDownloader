import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import subprocess

def select_output_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        output_folder_var.set(folder_selected)

def on_url_change(*args):
    execute_button.config(state=tk.NORMAL if url_entry.get().strip() else tk.DISABLED)

def clear_output():
    output_text.config(state="normal")
    output_text.delete("1.0", tk.END)
    output_text.config(state="disabled")

def execute_logic():
    execute_button.config(state=tk.DISABLED)  # Disable execute button
    clear_output()  # Clear output before new execution

    def process():
        url = url_entry.get().strip()
        output_folder = output_folder_var.get().strip()
        filename = output_filename_var.get().strip()
        rep_idx_label = rep_idx_var.get()
        rep_idx = rep_idx_mapping[rep_idx_label]  # Convert label to index
        overwrite = overwrite_var.get()  # Get overwrite checkbox state

        if not filename.endswith(".mp4"):
            filename += ".mp4"

        output_file_path = os.path.join(output_folder, filename)
        mpd_path = os.path.join(output_folder, "index.mpd")

        # Check if the file exists and handle overwriting
        if os.path.exists(output_file_path) and not overwrite:
            append_output(f"File {filename} already exists. Overwrite is disabled.\n")
            execute_button.config(state=tk.NORMAL)
            return

        if url and output_folder and filename:
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
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
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

def append_output(text):
    output_text.config(state="normal")
    output_text.insert(tk.END, text)
    output_text.see(tk.END)
    output_text.config(state="disabled")

def show_completion_popup():
    messagebox.showinfo("Operation Completed", "The process has finished successfully.")
    execute_button.config(state=tk.NORMAL)

# Default values
default_folder = os.getcwd()
default_filename = "output.mp4"

# Rep Index Mapping
rep_idx_mapping = {
    "1080p": "0",
    "720p": "1",
    "360p": "2"
}

# Create main window
root = tk.Tk()
root.title("Three Sixty Downloader")
root.geometry("900x700")
root.resizable(True, True)  # Allow resizing in both directions

# URL Input
tk.Label(root, text="Input URL:").pack(pady=5)
url_var = tk.StringVar()
url_var.trace_add("write", on_url_change)
url_entry = tk.Entry(root, width=100, textvariable=url_var)
url_entry.pack(pady=5)

# Output Folder Selection
output_folder_var = tk.StringVar(value=default_folder)
tk.Label(root, text="Output Folder:").pack(pady=5)
output_folder_entry = tk.Entry(root, textvariable=output_folder_var, width=100, state="readonly")
output_folder_entry.pack(pady=5)
tk.Button(root, text="Browse", command=select_output_folder).pack(pady=5)

# Output Filename Input
output_filename_var = tk.StringVar(value=default_filename)
tk.Label(root, text="Output Filename:").pack(pady=5)
output_filename_entry = tk.Entry(root, textvariable=output_filename_var, width=100)
output_filename_entry.pack(pady=5)

# Rep Index Dropdown
tk.Label(root, text="Select Video Quality:").pack(pady=5)
rep_idx_var = tk.StringVar(value="360p")  # Default value
rep_idx_dropdown = tk.OptionMenu(root, rep_idx_var, *rep_idx_mapping.keys())
rep_idx_dropdown.pack(pady=5)

# Overwrite Checkbox
overwrite_var = tk.BooleanVar(value=False)
overwrite_checkbox = tk.Checkbutton(root, text="Overwrite Existing Video File", variable=overwrite_var)
overwrite_checkbox.pack(pady=5)

# Execute Button (Initially Disabled)
execute_button = tk.Button(root, text="Execute", command=execute_logic, state=tk.DISABLED)
execute_button.pack(pady=5)

# Output Log Area
tk.Label(root, text="Output Log:").pack(pady=5)
output_frame = tk.Frame(root)
output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

output_text = tk.Text(output_frame, height=8, wrap=tk.WORD, state="disabled")
output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(output_frame, command=output_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
output_text.config(yscrollcommand=scrollbar.set)

# Clear Output Button
clear_button = tk.Button(root, text="Clear Output", command=clear_output)
clear_button.pack(pady=5)

root.mainloop()
