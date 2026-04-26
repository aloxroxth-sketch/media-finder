import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


BG       = "#0d0d14"
PANEL    = "#13131e"
CARD     = "#1a1a27"
BORDER   = "#2a2a3d"
TEXT     = "#e0deff"
SUBTEXT  = "#6b688a"
INPUT_BG = "#0a0a12"


ALL_KNOWN_EXTS = sorted([
    ".jpg",".jpeg",".png",".gif",".bmp",".tiff",".tif",".heic",".webp",
    ".raw",".cr2",".nef",".arw",".dng",".orf",".rw2",
    ".mp4",".mov",".avi",".mkv",".wmv",".m4v",".flv",".3gp",".ts",
    ".mts",".m2ts",".vob",".vcd",".mpg",".mpeg",".rmvb",".divx",".xvid",
    ".mp3",".wav",".flac",".aac",".ogg",".wma",".m4a",".aiff",".opus",
    ".mid",".midi",".ape",".ac3",".dts",".amr",".au",
    ".docx",".doc",".pdf",".txt",".odt",".rtf",".xlsx",".xls",
    ".pptx",".ppt",".csv",".md",".pages",".numbers",".key",
    ".psd",".ai",".indd",".xd",".prproj",".aep",".eps",".svg",
    ".psb",".fla",".idml",".sketch",".fig",
    ".zip",".rar",".7z",".tar",".gz",".bz2",
    ".ttf",".otf",".woff",".woff2",
    ".obj",".fbx",".stl",".blend",".3ds",".dae",
    ".py",".js",".ts",".html",".css",".json",".xml",".sql",
])

FIXED_SECTIONS = [
    {"name":"Photos",    "icon":"📷","color":"#6c63ff","folder":"photos",
     "exts":[".jpg",".jpeg",".png",".gif",".bmp",".tiff",".tif",".heic",".webp",".raw",".cr2",".nef",".arw"]},
    {"name":"Videos",    "icon":"🎬","color":"#ff6584","folder":"videos",
     "exts":[".mp4",".mov",".avi",".mkv",".wmv",".m4v",".flv",".3gp",".ts",".mts"]},
    {"name":"Audio",     "icon":"🎵","color":"#43e97b","folder":"audio",
     "exts":[".mp3",".wav",".flac",".aac",".ogg",".wma",".m4a",".aiff",".opus"]},
    {"name":"Documents", "icon":"📄","color":"#f7971e","folder":"documents",
     "exts":[".docx",".doc",".pdf",".txt",".odt",".rtf",".xlsx",".xls",".pptx",".csv"]},
]

CUSTOM_COLORS = ["#00d2ff","#f953c6","#ee0979","#4facfe","#fddb92","#a8edea","#b721ff"]



class AutocompleteEntry(tk.Entry):
    """Entry that shows a dropdown of matching known extensions as you type."""

    def __init__(self, parent, color, candidates, on_select_cb, **kw):
        super().__init__(parent, **kw)
        self.color        = color
        self.candidates   = candidates
        self.on_select_cb = on_select_cb
        self._popup       = None
        self._listbox     = None

        self.bind("<KeyRelease>", self._on_key)
        self.bind("<FocusOut>",   lambda e: self.after(150, self._close_popup))
        self.bind("<Escape>",     lambda e: self._close_popup())
        self.bind("<Down>",       self._focus_list)

    def _on_key(self, event):
        if event.keysym in ("Return", "Escape", "Down", "Up"):
            return
        raw = self.get().strip()
        if not raw or raw.startswith("e.g"):
            self._close_popup()
            return
        # support comma-separated — complete the last token
        token = raw.split(",")[-1].strip()
        if not token:
            self._close_popup()
            return
        t = token if token.startswith(".") else "." + token
        matches = [e for e in self.candidates if e.startswith(t)]
        if matches:
            self._show_popup(matches)
        else:
            self._close_popup()

    def _show_popup(self, matches):
        self._close_popup()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = max(self.winfo_width(), 140)

        self._popup = tk.Toplevel(self)
        self._popup.wm_overrideredirect(True)
        self._popup.geometry(f"{w}x{min(len(matches)*20+4, 160)}+{x}+{y}")
        self._popup.configure(bg=BORDER)

        self._listbox = tk.Listbox(
            self._popup, font=("Courier", 9),
            bg=INPUT_BG, fg=self.color,
            selectbackground=self.color, selectforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            activestyle="dotbox", height=min(len(matches), 8)
        )
        self._listbox.pack(fill="both", expand=True, padx=1, pady=1)
        for m in matches:
            self._listbox.insert("end", m)
        self._listbox.bind("<ButtonRelease-1>", self._pick)
        self._listbox.bind("<Return>",          self._pick)
        self._listbox.bind("<Escape>",          lambda e: self._close_popup())

    def _focus_list(self, event):
        if self._listbox:
            self._listbox.focus_set()
            self._listbox.selection_set(0)

    def _pick(self, event):
        if not self._listbox:
            return
        sel = self._listbox.curselection()
        if not sel:
            return
        chosen = self._listbox.get(sel[0])
        # replace last token
        raw    = self.get()
        parts  = raw.split(",")
        parts[-1] = chosen
        self.delete(0, "end")
        self.insert(0, ", ".join(p.strip() for p in parts))
        self._close_popup()
        self.focus_set()
        if self.on_select_cb:
            self.on_select_cb(chosen)

    def _close_popup(self):
        if self._popup:
            self._popup.destroy()
            self._popup  = None
            self._listbox = None


class SectionCard(tk.Frame):
    def __init__(self, parent, name, icon, color, folder, exts, canvas_ref, **kw):
        super().__init__(parent, bg=CARD, highlightthickness=1,
                         highlightbackground=BORDER, **kw)
        self.name       = name
        self.icon       = icon
        self.color      = color
        self.folder     = folder
        self.canvas_ref = canvas_ref
        self.ext_vars   = {}
        self.enabled    = tk.BooleanVar(value=True)

        self._build_header()
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        self._build_list()
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        self._build_input_row()

        for ext in exts:
            self._add_ext(ext, reflow=False)
        self._reflow()

    def _build_header(self):
        h = tk.Frame(self, bg=CARD, padx=8, pady=5)
        h.pack(fill="x")
        tk.Checkbutton(h, variable=self.enabled, bg=CARD,
                       activebackground=CARD, selectcolor=CARD,
                       fg=self.color, highlightthickness=0, bd=0
                       ).pack(side="left")
        tk.Label(h, text=f"{self.icon} {self.name.upper()}",
                 font=("Courier", 10, "bold"), fg=self.color, bg=CARD
                 ).pack(side="left")
        tk.Label(h, text=f" →/{self.folder}/",
                 font=("Courier", 7), fg=SUBTEXT, bg=CARD
                 ).pack(side="left")

    def _build_list(self):
        self.list_frame = tk.Frame(self, bg=CARD, padx=10, pady=2)
        self.list_frame.pack(fill="x")

    def _reflow(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        for ext, var in self.ext_vars.items():
            tk.Checkbutton(
                self.list_frame, text=ext, variable=var,
                font=("Courier", 9), fg=TEXT, bg=CARD,
                activeforeground=self.color, activebackground=CARD,
                selectcolor=CARD, relief="flat", bd=0,
                highlightthickness=0, cursor="hand2", anchor="w",
                pady=0, padx=2
            ).pack(fill="x", ipady=0, pady=0)
        self._notify_canvas()

    def _build_input_row(self):
        row = tk.Frame(self, bg=CARD, padx=8, pady=6)
        row.pack(fill="x")

        self.ext_entry = AutocompleteEntry(
            row, color=self.color,
            candidates=ALL_KNOWN_EXTS,
            on_select_cb=None,
            font=("Courier", 8),
            bg=INPUT_BG, fg=self.color,
            insertbackground=self.color,
            relief="flat", bd=0,
            highlightthickness=1,
            highlightcolor=self.color,
            highlightbackground=BORDER,
            width=14
        )
        self.ext_entry.pack(side="left", ipady=3, padx=(0, 5))
        self.ext_entry.bind("<Return>", lambda e: self._on_add())

        tk.Button(row, text="ADD", command=self._on_add,
                  font=("Courier", 7, "bold"), fg="white", bg=self.color,
                  activeforeground="white", activebackground=self.color,
                  relief="flat", bd=0, padx=6, pady=2, cursor="hand2"
                  ).pack(side="left")

    def _on_add(self):
        raw = self.ext_entry.get().strip()
        if not raw:
            return
        for part in raw.split(","):
            part = part.strip()
            if part:
                self._add_ext(part)
        self._reflow()
        self.ext_entry.delete(0, "end")

    def _add_ext(self, ext, reflow=True):
        ext = ext.lower().strip()
        if not ext.startswith("."):
            ext = "." + ext
        if ext in self.ext_vars:
            return
        self.ext_vars[ext] = tk.BooleanVar(value=True)
        if reflow:
            self._reflow()

    def _notify_canvas(self):
        if self.canvas_ref:
            self.update_idletasks()
            self.canvas_ref.configure(scrollregion=self.canvas_ref.bbox("all"))

    def selected_exts(self):
        if not self.enabled.get():
            return set()
        return {ext for ext, var in self.ext_vars.items() if var.get()}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Media Finder")
        self.configure(bg=BG)

        
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = min(1040, sw - 40)
        h  = min(880,  sh - 60)
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(min(700, sw - 40), min(500, sh - 60))

        self.source_var = tk.StringVar()
        self.dest_var   = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready — scan first, then copy.")
        self.cards      = []
        self._found     = []

        self._build()

    def _build(self):
        self._header()
        self._folder_bar()
        self._action_bar()
        self._results_panel()
        self._sections_area()
        self._new_section_bar()

  
    def _header(self):
        h = tk.Frame(self, bg=BG)
        h.pack(fill="x", padx=20, pady=(14, 2))
        tk.Label(h, text="MEDIA",  font=("Courier", 20, "bold"), fg="#6c63ff", bg=BG).pack(side="left")
        tk.Label(h, text="FINDER", font=("Courier", 20, "bold"), fg="#ff6584", bg=BG).pack(side="left")
        tk.Label(h, text="   scan · filter · copy into organised folders",
                 font=("Courier", 9), fg=SUBTEXT, bg=BG).pack(side="left", pady=4)

   
    def _folder_bar(self):
        bar = tk.Frame(self, bg=PANEL, padx=12, pady=8)
        bar.pack(fill="x", padx=20, pady=(0, 5))
        bar.columnconfigure(1, weight=1)
        bar.columnconfigure(4, weight=1)

        tk.Label(bar, text="SOURCE", font=("Courier", 8, "bold"),
                 fg=SUBTEXT, bg=PANEL).grid(row=0, column=0, padx=(0, 6))
        tk.Entry(bar, textvariable=self.source_var, font=("Courier", 9),
                 bg=INPUT_BG, fg=TEXT, insertbackground="#6c63ff",
                 relief="flat", bd=0, highlightthickness=1,
                 highlightcolor="#6c63ff", highlightbackground=BORDER
                 ).grid(row=0, column=1, sticky="ew", padx=(0, 6), ipady=4)
        self._btn(bar, "BROWSE", self._browse_src, "#6c63ff"
                  ).grid(row=0, column=2, padx=(0, 18))

        tk.Label(bar, text="DEST", font=("Courier", 8, "bold"),
                 fg=SUBTEXT, bg=PANEL).grid(row=0, column=3, padx=(0, 6))
        tk.Entry(bar, textvariable=self.dest_var, font=("Courier", 9),
                 bg=INPUT_BG, fg=TEXT, insertbackground="#43e97b",
                 relief="flat", bd=0, highlightthickness=1,
                 highlightcolor="#43e97b", highlightbackground=BORDER
                 ).grid(row=0, column=4, sticky="ew", padx=(0, 6), ipady=4)
        self._btn(bar, "BROWSE", self._browse_dst, "#43e97b"
                  ).grid(row=0, column=5)


    def _action_bar(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=20, pady=(0, 4))
        bar.columnconfigure(3, weight=1)

        self._btn(bar, "🔍  SCAN",  self._scan,  "#6c63ff").grid(row=0, column=0, padx=(0, 6))
        self._btn(bar, "📁  COPY",  self._copy,  "#43e97b").grid(row=0, column=1, padx=(0, 6))
        self._btn(bar, "🗑  CLEAR", self._clear, SUBTEXT  ).grid(row=0, column=2)
        tk.Label(bar, textvariable=self.status_var, font=("Courier", 8),
                 fg=SUBTEXT, bg=BG, anchor="e").grid(row=0, column=3, sticky="e")

    def _results_panel(self):
        tk.Label(self, text="SCAN RESULTS", font=("Courier", 8, "bold"),
                 fg=SUBTEXT, bg=BG).pack(anchor="w", padx=20)

        f = tk.Frame(self, bg=PANEL, height=120)
        f.pack(fill="x", padx=20, pady=(2, 6))
        f.pack_propagate(False)
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(f, font=("Courier", 8), bg="#09090f",
                                  fg=TEXT, selectbackground="#6c63ff",
                                  selectforeground="white", relief="flat",
                                  bd=0, highlightthickness=0, activestyle="none")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=4)
        sb.grid(row=0, column=1, sticky="ns", pady=4)

 
    def _sections_area(self):
        tk.Label(self, text="SECTIONS", font=("Courier", 8, "bold"),
                 fg=SUBTEXT, bg=BG).pack(anchor="w", padx=20)

        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True, padx=20, pady=(2, 0))

        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(container, orient="vertical",   command=self.canvas.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.canvas.xview)

        self.inner = tk.Frame(self.canvas, bg=BG)
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(
                            scrollregion=self.canvas.bbox("all")))

        self.canvas.bind("<MouseWheel>", self._scroll)
        self.canvas.bind("<Button-4>",   self._scroll)
        self.canvas.bind("<Button-5>",   self._scroll)

        for meta in FIXED_SECTIONS:
            self._make_card(meta["name"], meta["icon"],
                            meta["color"], meta["folder"], meta["exts"])

    def _scroll(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _make_card(self, name, icon, color, folder, exts):
        col = tk.Frame(self.inner, bg=BG)
        col.pack(side="left", fill="y", padx=(0, 6), anchor="n")
        card = SectionCard(col, name, icon, color, folder, exts,
                           canvas_ref=self.canvas)
        card.pack(fill="x")
        self.cards.append(card)
        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # ── New section bar ────────────────────────────────────────────────────
    def _new_section_bar(self):
        bar = tk.Frame(self, bg=PANEL, padx=12, pady=8)
        bar.pack(fill="x", padx=20, pady=(6, 16))

        tk.Label(bar, text="NEW SECTION", font=("Courier", 8, "bold"),
                 fg=SUBTEXT, bg=PANEL).pack(side="left", padx=(0, 8))

        self.new_sec_entry = tk.Entry(bar, font=("Courier", 9),
                                      bg=INPUT_BG, fg=SUBTEXT,
                                      insertbackground="#f7971e",
                                      relief="flat", bd=0,
                                      highlightthickness=1,
                                      highlightcolor="#f7971e",
                                      highlightbackground=BORDER,
                                      width=22)
        self.new_sec_entry.insert(0, "e.g. Adobe, Fonts, 3D Files")
        self.new_sec_entry.pack(side="left", ipady=4, padx=(0, 8))
        self.new_sec_entry.bind("<FocusIn>",  self._clear_ph)
        self.new_sec_entry.bind("<FocusOut>", self._restore_ph)
        self.new_sec_entry.bind("<Return>",   lambda e: self._create_section())

        self._btn(bar, "CREATE", self._create_section, "#f7971e").pack(side="left")
        tk.Label(bar, text="  — creates a blank section with its own folder and extension input",
                 font=("Courier", 7), fg=SUBTEXT, bg=PANEL).pack(side="left", padx=(8, 0))

    def _clear_ph(self, e):
        if self.new_sec_entry.get().startswith("e.g."):
            self.new_sec_entry.delete(0, "end")
            self.new_sec_entry.configure(fg=TEXT)

    def _restore_ph(self, e):
        if not self.new_sec_entry.get().strip():
            self.new_sec_entry.insert(0, "e.g. Adobe, Fonts, 3D Files")
            self.new_sec_entry.configure(fg=SUBTEXT)

    def _create_section(self):
        name = self.new_sec_entry.get().strip()
        if not name or name.startswith("e.g."):
            messagebox.showwarning("Name missing", "Type a section name first.")
            return
        name = name.title()
        if any(c.name.lower() == name.lower() for c in self.cards):
            messagebox.showwarning("Exists", f"'{name}' already exists.")
            return
        idx   = len(self.cards) - 4
        color = CUSTOM_COLORS[idx % len(CUSTOM_COLORS)]
        self._make_card(name, "📂", color,
                        name.lower().replace(" ", "_"), exts=[])
        self.new_sec_entry.delete(0, "end")
        self._restore_ph(None)
        self.canvas.xview_moveto(1.0)

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd,
                         font=("Courier", 8, "bold"), fg="white", bg=color,
                         activeforeground="white", activebackground=color,
                         relief="flat", bd=0, padx=12, pady=5, cursor="hand2")

    def _browse_src(self):
        d = filedialog.askdirectory()
        if d: self.source_var.set(d)

    def _browse_dst(self):
        d = filedialog.askdirectory()
        if d: self.dest_var.set(d)


    def _scan(self):
        src = self.source_var.get().strip()
        if not src or not os.path.isdir(src):
            messagebox.showerror("Error", "Choose a valid source folder.")
            return
        self._ext_map = {}
        for card in self.cards:
            for ext in card.selected_exts():
                self._ext_map[ext] = card.folder
        if not self._ext_map:
            messagebox.showwarning("Nothing selected",
                                   "Tick at least one extension.")
            return
        self.listbox.delete(0, "end")
        self._found = []
        self.status_var.set("Scanning…")
        threading.Thread(target=self._do_scan, args=(src,), daemon=True).start()

    def _do_scan(self, src):
        count = 0
        for root, _, files in os.walk(src):
            for name in files:
                ext = os.path.splitext(name)[1].lower()
                if ext in self._ext_map:
                    full   = os.path.join(root, name)
                    folder = self._ext_map[ext]
                    self._found.append((full, folder))
                    self.listbox.insert("end", f"[{folder:<14}]  {full}")
                    count += 1
        self.status_var.set(
            f"Found {count} file{'s' if count != 1 else ''}. Review, then COPY.")

    def _copy(self):
        if not self._found:
            messagebox.showinfo("Nothing to copy", "Run SCAN first.")
            return
        dest = self.dest_var.get().strip()
        if not dest:
            messagebox.showerror("Error", "Choose a destination folder.")
            return
        self.status_var.set("Copying…")
        threading.Thread(target=self._do_copy, args=(dest,), daemon=True).start()

    def _do_copy(self, dest_root):
        copied, skipped = 0, 0
        used = set()
        for src_path, folder in self._found:
            dest_dir = os.path.join(dest_root, folder)
            os.makedirs(dest_dir, exist_ok=True)
            used.add(folder)
            fname    = os.path.basename(src_path)
            dst_path = os.path.join(dest_dir, fname)
            if os.path.exists(dst_path):
                base, ext = os.path.splitext(fname)
                i = 1
                while os.path.exists(dst_path):
                    dst_path = os.path.join(dest_dir, f"{base}_{i}{ext}")
                    i += 1
            try:
                shutil.copy2(src_path, dst_path)
                copied += 1
            except Exception:
                skipped += 1
        self.status_var.set(f"Done — {copied} copied, {skipped} skipped.")
        messagebox.showinfo("Complete",
                            f"Copied {copied} file(s).\n\nFolders created:\n" +
                            "\n".join(f"  /{f}/" for f in sorted(used)))

    def _clear(self):
        self.listbox.delete(0, "end")
        self._found = []
        self.status_var.set("Cleared.")


if __name__ == "__main__":
    App().mainloop()
