#!/usr/bin/env python3
"""
Bell Flyer-Box Label Packer  (GUI + CLI)

Packs single-school 10-up "Picture Day Flyers" label sheets down to only the
labels actually needed, filling sheets continuously to eliminate waste.

Rule:  3 labels per box, 1 box = up to 1000 flyers
       labels_needed = 3 * ceil(flyers / 1000)

Filename must encode the flyer count as  ..._<N>_Flyers.pdf  (space or underscore)
  e.g.  "Draper ES (Canyons) Labels 350 Flyers.pdf" -> 350 flyers -> 1 box -> 3 labels

GUI mode (double-click the .exe): choose individual PDF files, see a preview of
the first packed page, then Pack Labels & Save File (choose where + the name).
CLI mode:  label_packer.py INPUT_DIR_OR_FILES... [--out OUTPUT_PDF]
"""
import sys, os, re, math, glob
import fitz  # PyMuPDF

APP_TITLE = "Bell Flyer-Box Label Packer"
VERSION = "1.0.2"          # ← bump this one line for each release; shown bottom-right

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
PREVIEW_DPI = 72           # low DPI = fast preview render


def labels_needed(flyers: int) -> int:
    return LABELS_PER_BOX * math.ceil(flyers / FLYERS_PER_BOX)


def parse_count(path: str):
    # Accept space OR underscore around the number, e.g.
    #   "Teton HS Labels 2000 Flyers.pdf"  or  "Teton_HS_Labels_2000_Flyers.pdf"
    m = re.search(r'[ _](\d+)[ _]*Flyers', os.path.basename(path), re.IGNORECASE)
    return int(m.group(1)) if m else None


def sort_key(path: str):
    """Case-insensitive alphabetical sort by filename (so packing order is A→Z)."""
    return os.path.basename(path).lower()


def collect_labels(files, log=print):
    """Expand a list of PDF file paths into per-label entries, in the order given.
    Caller is responsible for sorting `files` alphabetically first."""
    entries = []
    used = []
    for f in files:
        base = os.path.basename(f)
        if base.lower().startswith("packed_"):
            continue  # never re-pack our own output
        cnt = parse_count(f)
        if cnt is None:
            log(f"  ! skipped (no '<N> Flyers' in name): {base}")
            continue
        doc = fitz.open(f)
        need = labels_needed(cnt)
        cell = SLOTS[0]  # top-left cell of the source sheet
        for _ in range(need):
            entries.append((cell, doc, 0))
        used.append(f)
        log(f"  {base:50s} flyers={cnt:>5}  boxes={math.ceil(cnt/1000)}  labels={need}")
    return entries, used


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


def build_first_page(entries):
    """Build ONLY the first packed sheet as an in-memory fitz doc (for preview)."""
    out = fitz.open()
    page = out.new_page(width=PAGE_W, height=PAGE_H)
    for slot_idx in range(min(len(SLOTS), len(entries))):
        cell, src, spage = entries[slot_idx]
        page.show_pdf_page(SLOTS[slot_idx], src, spage, clip=cell)
    return out


def run(files, output_pdf, log=print):
    """Pack the given (already-sorted) list of files to output_pdf."""
    log(f"Packing {len(files)} file(s)...")
    entries, used = collect_labels(files, log)
    if not entries:
        log("No labels found. Make sure filenames contain '<N> Flyers' and end in .pdf")
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
    from tkinter import filedialog, scrolledtext, messagebox

    root = tk.Tk()
    root.title(f"{APP_TITLE} — Version {VERSION}")
    root.geometry("1040x620")
    root.minsize(900, 540)

    # State: the alphabetically-sorted list of chosen files.
    chosen_files = []

    # ── Outer layout: content frame (top) + version strip (bottom) ──────────
    outer = tk.Frame(root)
    outer.pack(fill="both", expand=True)

    frm = tk.Frame(outer, padx=12, pady=10)
    frm.pack(fill="both", expand=True)

    # Header
    tk.Label(frm, text=APP_TITLE, font=("Segoe UI", 15, "bold")).pack(anchor="w")
    tk.Label(
        frm,
        text=("Select the label files you want to pack. Name each file as "
              "\"[School Name] Labels [# of flyers] Flyers\" — for example: "
              "Draper ES (Canyons) Labels 350 Flyers. When all files are loaded, "
              "click \"Pack Labels & Save File\" in the bottom-left corner."),
        fg="#444", wraplength=1000, justify="left",
    ).pack(anchor="w", pady=(0, 10))

    # ── Two-pane body: left = controls + file list + log, right = preview ───
    body = tk.Frame(frm)
    body.pack(fill="both", expand=True)

    left = tk.Frame(body)
    left.pack(side="left", fill="both", expand=True)

    right = tk.Frame(body, width=430)
    right.pack(side="right", fill="both", expand=False)
    right.pack_propagate(False)

    # --- Left: choose-files row ---
    row = tk.Frame(left); row.pack(fill="x")
    count_var = tk.StringVar(value="No files selected")
    tk.Label(row, textvariable=count_var, fg="#333").pack(side="left")

    # --- Left: selected-file list ---
    tk.Label(left, text="Files to pack (alphabetical order):",
             font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 0))
    filelist = tk.Listbox(left, height=7, font=("Consolas", 9))
    filelist.pack(fill="x")

    # --- Left: log ---
    tk.Label(left, text="Log:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 0))
    logbox = scrolledtext.ScrolledText(left, height=8, font=("Consolas", 9))
    logbox.pack(fill="both", expand=True)

    def log(msg=""):
        logbox.insert("end", str(msg) + "\n"); logbox.see("end"); root.update()

    # --- Right: preview pane ---
    tk.Label(right, text="Preview — first page (fit to view):",
             font=("Segoe UI", 9, "bold")).pack(anchor="w")
    preview_canvas = tk.Canvas(right, bg="#e9e9e9", highlightthickness=1,
                               highlightbackground="#bbb")
    preview_canvas.pack(fill="both", expand=True, pady=(4, 0))
    # Keep a reference to the PhotoImage so it isn't garbage-collected.
    _preview_ref = {}
    _preview_state = {"resize_job": ""}

    def render_preview():
        """Render the first packed page scaled to FIT the preview canvas,
        preserving the page's aspect ratio (US Letter 612x792)."""
        preview_canvas.delete("all")
        cw = preview_canvas.winfo_width()
        ch = preview_canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            # Canvas not laid out yet — try again shortly.
            root.after(120, render_preview)
            return
        if not chosen_files:
            preview_canvas.create_text(cw // 2, ch // 2,
                                       text="(select files to preview)",
                                       fill="#888", font=("Segoe UI", 10))
            return
        try:
            entries, _ = collect_labels(chosen_files, log=lambda *a, **k: None)
            if not entries:
                preview_canvas.create_text(cw // 2, ch // 2,
                                           text="(no valid label files)",
                                           fill="#888", font=("Segoe UI", 10))
                return
            doc = build_first_page(entries)
            page = doc[0]
            # Compute a zoom that fits the page inside the canvas (with a small
            # margin), keeping aspect ratio. 72 pt = 1 in, so zoom=1 → 72 dpi.
            margin = 12
            avail_w = max(1, cw - margin)
            avail_h = max(1, ch - margin)
            zoom = min(avail_w / page.rect.width, avail_h / page.rect.height)
            zoom = max(0.05, zoom)  # guard against zero/negative
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            doc.close()
            img = tk.PhotoImage(data=pix.tobytes("ppm"))
            _preview_ref["img"] = img
            preview_canvas.create_image(cw // 2, ch // 2, image=img)
        except Exception as e:
            preview_canvas.create_text(cw // 2, ch // 2,
                                       text=f"(preview error: {e})",
                                       fill="#a00", font=("Segoe UI", 9))

    def _on_canvas_resize(event):
        # Debounce: re-fit the preview ~150ms after the last resize event so we
        # don't re-render on every intermediate pixel while dragging.
        if _preview_state["resize_job"]:
            root.after_cancel(_preview_state["resize_job"])
        _preview_state["resize_job"] = root.after(150, render_preview)

    preview_canvas.bind("<Configure>", _on_canvas_resize)

    def refresh_filelist():
        filelist.delete(0, "end")
        for f in chosen_files:
            filelist.insert("end", os.path.basename(f))
        n = len(chosen_files)
        count_var.set(f"{n} file{'s' if n != 1 else ''} selected"
                      if n else "No files selected")

    def choose():
        picked = filedialog.askopenfilenames(
            title="Choose label PDF files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not picked:
            return
        # Sort alphabetically (case-insensitive) so packing order is A→Z.
        chosen_files[:] = sorted(picked, key=sort_key)
        refresh_filelist()
        logbox.delete("1.0", "end")
        log(f"Loaded {len(chosen_files)} file(s), sorted alphabetically.")
        render_preview()

    def do_pack_and_save():
        if not chosen_files:
            messagebox.showinfo(APP_TITLE, "Please choose files first.")
            return
        out_path = filedialog.asksaveasfilename(
            title="Save packed labels as...",
            defaultextension=".pdf",
            initialfile="Packed_Box_Labels.pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not out_path:
            return  # user cancelled
        logbox.delete("1.0", "end")
        try:
            out, placed, sheets = run(chosen_files, out_path, log=log)
            if out:
                log("")
                log("DONE. You can open and print the saved PDF.")
                messagebox.showinfo(APP_TITLE,
                                    f"Packed {placed} labels onto {sheets} sheet(s).\n\nSaved:\n{out}")
        except Exception as e:
            log(f"ERROR: {e}")
            messagebox.showerror(APP_TITLE, f"Something went wrong:\n{e}")

    tk.Button(row, text="Choose Files...", command=choose).pack(side="right")

    # --- Bottom-left action button ---
    tk.Button(frm, text="Pack Labels & Save File", command=do_pack_and_save,
              bg="#1A2B8F", fg="white", font=("Segoe UI", 11, "bold"),
              padx=16, pady=6).pack(anchor="w", pady=(10, 0))

    # ── Version strip pinned to the bottom, text right-aligned, FIXED size ──
    # Fixed font size (does not scale when the window resizes) — matches all
    # other elements. Lives in the bottom-right corner.
    version_strip = tk.Frame(outer)
    version_strip.pack(side="bottom", fill="x")
    tk.Label(version_strip, text=f"Version {VERSION}", fg="#777",
             font=("Segoe UI", 9)).pack(side="right", padx=10, pady=(0, 6))

    refresh_filelist()
    # Render the empty-state preview once the canvas has a real size.
    root.after(200, render_preview)
    root.mainloop()


def _gather_cli_files(args):
    """Expand CLI args: a single directory → all *.pdf in it; else treat as files."""
    if len(args) == 1 and os.path.isdir(args[0]):
        return sorted(glob.glob(os.path.join(args[0], "*.pdf")), key=sort_key)
    return sorted(args, key=sort_key)


def main():
    argv = sys.argv[1:]
    if not argv:
        launch_gui()
        return
    # CLI: files/dir plus optional --out OUTPUT
    out = None
    if "--out" in argv:
        i = argv.index("--out")
        out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    files = _gather_cli_files(argv)
    if not files:
        print("No input PDFs found.")
        sys.exit(1)
    if not out:
        base_dir = os.path.dirname(files[0]) or "."
        out = os.path.join(base_dir, "Packed_Box_Labels.pdf")
    run(files, out)


if __name__ == "__main__":
    main()
