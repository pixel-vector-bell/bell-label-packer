#!/usr/bin/env python3
"""
Bell Flyer-Box Label Packer  (GUI + CLI)

Packs single-school 10-up "Picture Day Flyers" label sheets down to only the
labels actually needed, filling sheets continuously to eliminate waste.

Rule:  3 labels per box, 1 box = up to 1000 flyers
       labels_needed = 3 * ceil(flyers / 1000)

Filename must encode the flyer count as  ..._<N>_Flyers.pdf
  e.g.  Teton_HS_Labels_2000_Flyers.pdf  -> 2000 flyers -> 2 boxes -> 6 labels

GUI mode (double-click the .exe): pick a folder of PDFs, click Pack, get one
packed PDF beside them.  CLI mode:  label_packer.py INPUT_DIR [OUTPUT_PDF]
"""
import sys, os, re, math, glob
import fitz  # PyMuPDF

APP_TITLE = "Bell Flyer-Box Label Packer"

# ---- 10-up template geometry (measured from the real Bell template) ----
PAGE_W, PAGE_H = 612.0, 792.0
COLS, ROWS = 2, 5
COL_X = [(10.0, 296.0), (316.0, 602.0)]
ROW_Y = [(25.0, 167.0), (169.0, 311.0), (313.0, 455.0),
         (457.0, 599.0), (601.0, 743.0)]
SLOTS = [fitz.Rect(cx0, ry0, cx1, ry1)
         for (ry0, ry1) in ROW_Y for (cx0, cx1) in COL_X]

FLYERS_PER_BOX = 1000
LABELS_PER_BOX = 3


def labels_needed(flyers: int) -> int:
    return LABELS_PER_BOX * math.ceil(flyers / FLYERS_PER_BOX)


def parse_count(path: str):
    m = re.search(r'_(\d+)_Flyers', os.path.basename(path), re.IGNORECASE)
    return int(m.group(1)) if m else None


def collect_labels(input_dir, log=print):
    entries = []
    files = sorted(glob.glob(os.path.join(input_dir, "*.pdf")))
    for f in files:
        if os.path.basename(f).lower().startswith("packed_"):
            continue  # never re-pack our own output
        cnt = parse_count(f)
        if cnt is None:
            log(f"  ! skipped (no _<N>_Flyers in name): {os.path.basename(f)}")
            continue
        doc = fitz.open(f)
        need = labels_needed(cnt)
        cell = SLOTS[0]  # top-left cell of the source sheet
        for _ in range(need):
            entries.append((cell, doc, 0))
        log(f"  {os.path.basename(f):50s} flyers={cnt:>5}  boxes={math.ceil(cnt/1000)}  labels={need}")
    return entries, files


def pack(entries, output_pdf):
    out = fitz.open()
    page = None
    placed = 0
    for cell, src, spage in entries:
        slot_idx = placed % len(SLOTS)
        if slot_idx == 0:
            page = out.new_page(width=PAGE_W, height=PAGE_H)
        page.show_pdf_page(SLOTS[slot_idx], src, spage, clip=cell)
        placed += 1
    out.save(output_pdf, garbage=4, deflate=True)
    out.close()
    return placed


def run(input_dir, output_pdf=None, log=print):
    if not output_pdf:
        output_pdf = os.path.join(input_dir, "Packed_Box_Labels.pdf")
    log(f"Scanning: {input_dir}")
    entries, files = collect_labels(input_dir, log)
    if not entries:
        log("No labels found. Make sure filenames contain _<N>_Flyers and end in .pdf")
        return None, 0, 0
    total = len(entries)
    sheets = math.ceil(total / len(SLOTS))
    placed = pack(entries, output_pdf)
    waste = sheets * len(SLOTS) - placed
    log("")
    log(f"Packed {placed} labels onto {sheets} sheet(s).  Empty slots on last sheet: {waste}")
    log(f"Saved: {output_pdf}")
    return output_pdf, placed, sheets


# ------------------------------ GUI ------------------------------
def launch_gui():
    import tkinter as tk
    from tkinter import filedialog, scrolledtext

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("680x480")

    frm = tk.Frame(root, padx=12, pady=12)
    frm.pack(fill="both", expand=True)

    tk.Label(frm, text=APP_TITLE, font=("Segoe UI", 15, "bold")).pack(anchor="w")
    tk.Label(frm, text="Pick a folder of *_<N>_Flyers.pdf label files. "
                       "A single packed PDF is written into that same folder.",
             fg="#444", wraplength=640, justify="left").pack(anchor="w", pady=(0, 10))

    path_var = tk.StringVar()
    row = tk.Frame(frm); row.pack(fill="x")
    tk.Entry(row, textvariable=path_var).pack(side="left", fill="x", expand=True)

    logbox = scrolledtext.ScrolledText(frm, height=16, font=("Consolas", 9))
    logbox.pack(fill="both", expand=True, pady=(10, 0))

    def log(msg=""):
        logbox.insert("end", str(msg) + "\n"); logbox.see("end"); root.update()

    def choose():
        d = filedialog.askdirectory(title="Choose folder of label PDFs")
        if d:
            path_var.set(d)

    def do_pack():
        d = path_var.get().strip()
        if not d or not os.path.isdir(d):
            log("Please choose a valid folder first."); return
        logbox.delete("1.0", "end")
        try:
            out, placed, sheets = run(d, log=log)
            if out:
                log("")
                log("DONE. Open the folder to print Packed_Box_Labels.pdf")
        except Exception as e:
            log(f"ERROR: {e}")

    tk.Button(row, text="Choose Folder...", command=choose).pack(side="left", padx=(8, 0))
    tk.Button(frm, text="Pack Labels", command=do_pack,
              bg="#1A2B8F", fg="white", font=("Segoe UI", 11, "bold"),
              padx=16, pady=6).pack(anchor="w", pady=(10, 0))

    root.mainloop()


def main():
    if len(sys.argv) >= 2:
        input_dir = sys.argv[1]
        output_pdf = sys.argv[2] if len(sys.argv) > 2 else None
        run(input_dir, output_pdf)
    else:
        launch_gui()


if __name__ == "__main__":
    main()
