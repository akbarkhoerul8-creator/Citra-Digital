"""
Visualisasi Nilai RGB Piksel + Image Analyzer - Tugas Pengolahan Citra Digital
Library : Pillow, NumPy, Tkinter (bawaan Python)

TUJUAN : Membuktikan bahwa foto (citra digital) adalah susunan angka.

Tab 1  Penjelajah Piksel   : gerakkan mouse -> nilai RGB real-time, klik -> kunci titik
Tab 2  Metadata & Data     : info dasar, EXIF kamera, GPS + link Google Maps,
                             foto jadi angka, statistik, ukuran data, byte mentah file
Tab 3  Channel & Grayscale : foto dipecah per channel + angka channel di sekitar kursor
Tab 4  Angka -> Foto       : negatif, kotak merah, gambar 6 piksel dari nol,
                             uji rekonstruksi PNG (hasil disimpan di folder hasil/)
"""

import os
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, ImageTk, ExifTags

NAMA_FILE_DEFAULT = "IMG_9164.PNG"   # ganti sesuai nama fotomu
MAKS_W, MAKS_H = 520, 700            # ukuran maksimum foto di layar
ZOOM_N = 9                           # kaca pembesar 9 x 9 piksel
ZOOM_CELL = 24                       # ukuran tiap kotak zoom (px)
BAR_W = 300                          # panjang bar R, G, B
THUMB = 200                          # ukuran thumbnail channel (px)
ANGKA_N = 8                          # area angka channel 8 x 8
ANGKA_CELL = 44                      # ukuran tiap kotak angka (px)
HASIL_MAKS = 520                     # ukuran maksimum pratinjau hasil (px)
BG = "#f2f2f2"

FOLDER_SKRIP = Path(__file__).resolve().parent
FOLDER_HASIL = FOLDER_SKRIP / "hasil"


def dms_ke_desimal(dms, ref):
    derajat, menit, detik = (float(x) for x in dms)
    nilai = derajat + menit / 60 + detik / 3600
    return -nilai if ref in ("S", "W") else nilai


class AplikasiRGB:
    def __init__(self, root):
        self.root = root
        root.title("Visualisasi Nilai RGB Piksel & Image Analyzer - Pengolahan Citra Digital")
        root.configure(bg=BG)

        self.data = None
        self.gray = None
        self.path = None
        self.scale = 1.0
        self.foto_tk = None
        self.titik_terpilih = []
        self.pos = (0, 0)
        self.link_maps = None
        self.thumb_refs = []
        self.hasil_tk = None
        self.kanal_var = tk.IntVar(value=0)

        self.buat_layout()

        for kandidat in (FOLDER_SKRIP / NAMA_FILE_DEFAULT,
                         FOLDER_SKRIP / "assets" / NAMA_FILE_DEFAULT):
            if kandidat.exists():
                self.muat_foto(kandidat)
                break
        else:
            self.buka_dialog()

    # ================================================================== UI
    def buat_layout(self):
        atas = tk.Frame(self.root, bg=BG)
        atas.pack(fill="x", padx=10, pady=(10, 4))
        tk.Button(atas, text="Buka Foto", command=self.buka_dialog,
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self.lbl_nama = tk.Label(atas, text="(belum ada foto)", bg=BG,
                                 font=("Segoe UI", 10))
        self.lbl_nama.pack(side="left", padx=10)

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_piksel = tk.Frame(self.nb, bg=BG)
        self.tab_data = tk.Frame(self.nb, bg=BG)
        self.tab_channel = tk.Frame(self.nb, bg=BG)
        self.tab_hasil = tk.Frame(self.nb, bg=BG)
        self.nb.add(self.tab_piksel, text="  1. Penjelajah Piksel  ")
        self.nb.add(self.tab_data, text="  2. Metadata & Data  ")
        self.nb.add(self.tab_channel, text="  3. Channel & Grayscale  ")
        self.nb.add(self.tab_hasil, text="  4. Angka -> Foto  ")
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.gambar_angka_channel())

        self.buat_tab_piksel(self.tab_piksel)
        self.buat_tab_data(self.tab_data)
        self.buat_tab_channel(self.tab_channel)
        self.buat_tab_hasil(self.tab_hasil)

    # ------------------------------------------------ tab 1: penjelajah piksel
    def buat_tab_piksel(self, parent):
        kiri = tk.Frame(parent, bg=BG)
        kiri.grid(row=0, column=0, padx=10, pady=10, sticky="n")
        kanan = tk.Frame(parent, bg=BG)
        kanan.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="n")

        # --- kiri: foto
        self.canvas = tk.Canvas(kiri, width=MAKS_W, height=MAKS_H,
                                bg="#222", highlightthickness=0, cursor="crosshair")
        self.canvas.pack()
        self.canvas.bind("<Motion>", self.saat_mouse_gerak)
        self.canvas.bind("<Button-1>", self.saat_klik)

        # --- kanan: info foto
        f_info = tk.LabelFrame(kanan, text=" Informasi Foto ", bg=BG,
                               font=("Segoe UI", 10, "bold"))
        f_info.pack(fill="x", pady=(0, 8))
        self.lbl_info = tk.Label(f_info, text="-", justify="left", anchor="w",
                                 bg=BG, font=("Consolas", 10))
        self.lbl_info.pack(fill="x", padx=8, pady=4)

        # --- kanan: piksel
        f_pix = tk.LabelFrame(kanan, text=" Piksel di bawah kursor ", bg=BG,
                              font=("Segoe UI", 10, "bold"))
        f_pix.pack(fill="x", pady=(0, 8))

        baris = tk.Frame(f_pix, bg=BG)
        baris.pack(fill="x", padx=8, pady=6)
        self.swatch = tk.Label(baris, width=10, height=4, bg="#888",
                               relief="solid", bd=1)
        self.swatch.pack(side="left")
        self.lbl_pix = tk.Label(baris, text="Gerakkan mouse ke foto", justify="left",
                                bg=BG, font=("Consolas", 11))
        self.lbl_pix.pack(side="left", padx=10)

        self.bar_canvas = tk.Canvas(f_pix, width=BAR_W + 90, height=80,
                                    bg=BG, highlightthickness=0)
        self.bar_canvas.pack(padx=8, pady=(0, 6))

        # --- kanan: zoom + matriks
        f_zoom = tk.LabelFrame(kanan, text=" Kaca pembesar (9 x 9 piksel) & matriks 3 x 3 ",
                               bg=BG, font=("Segoe UI", 10, "bold"))
        f_zoom.pack(fill="x", pady=(0, 8))
        isi = tk.Frame(f_zoom, bg=BG)
        isi.pack(padx=8, pady=6)
        ukuran = ZOOM_N * ZOOM_CELL
        self.zoom = tk.Canvas(isi, width=ukuran, height=ukuran,
                              bg="#ddd", highlightthickness=0)
        self.zoom.pack(side="left")
        self.lbl_matriks = tk.Label(isi, text="", justify="left", anchor="nw",
                                    bg=BG, font=("Consolas", 9))
        self.lbl_matriks.pack(side="left", padx=10, anchor="n")

        # --- kanan: histogram
        f_hist = tk.LabelFrame(kanan, text=" Histogram RGB seluruh foto ", bg=BG,
                               font=("Segoe UI", 10, "bold"))
        f_hist.pack(fill="x", pady=(0, 8))
        self.hist = tk.Canvas(f_hist, width=BAR_W + 60, height=90,
                              bg="white", highlightthickness=0)
        self.hist.pack(padx=8, pady=6)

        # --- kanan: titik terpilih
        f_pin = tk.LabelFrame(kanan, text=" Titik yang diklik ", bg=BG,
                              font=("Segoe UI", 10, "bold"))
        f_pin.pack(fill="x")
        self.lbl_pin = tk.Label(f_pin, text="(klik foto untuk menandai titik)",
                                justify="left", anchor="w", bg=BG,
                                font=("Consolas", 9))
        self.lbl_pin.pack(fill="x", padx=8, pady=4)

    # ------------------------------------------------ tab 2: metadata & data
    def buat_tab_data(self, parent):
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", padx=10, pady=(10, 4))
        self.btn_maps = tk.Button(bar, text="Buka lokasi di Google Maps",
                                  command=self.buka_maps, state="disabled")
        self.btn_maps.pack(side="left")
        self.txt_data = ScrolledText(parent, width=100, height=36, font=("Consolas", 10),
                                     wrap="none", state="disabled")
        self.txt_data.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ------------------------------------------------ tab 3: channel & grayscale
    def buat_tab_channel(self, parent):
        f_ch = tk.LabelFrame(parent, text=" Foto dipecah per channel (2 channel lain dinolkan) ",
                             bg=BG, font=("Segoe UI", 10, "bold"))
        f_ch.pack(fill="x", padx=10, pady=10)
        self.lbl_thumb = []
        judul = ["Channel R (berwarna)", "Channel G (berwarna)",
                 "Channel B (berwarna)", "Grayscale (1 angka/piksel)"]
        for i, jud in enumerate(judul):
            kol = tk.Frame(f_ch, bg=BG)
            kol.grid(row=0, column=i, padx=6, pady=6)
            lbl = tk.Label(kol, bg="#222", width=THUMB // 8, height=THUMB // 16)
            lbl.pack()
            tk.Label(kol, text=jud, bg=BG, font=("Segoe UI", 9, "bold")).pack()
            self.lbl_thumb.append(lbl)

        f_ang = tk.LabelFrame(parent, text=" Angka channel di sekitar kursor (area 8 x 8) ",
                              bg=BG, font=("Segoe UI", 10, "bold"))
        f_ang.pack(fill="x", padx=10, pady=(0, 10))
        pilih = tk.Frame(f_ang, bg=BG)
        pilih.pack(anchor="w", padx=8, pady=(6, 0))
        tk.Label(pilih, text="Channel:", bg=BG).pack(side="left")
        for i, nama in enumerate("RGB"):
            tk.Radiobutton(pilih, text=nama, value=i, variable=self.kanal_var,
                           bg=BG, command=self.gambar_angka_channel).pack(side="left", padx=4)
        ukuran = ANGKA_N * ANGKA_CELL
        self.cv_angka = tk.Canvas(f_ang, width=ukuran, height=ukuran,
                                  bg="#ddd", highlightthickness=0)
        self.cv_angka.pack(side="left", padx=8, pady=8)
        self.lbl_angka_info = tk.Label(
            f_ang, justify="left", anchor="nw", bg=BG, font=("Consolas", 10),
            text="Gerakkan mouse di Tab 1,\nlalu kembali ke tab ini.")
        self.lbl_angka_info.pack(side="left", padx=10, anchor="n", pady=8)

    # ------------------------------------------------ tab 4: angka -> foto
    def buat_tab_hasil(self, parent):
        f_btn = tk.LabelFrame(parent, text=" Ubah angkanya, gambarnya ikut berubah ",
                              bg=BG, font=("Segoe UI", 10, "bold"))
        f_btn.pack(fill="x", padx=10, pady=10)
        tombol = [
            ("Foto asli", self.tampil_asli),
            ("Negatif (255 - angka)", self.tampil_negatif),
            ("Kotak merah 100x100", self.tampil_kotak),
            ("Gambar 6 piksel dari nol", self.tampil_enam_piksel),
            ("Uji rekonstruksi PNG", self.tampil_rekonstruksi),
            ("Simpan semua ke hasil/", self.simpan_semua),
        ]
        for i, (teks, cmd) in enumerate(tombol):
            tk.Button(f_btn, text=teks, command=cmd).grid(
                row=i // 3, column=i % 3, padx=6, pady=4, sticky="ew")

        self.lbl_hasil_info = tk.Label(parent, text="Pilih salah satu tombol di atas.",
                                       justify="left", anchor="w", bg=BG, wraplength=900,
                                       font=("Segoe UI", 10))
        self.lbl_hasil_info.pack(fill="x", padx=12, pady=(0, 6))
        self.lbl_hasil_img = tk.Label(parent, bg="#222")
        self.lbl_hasil_img.pack(padx=10, pady=(0, 10))

    # ============================================================ muat foto
    def buka_dialog(self):
        p = filedialog.askopenfilename(
            title="Pilih foto",
            filetypes=[("Gambar", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"),
                       ("Semua file", "*.*")])
        if p:
            self.muat_foto(Path(p))

    def muat_foto(self, path):
        try:
            asli = Image.open(path)
        except Exception as e:
            messagebox.showerror("Gagal", f"Tidak bisa membuka foto:\n{e}")
            return

        format_file = asli.format
        mode_asli = asli.mode
        exif = asli.getexif()
        koordinat = self.baca_gps(exif)
        meta = self.baca_exif_kamera(exif)

        img = ImageOps.exif_transpose(asli).convert("RGB")
        self.path = Path(path)
        self.data = np.array(img)
        tinggi, lebar, kanal = self.data.shape

        r = self.data[..., 0].astype(float)
        g = self.data[..., 1].astype(float)
        b = self.data[..., 2].astype(float)
        self.gray = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.uint8)

        # --- tab 1
        self.scale = min(MAKS_W / lebar, MAKS_H / tinggi)
        dw, dh = int(lebar * self.scale), int(tinggi * self.scale)
        self.canvas.config(width=dw, height=dh)
        self.canvas.delete("all")
        self.foto_tk = ImageTk.PhotoImage(img.resize((dw, dh), Image.LANCZOS))
        self.canvas.create_image(0, 0, anchor="nw", image=self.foto_tk)

        gps_teks = (f"{koordinat[0]:.6f}, {koordinat[1]:.6f}"
                    if koordinat else "tidak ada data GPS")
        self.lbl_nama.config(text=self.path.name)
        self.lbl_info.config(text=(
            f"Nama file : {self.path.name}\n"
            f"Format    : {format_file}\n"
            f"Resolusi  : {lebar} x {tinggi} piksel\n"
            f"Piksel    : {lebar * tinggi:,}".replace(",", ".") + "\n"
            f"Channel   : {kanal} (R, G, B) | {self.data.dtype}\n"
            f"GPS       : {gps_teks}"))

        self.titik_terpilih = []
        self.pos = (0, 0)
        self.lbl_pin.config(text="(klik foto untuk menandai titik)")
        self.gambar_histogram()
        self.perbarui_piksel(0, 0)

        # --- tab 2, 3, 4
        self.link_maps = (f"https://www.google.com/maps?q={koordinat[0]:.6f},{koordinat[1]:.6f}"
                          if koordinat else None)
        self.btn_maps.config(state="normal" if self.link_maps else "disabled")
        self.isi_tab_data(format_file, mode_asli, meta, koordinat)
        self.buat_thumbnail_channel()
        self.gambar_angka_channel()
        self.tampil_asli()

    @staticmethod
    def baca_gps(exif):
        """Kembalikan (lat, lon) desimal, atau None jika tidak ada GPS."""
        try:
            gps = exif.get_ifd(0x8825)       # 0x8825 = bagian GPS
            if gps and 2 in gps and 4 in gps:
                lat = dms_ke_desimal(gps[2], gps.get(1, "N"))
                lon = dms_ke_desimal(gps[4], gps.get(3, "E"))
                return lat, lon
        except Exception:
            pass
        return None

    @staticmethod
    def baca_exif_kamera(exif):
        meta = {}
        try:
            for kode, nilai in exif.items():
                meta[ExifTags.TAGS.get(kode, kode)] = nilai
            for kode, nilai in exif.get_ifd(0x8769).items():   # detail kamera
                meta[ExifTags.TAGS.get(kode, kode)] = nilai
        except Exception:
            pass
        return meta

    # ============================================================== event tab 1
    def posisi_piksel(self, event):
        x = min(max(int(event.x / self.scale), 0), self.data.shape[1] - 1)
        y = min(max(int(event.y / self.scale), 0), self.data.shape[0] - 1)
        return x, y

    def saat_mouse_gerak(self, event):
        if self.data is None:
            return
        x, y = self.posisi_piksel(event)
        self.pos = (x, y)
        self.perbarui_piksel(x, y)
        self.canvas.delete("kursor")
        r = 8
        self.canvas.create_oval(event.x - r, event.y - r, event.x + r, event.y + r,
                                outline="white", width=2, tags="kursor")
        self.canvas.create_oval(event.x - r - 1, event.y - r - 1,
                                event.x + r + 1, event.y + r + 1,
                                outline="black", tags="kursor")

    def saat_klik(self, event):
        if self.data is None:
            return
        x, y = self.posisi_piksel(event)
        R, G, B = (int(v) for v in self.data[y, x])
        self.titik_terpilih.append((x, y, R, G, B))
        self.titik_terpilih = self.titik_terpilih[-5:]

        self.canvas.delete("pin")
        for i, (px, py, *_rgb) in enumerate(self.titik_terpilih, 1):
            cx, cy = px * self.scale, py * self.scale
            self.canvas.create_rectangle(cx - 5, cy - 5, cx + 5, cy + 5,
                                         outline="yellow", width=2, tags="pin")
            self.canvas.create_text(cx + 10, cy - 10, text=str(i), fill="yellow",
                                    font=("Segoe UI", 11, "bold"), tags="pin")
        teks = "\n".join(
            f"{i}. ({px},{py}) RGB [{r:3d} {g:3d} {b:3d}]  #{r:02X}{g:02X}{b:02X}"
            for i, (px, py, r, g, b) in enumerate(self.titik_terpilih, 1))
        self.lbl_pin.config(text=teks)

    # ============================================================ tampilan tab 1
    def perbarui_piksel(self, x, y):
        R, G, B = (int(v) for v in self.data[y, x])
        hex_warna = f"#{R:02x}{G:02x}{B:02x}"

        self.swatch.config(bg=hex_warna)
        self.lbl_pix.config(text=(
            f"Koordinat : ({x}, {y})\n"
            f"RGB       : [{R}, {G}, {B}]\n"
            f"HEX       : {hex_warna.upper()}"))

        # bar R, G, B
        self.bar_canvas.delete("all")
        for i, (nama, nilai, warna) in enumerate(
                [("R", R, "#e53935"), ("G", G, "#43a047"), ("B", B, "#1e88e5")]):
            y0 = 6 + i * 25
            self.bar_canvas.create_text(8, y0 + 9, text=nama,
                                        font=("Consolas", 11, "bold"))
            self.bar_canvas.create_rectangle(22, y0, 22 + BAR_W, y0 + 18,
                                             outline="#aaa", fill="white")
            self.bar_canvas.create_rectangle(22, y0, 22 + BAR_W * nilai / 255, y0 + 18,
                                             outline="", fill=warna)
            self.bar_canvas.create_text(22 + BAR_W + 8, y0 + 9, text=str(nilai),
                                        anchor="w", font=("Consolas", 11, "bold"))

        # kaca pembesar
        self.zoom.delete("all")
        tinggi, lebar, _ = self.data.shape
        setengah = ZOOM_N // 2
        for dy in range(-setengah, setengah + 1):
            for dx in range(-setengah, setengah + 1):
                px = min(max(x + dx, 0), lebar - 1)
                py = min(max(y + dy, 0), tinggi - 1)
                r, g, b = (int(v) for v in self.data[py, px])
                cx = (dx + setengah) * ZOOM_CELL
                cy = (dy + setengah) * ZOOM_CELL
                self.zoom.create_rectangle(cx, cy, cx + ZOOM_CELL, cy + ZOOM_CELL,
                                           fill=f"#{r:02x}{g:02x}{b:02x}",
                                           outline="#bbb")
        c = setengah * ZOOM_CELL
        self.zoom.create_rectangle(c, c, c + ZOOM_CELL, c + ZOOM_CELL,
                                   outline="red", width=3)

        # matriks 3 x 3
        baris = []
        for dy in (-1, 0, 1):
            sel = []
            for dx in (-1, 0, 1):
                px = min(max(x + dx, 0), lebar - 1)
                py = min(max(y + dy, 0), tinggi - 1)
                r, g, b = (int(v) for v in self.data[py, px])
                sel.append(f"{r:3d},{g:3d},{b:3d}")
            baris.append(" | ".join(sel))
        self.lbl_matriks.config(text="Matriks RGB 3x3\n(R,G,B per piksel)\n\n" +
                                "\n".join(baris))

    def gambar_histogram(self):
        self.hist.delete("all")
        W, H = BAR_W + 40, 80
        x0, y0 = 10, 4
        hitungan = [np.bincount(self.data[..., c].ravel(), minlength=256)
                    for c in range(3)]
        batas = max(np.percentile(np.concatenate(hitungan), 99), 1)
        for h, warna in zip(hitungan, ["#e53935", "#43a047", "#1e88e5"]):
            titik = []
            for i in range(256):
                titik.append(x0 + i * W / 255)
                titik.append(y0 + H - min(h[i], batas) / batas * H)
            self.hist.create_line(*titik, fill=warna, width=1.5)
        self.hist.create_line(x0, y0 + H, x0 + W, y0 + H, fill="#666")
        self.hist.create_text(x0, y0 + H + 6, text="0", anchor="n", font=("Consolas", 8))
        self.hist.create_text(x0 + W, y0 + H + 6, text="255", anchor="n",
                              font=("Consolas", 8))

    # ============================================================ tab 2: isi teks
    def isi_tab_data(self, format_file, mode_asli, meta, koordinat):
        d = self.data
        tinggi, lebar, kanal = d.shape
        L = []

        L.append("=== 1. INFORMASI DASAR ===")
        L.append(f"Nama file      : {self.path.name}")
        L.append(f"Format         : {format_file}")
        L.append(f"Resolusi       : {lebar} x {tinggi}")
        L.append(f"Mode warna     : {mode_asli}")
        L.append(f"Total piksel   : {lebar * tinggi:,}".replace(",", "."))
        L.append("")

        L.append("=== 2. METADATA EXIF ===")
        yang_ditampilkan = [
            ("DateTimeOriginal", "Tanggal pengambilan"),
            ("Make", "Merek kamera"),
            ("Model", "Model kamera"),
            ("ISOSpeedRatings", "ISO"),
            ("ExposureTime", "Exposure time"),
            ("FNumber", "Aperture (F)"),
            ("FocalLength", "Focal length"),
        ]
        ada = False
        for nama_exif, label in yang_ditampilkan:
            if nama_exif in meta:
                L.append(f"{label:<20}: {meta[nama_exif]}")
                ada = True
        if not ada:
            L.append("Metadata kamera tidak tersedia.")
        if koordinat:
            L.append(f"Koordinat GPS       : {koordinat[0]:.6f}, {koordinat[1]:.6f}")
            L.append(f"Link Google Maps    : {self.link_maps}")
            L.append("(!) Catatan privasi : foto bisa membocorkan lokasi lewat metadata.")
        else:
            L.append("GPS                 : tidak tersedia")
        L.append("")

        L.append("=== 3. FOTO MENJADI ANGKA ===")
        L.append(f"Shape array : {d.shape} -> (tinggi, lebar, channel)")
        L.append(f"Tipe data   : {d.dtype} -> bilangan bulat 0 sampai 255")
        L.append("")
        L.append("Artinya:")
        L.append(f"  tinggi  = {tinggi} -> jumlah BARIS piksel")
        L.append(f"  lebar   = {lebar} -> jumlah KOLOM piksel")
        L.append(f"  channel = {kanal} -> angka per piksel [R, G, B]")
        L.append("")
        L.append("Contoh arti warna:")
        L.append("  [255,   0,   0] = merah")
        L.append("  [  0, 255,   0] = hijau")
        L.append("  [  0,   0, 255] = biru")
        L.append("  [  0,   0,   0] = hitam")
        L.append("  [255, 255, 255] = putih")
        L.append("")

        L.append("=== 4. NILAI PIKSEL (3 titik sampel) ===")
        for nama, (y, x) in [("pojok kiri atas", (0, 0)),
                             ("tengah gambar", (tinggi // 2, lebar // 2)),
                             ("pojok kanan bawah", (tinggi - 1, lebar - 1))]:
            r, g, b = (int(v) for v in d[y, x])
            L.append(f"Piksel (baris={y}, kolom={x}) [{nama}] -> R={r}, G={g}, B={b}")
        L.append("")

        L.append("=== 5. POTONGAN MATRIX (5x5 piksel pertama) ===")
        potongan = d[:5, :5]
        L.append(str(potongan))
        L.append(f"Shape: {potongan.shape} -> baris, kolom, 3 angka (RGB)")
        L.append("Setiap [R G B] di atas = SATU piksel.")
        L.append("")

        L.append("=== 6. STATISTIK ===")
        for nama, c in zip(("Red  ", "Green", "Blue "), range(3)):
            k = d[..., c]
            L.append(f"{nama} -> min {k.min()}, max {k.max()}, rata-rata {k.mean():.2f}")
        L.append("")
        ukuran_array = d.nbytes
        ukuran_file = os.path.getsize(self.path)
        L.append(f"Ukuran array (mentah)  : {ukuran_array:,} byte".replace(",", "."))
        L.append(f"Ukuran file di disk    : {ukuran_file:,} byte".replace(",", "."))
        L.append(f"Rasio file / array     : {ukuran_file / ukuran_array:.1%}")
        L.append("Array = hasil decode (tinggi x lebar x 3 byte). File di disk biasanya")
        L.append("lebih kecil karena dikompresi (JPEG/PNG).")
        L.append("")
        L.append("Satu channel : 256 kemungkinan (0-255) = 8 bit")
        L.append(f"Tiga channel : 256 x 256 x 256 = {256 ** 3:,} warna (24 bit)".replace(",", "."))
        L.append("")

        L.append("=== 7. GRAYSCALE ===")
        L.append(f"Shape gray : {self.gray.shape} -> tidak ada dimensi channel lagi")
        L.append("Rumus      : gray = 0.299*R + 0.587*G + 0.114*B")
        my, mx = tinggi // 2, lebar // 2
        L.append(f"Piksel tengah: RGB = {d[my, mx]} -> gray = {self.gray[my, mx]}")
        L.append("")

        L.append("=== 8. BYTE MENTAH FILE ===")
        try:
            with open(self.path, "rb") as f:
                awal = f.read(16)
            L.append(f"16 byte pertama (desimal)     : {list(awal)}")
            L.append(f"16 byte pertama (heksadesimal): {awal.hex(' ').upper()}")
            if awal[:2] == b"\xff\xd8":
                L.append("JPEG selalu diawali FF D8 -> 'tanda tangan' file JPEG.")
            elif awal[:4] == b"\x89PNG":
                L.append("PNG selalu diawali 89 50 4E 47 (\\x89 + 'PNG') -> 'tanda tangan' file PNG.")
            elif awal[:2] == b"BM":
                L.append("BMP selalu diawali 42 4D ('BM') -> 'tanda tangan' file BMP.")
        except OSError as e:
            L.append(f"Tidak bisa membaca byte file: {e}")

        self.txt_data.config(state="normal")
        self.txt_data.delete("1.0", "end")
        self.txt_data.insert("1.0", "\n".join(L))
        self.txt_data.config(state="disabled")

    def buka_maps(self):
        if self.link_maps:
            webbrowser.open(self.link_maps)

    # ============================================================ tab 3
    def buat_thumbnail_channel(self):
        d = self.data
        nol = np.zeros_like(d)
        larik = []
        for c in range(3):
            tmp = nol.copy()
            tmp[..., c] = d[..., c]
            larik.append(tmp)
        larik.append(self.gray)

        self.thumb_refs = []
        for lbl, arr in zip(self.lbl_thumb, larik):
            im = Image.fromarray(arr)
            im.thumbnail((THUMB, THUMB))
            tkimg = ImageTk.PhotoImage(im)
            self.thumb_refs.append(tkimg)
            lbl.config(image=tkimg, width=im.width, height=im.height)

    def gambar_angka_channel(self):
        if self.data is None:
            return
        c = self.kanal_var.get()
        tinggi, lebar, _ = self.data.shape
        n = min(ANGKA_N, tinggi, lebar)
        x, y = self.pos
        x0 = min(max(x - n // 2, 0), lebar - n)
        y0 = min(max(y - n // 2, 0), tinggi - n)

        self.cv_angka.delete("all")
        for j in range(n):
            for i in range(n):
                v = int(self.data[y0 + j, x0 + i, c])
                cx, cy = i * ANGKA_CELL, j * ANGKA_CELL
                self.cv_angka.create_rectangle(
                    cx, cy, cx + ANGKA_CELL, cy + ANGKA_CELL,
                    fill=f"#{v:02x}{v:02x}{v:02x}", outline="#888")
                self.cv_angka.create_text(
                    cx + ANGKA_CELL / 2, cy + ANGKA_CELL / 2, text=str(v),
                    fill="black" if v > 128 else "white", font=("Consolas", 10))
        px, py = (x - x0) * ANGKA_CELL, (y - y0) * ANGKA_CELL
        self.cv_angka.create_rectangle(px, py, px + ANGKA_CELL, py + ANGKA_CELL,
                                       outline="red", width=3)
        self.lbl_angka_info.config(text=(
            f"Kursor     : ({x}, {y})\n"
            f"Area       : {n} x {n} mulai (x={x0}, y={y0})\n"
            f"Channel    : {'RGB'[c]}\n"
            f"Nilai kursor: {int(self.data[y, x, c])}\n\n"
            f"Gelap  = angka kecil (0 = hitam)\n"
            f"Terang = angka besar (255 = putih)"))

    # ============================================================ tab 4
    def tampil_hasil(self, arr, keterangan):
        im = Image.fromarray(arr)
        im.thumbnail((HASIL_MAKS, HASIL_MAKS), Image.NEAREST if arr.shape[0] < 10 else Image.LANCZOS)
        self.hasil_tk = ImageTk.PhotoImage(im)
        self.lbl_hasil_img.config(image=self.hasil_tk)
        self.lbl_hasil_info.config(text=keterangan)

    def arr_negatif(self):
        return 255 - self.data

    def arr_kotak(self):
        m = self.data.copy()                      # .copy() agar array asli tidak rusak
        m[50:150, 50:150] = [255, 0, 0]
        return m

    @staticmethod
    def arr_enam_piksel():
        kecil = np.array(
            [[[255, 0, 0], [0, 255, 0], [0, 0, 255]],          # merah, hijau, biru
             [[255, 255, 0], [255, 255, 255], [0, 0, 0]]],     # kuning, putih, hitam
            dtype=np.uint8)
        besar = Image.fromarray(kecil).resize((300, 200), Image.NEAREST)
        return kecil, np.array(besar)

    def tampil_asli(self):
        if self.data is None:
            return
        self.tampil_hasil(self.data, "Foto asli: np.array(foto) -> matriks angka 0-255.")

    def tampil_negatif(self):
        if self.data is None:
            return
        self.tampil_hasil(self.arr_negatif(),
                          "Negatif: setiap angka dibalik (255 - angka). 0 jadi 255, 255 jadi 0.")

    def tampil_kotak(self):
        if self.data is None:
            return
        self.tampil_hasil(self.arr_kotak(),
                          "Kotak merah: area 100x100 piksel (baris 50-149, kolom 50-149) "
                          "dipaksa bernilai [255, 0, 0].")

    def tampil_enam_piksel(self):
        kecil, besar = self.arr_enam_piksel()
        self.tampil_hasil(besar,
                          f"Gambar dari nol: shape {kecil.shape} = 6 piksel, hanya dari angka "
                          "yang ditulis sendiri, tanpa kamera.\n"
                          "Baris 1: merah, hijau, biru | Baris 2: kuning, putih, hitam "
                          "(diperbesar dengan NEAREST).")

    def tampil_rekonstruksi(self):
        if self.data is None:
            return
        os.makedirs(FOLDER_HASIL, exist_ok=True)
        p = FOLDER_HASIL / "hasil_rekonstruksi.png"
        Image.fromarray(self.data).save(p)
        baca_ulang = np.array(Image.open(p).convert("RGB"))
        sama = np.array_equal(baca_ulang, self.data)
        self.tampil_hasil(
            baca_ulang,
            f"Array -> PNG -> array identik dengan aslinya? {sama}\n"
            "PNG bersifat lossless (tidak mengubah angka), jadi hasilnya harus identik.\n"
            f"Disimpan di: {p}")

    def simpan_semua(self):
        if self.data is None:
            return
        os.makedirs(FOLDER_HASIL, exist_ok=True)
        Image.fromarray(self.data).save(FOLDER_HASIL / "hasil_rekonstruksi.png")
        Image.fromarray(self.arr_negatif()).save(FOLDER_HASIL / "hasil_negatif.png")
        Image.fromarray(self.arr_kotak()).save(FOLDER_HASIL / "hasil_kotak_merah.png")
        Image.fromarray(self.arr_enam_piksel()[1]).save(FOLDER_HASIL / "hasil_buatan_sendiri.png")
        self.lbl_hasil_info.config(
            text=f"4 gambar disimpan di folder:\n{FOLDER_HASIL}\n"
                 "(hasil_rekonstruksi, hasil_negatif, hasil_kotak_merah, hasil_buatan_sendiri)")


if __name__ == "__main__":
    root = tk.Tk()
    AplikasiRGB(root)
    root.mainloop()