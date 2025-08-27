# main.py
# CSV Keyword Filter GUI
# Works as .py or .pyw (no console). Provides Start button and Results (save/open) options.

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def read_keywords(path, case_sensitive=False):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        kws = [line.strip() for line in f if line.strip()]
    if not case_sensitive:
        kws = [k.lower() for k in kws]
    return kws

def filter_lines(csv_file, keywords_file, output_file, case_sensitive=False):
    """
    Streams the CSV file line-by-line and writes any line containing
    any keyword to the output file. Returns the number of matched lines.
    """
    keywords = read_keywords(keywords_file, case_sensitive=case_sensitive)
    if not keywords:
        raise ValueError("No keywords found in the keywords file. Add one per line.")

    matches = 0
    with open(csv_file, "r", encoding="utf-8", errors="replace") as fin, \
         open(output_file, "w", encoding="utf-8") as fout:
        for line in fin:
            hay = line if case_sensitive else line.lower()
            if any(k in hay for k in keywords):
                fout.write(line)
                matches += 1
    return matches

def open_in_explorer(path):
    try:
        if sys.platform.startswith("darwin"):
            import subprocess
            subprocess.call(["open", path])
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            import subprocess
            subprocess.call(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Open File", f"Couldn't open file:\n{e}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CSV Keyword Filter")
        self.geometry("700x260")
        self.minsize(620, 240)

        # Variables
        self.csv_path = tk.StringVar()
        self.keywords_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.case_insensitive = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Ready. Select files, then press Start.")

        # Layout
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)

        # Row 0: CSV
        ttk.Label(frm, text="CSV file:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.csv_path).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Browse…", command=self._browse_csv).grid(row=0, column=2, **pad)

        # Row 1: Keywords
        ttk.Label(frm, text="Keywords file (.txt):").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.keywords_path).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Browse…", command=self._browse_keywords).grid(row=1, column=2, **pad)

        # Row 2: Output
        ttk.Label(frm, text="Results file:").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.output_path).grid(row=2, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Choose…", command=self._choose_output).grid(row=2, column=2, **pad)

        # Row 3: Options
        ttk.Checkbutton(
            frm,
            text="Case-insensitive search",
            variable=self.case_insensitive
        ).grid(row=3, column=1, sticky="w", **pad)

        # Row 4: Buttons
        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=3, sticky="ew", **pad)
        self.start_btn = ttk.Button(btns, text="Start", command=self._start)
        self.start_btn.pack(side="left")
        self.open_btn = ttk.Button(btns, text="Open Results", command=self._open_results, state="disabled")
        self.open_btn.pack(side="left", padx=8)
        ttk.Button(btns, text="Quit", command=self.destroy).pack(side="right")

        # Row 5: Progress + Status
        self.progress = ttk.Progressbar(frm, mode="indeterminate")
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", **pad)
        ttk.Label(frm, textvariable=self.status_text).grid(row=6, column=0, columnspan=3, sticky="w", **pad)

        frm.columnconfigure(1, weight=1)

    def _browse_csv(self):
        fn = filedialog.askopenfilename(
            title="Select CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if fn:
            self.csv_path.set(fn)
            # If results path empty, default to results.txt next to CSV
            if not self.output_path.get():
                self.output_path.set(os.path.join(os.path.dirname(fn), "results.txt"))

    def _browse_keywords(self):
        fn = filedialog.askopenfilename(
            title="Select keywords .txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if fn:
            self.keywords_path.set(fn)

    def _choose_output(self):
        initial = self.output_path.get() or "results.txt"
        fn = filedialog.asksaveasfilename(
            title="Save results as…",
            defaultextension=".txt",
            initialfile=os.path.basename(initial),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if fn:
            self.output_path.set(fn)

    def _validate_inputs(self):
        if not self.csv_path.get():
            raise ValueError("Please choose a CSV file.")
        if not self.keywords_path.get():
            raise ValueError("Please choose a keywords .txt file.")
        if not self.output_path.get():
            raise ValueError("Please choose where to save the results file.")

        # Basic existence checks
        if not os.path.exists(self.csv_path.get()):
            raise FileNotFoundError(f"CSV not found:\n{self.csv_path.get()}")
        if not os.path.exists(self.keywords_path.get()):
            raise FileNotFoundError(f"Keywords file not found:\n{self.keywords_path.get()}")

    def _start(self):
        try:
            self._validate_inputs()
        except Exception as e:
            messagebox.showerror("Input error", str(e))
            return

        self.status_text.set("Working…")
        self.progress.start(12)
        self.start_btn.config(state="disabled")
        self.open_btn.config(state="disabled")

        csv_file = self.csv_path.get()
        keywords_file = self.keywords_path.get()
        output_file = self.output_path.get()
        case_sensitive = not self.case_insensitive.get()

        def worker():
            try:
                count = filter_lines(csv_file, keywords_file, output_file, case_sensitive=case_sensitive)
                self.after(0, lambda: self._finish_ok(count, output_file))
            except Exception as e:
                self.after(0, lambda: self._finish_err(e))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_ok(self, count, output_file):
        self.progress.stop()
        self.status_text.set(f"Done. {count} matching line(s) saved to: {output_file}")
        self.start_btn.config(state="normal")
        self.open_btn.config(state="normal")
        messagebox.showinfo("Success", f"Filtering complete.\n\nMatches: {count}\nSaved to:\n{output_file}")

    def _finish_err(self, err):
        self.progress.stop()
        self.start_btn.config(state="normal")
        self.open_btn.config(state="disabled")
        self.status_text.set("Error. See details.")
        messagebox.showerror("Error", str(err))

    def _open_results(self):
        path = self.output_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Open Results", "Results file not found yet.")
            return
        open_in_explorer(path)

if __name__ == "__main__":
    app = App()
    app.mainloop()
