import sys
sys.stdout.reconfigure(encoding="utf-8")

import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import datetime

# ---------- thread-safe logging ----------

def log(message):
    """Safely updates the Tkinter UI from a background thread."""
    def update_ui():
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        status_box.insert(tk.END, f"[{timestamp}] {message}\n")
        status_box.see(tk.END)
        current_status.set(message)
    
    # root.after pushes the UI update back to the main thread safely
    root.after(0, update_ui)


# ---------- thread-safe history ----------

def add_history(query, source, limit):
    def update_ui():
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        history_table.insert(
            "",
            tk.END,
            values=(query, source, limit, timestamp)
        )
    root.after(0, update_ui)


# ---------- run scraper ----------

def run_scraper():
    query = query_entry.get().strip()
    limit = limit_entry.get().strip()
    source = source_dropdown.get()

    if not query:
        log("Enter a query")
        return

    if not limit.isdigit():
        log("Lead count must be a number")
        return

    start_button.config(state="disabled")

    log("Starting scraper...")
    log(f"Query: {query}")
    log(f"Source: {source}")
    log(f"Limit: {limit}")

    progress.start()

    def task():
        try:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-u",         
                    "app.py", 
                    "--query",
                    query,
                    "--limit",
                    limit,
                    "--source",
                    source
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    log(line.strip())

            process.stdout.close()
            process.wait()

            if process.returncode == 0:
                log("Lead collection finished successfully")
                add_history(query, source, limit)
            else:
                log(f"Scraper exited with error code {process.returncode}")

        except Exception as e:
            log(f"Execution error: {e}")

        finally:
            root.after(0, progress.stop)
            root.after(0, lambda: start_button.config(state="normal"))

    threading.Thread(target=task, daemon=True).start()


# ---------- UI Setup ----------

root = tk.Tk()
root.title("SHDZ Lead Finder Tool")
root.geometry("920x720")

title = ttk.Label(root, text="SHDZ Lead Finder Tool", font=("Arial", 18, "bold"))
title.pack(pady=15)


# ---------- current status ----------

current_status = tk.StringVar()
current_status.set("Idle")

status_label = ttk.Label(
    root,
    textvariable=current_status,
    font=("Arial", 11, "italic"),
    foreground="gray"
)
status_label.pack(pady=5)


# ---------- query inputs ----------

frame = ttk.LabelFrame(root, text="Search Parameters", padding=15)
frame.pack(pady=10, fill="x", padx=50)

ttk.Label(frame, text="Search Query:").grid(row=0, column=0, sticky="w", pady=5)

query_entry = ttk.Entry(frame, width=50)
query_entry.grid(row=0, column=1, pady=5, padx=10)
query_entry.insert(0, "clothing manufacturer Tirupur")


ttk.Label(frame, text="Lead Limit:").grid(row=1, column=0, sticky="w", pady=5)

limit_entry = ttk.Entry(frame, width=15)
limit_entry.grid(row=1, column=1, sticky="w", pady=5, padx=10)
limit_entry.insert(0, "100")


ttk.Label(frame, text="Data Source:").grid(row=2, column=0, sticky="w", pady=5)

source_dropdown = ttk.Combobox(
    frame,
    values=[
        "maps",
        "maps_grid",
        "supplier_search",
        "instagram",
        "linkedin",
        "all"
    ],
    width=30,
    state="readonly"
)
source_dropdown.grid(row=2, column=1, sticky="w", pady=5, padx=10)
source_dropdown.set("all")


# ---------- run button ----------

start_button = ttk.Button(
    root,
    text="Start Scraping",
    command=run_scraper,
    width=20
)
start_button.pack(pady=15)


# ---------- progress bar ----------

progress = ttk.Progressbar(
    root,
    length=500,
    mode="indeterminate"
)
progress.pack(pady=5)


# ---------- status log ----------

log_frame = ttk.LabelFrame(root, text="Live Output Log", padding=10)
log_frame.pack(pady=10, fill="both", expand=True, padx=20)

scrollbar = ttk.Scrollbar(log_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

status_box = tk.Text(
    log_frame,
    height=15,
    width=100,
    yscrollcommand=scrollbar.set,
    font=("Consolas", 9),
    bg="#f4f4f4"
)
status_box.pack(fill="both", expand=True)

scrollbar.config(command=status_box.yview)


# ---------- run history ----------

history_frame = ttk.LabelFrame(root, text="Run History", padding=10)
history_frame.pack(pady=10, fill="x", padx=20)

history_table = ttk.Treeview(
    history_frame,
    columns=("Query", "Source", "Leads", "Time"),
    show="headings",
    height=5
)

history_table.heading("Query", text="Query")
history_table.heading("Source", text="Source")
history_table.heading("Leads", text="Leads")
history_table.heading("Time", text="Time")

history_table.column("Query", width=350)
history_table.column("Source", width=150)
history_table.column("Leads", width=100, anchor="center")
history_table.column("Time", width=150, anchor="center")

history_table.pack(fill="x")


root.mainloop()