# RGB Image Analyzer

Aplikasi Python untuk **membuktikan bahwa foto digital adalah susunan angka**. Foto dibaca menjadi angka (RGB 0-255), angkanya diamati dan diubah, lalu dikembalikan menjadi gambar.

Dibuat untuk tugas mata kuliah **Pengolahan Citra Digital**.

> **Analogi singkat:** foto itu seperti mozaik keramik di lantai. Dari jauh tampak satu gambar utuh, dari dekat ternyata ribuan kotak kecil berwarna. Tiap kotak = 1 piksel = 3 angka (Red, Green, Blue).

---

## Fitur

Aplikasi desktop (Tkinter) dengan 4 tab:

| Tab | Isi |
|---|---|
| **1. Penjelajah Piksel** | Gerakkan mouse di atas foto dan lihat nilai RGB, HEX, bar R/G/B, kaca pembesar 9×9, matriks 3×3, serta histogram secara langsung. Klik untuk menandai titik (maksimal 5 titik terakhir). |
| **2. Metadata & Data** | Info dasar foto, EXIF kamera, GPS + tombol Google Maps, bentuk array, 3 piksel sampel, potongan matriks 5×5, statistik per channel, ukuran array vs file, grayscale, dan byte mentah file. |
| **3. Channel & Grayscale** | Foto dipecah jadi channel R, G, B (berwarna) dan grayscale, plus kotak angka channel 8×8 di sekitar kursor. |
| **4. Angka → Foto** | Negatif (`255 - angka`), kotak merah 100×100, gambar 6 piksel dari nol, uji rekonstruksi PNG, dan simpan semua hasil ke folder `hasil/`. |

<!--
Tampilan (hapus tanda komentar ini setelah kamu menaruh screenshot di folder screenshots/):

![Tab 1](screenshots/tab1.png)
![Tab 3](screenshots/tab3.png)
-->

---

## Persyaratan

- Python 3.8 atau lebih baru
- Pustaka: **Pillow** (9 atau lebih baru) dan **NumPy**
- **Tkinter** (sudah bawaan Python di Windows dan macOS)

Instalasi pustaka:

```bash
pip install pillow numpy
```

Di Linux (Ubuntu/Debian), Tkinter dipasang terpisah:

```bash
sudo apt install python3-tk
```

---

## Cara Pakai

### 1. Siapkan foto

Taruh foto satu folder dengan `rgb_image_analyzer.py` (atau di subfolder `assets/`), lalu sesuaikan nama file di bagian atas script:

```python
NAMA_FILE_DEFAULT = "IMG_5611.PNG"   # ganti sesuai nama fotomu
```

Kalau file tidak ditemukan, dialog pilih file akan muncul. Foto juga bisa diganti kapan saja lewat tombol **Buka Foto**.

### 2. Jalankan

```bash
python rgb_image_analyzer.py
```

### 3. Jelajahi

1. **Tab 1:** gerakkan mouse di atas foto, lalu klik untuk menandai titik.
2. **Tab 3:** pindah ke tab ini untuk melihat angka channel di sekitar posisi kursor terakhir.
3. **Tab 4:** klik tombol-tombolnya. **Simpan semua ke hasil/** menyimpan 4 gambar ke folder `hasil/` (dibuat otomatis).

> Untuk melihat EXIF kamera dan GPS di Tab 2, pakai **file asli dari kamera**. Foto hasil screenshot atau yang sudah dikirim lewat aplikasi chat umumnya tidak membawa metadata tersebut.

---

## Versi Notebook (Jupyter / Google Colab)

Tkinter tidak berjalan di Jupyter atau Colab, jadi tersedia versi notebook dengan `ipywidgets` dan `matplotlib`. Notebook dipecah per tahap dan masing-masing bisa dijalankan sendiri:

| File | Isi |
|---|---|
| `1_Membaca_Foto_dan_Nilai_RGB.ipynb` | Info foto, tampilkan foto, nilai RGB/HEX satu piksel dengan slider |
| `2_Kaca_Pembesar_dan_Matriks_3x3.ipynb` | Kaca pembesar 9×9 dan matriks 3×3 per kanal |
| `3_Histogram_RGB.ipynb` | Histogram gabungan dan per kanal, statistik, grayscale |
| `4_Aplikasi_Interaktif_Lengkap.ipynb` | Semua fitur dalam satu antarmuka (tombol Buka Foto dan Tandai titik) |

Pustaka tambahan untuk notebook:

```bash
pip install matplotlib ipywidgets
```

Cell opsional untuk hover mouse real-time (hanya Jupyter lokal) membutuhkan `pip install ipympl`.
Di Google Colab tidak perlu menaruh foto di folder, karena akan muncul dialog upload.

---

## Struktur Folder

```
.
├── rgb_image_analyzer.py                    # aplikasi Tkinter 4 tab
├── IMG_5611.PNG                             # foto uji (ganti sesuai fotomu)
├── hasil/                                   # dibuat otomatis saat menyimpan hasil
│   ├── hasil_rekonstruksi.png
│   ├── hasil_negatif.png
│   ├── hasil_kotak_merah.png
│   └── hasil_buatan_sendiri.png
├── 1_Membaca_Foto_dan_Nilai_RGB.ipynb
├── 2_Kaca_Pembesar_dan_Matriks_3x3.ipynb
├── 3_Histogram_RGB.ipynb
├── 4_Aplikasi_Interaktif_Lengkap.ipynb
├── Laporan_Foto_adalah_Angka.docx           # laporan tugas
├── Laporan_Foto_adalah_Angka.pdf
└── README.md
```

---

## Konsep Singkat

- **Foto = array.** `np.array(foto)` menghasilkan larik berbentuk `(tinggi, lebar, 3)` bertipe `uint8`.
- **Piksel dibaca dengan `data[y, x]`** (baris dulu, baru kolom), menghasilkan `[R, G, B]`.
- **Warna:** 256 × 256 × 256 = 16.777.216 kemungkinan (24 bit). Angka kecil berarti gelap, angka besar berarti terang.
- **Grayscale:** `gray = 0.299 R + 0.587 G + 0.114 B`.
- **Angka → foto:** `Image.fromarray(array)` mengembalikan angka menjadi gambar. Pada format lossless seperti PNG, hasilnya identik dengan aslinya (`np.array_equal` bernilai `True`).

### Contoh potongan kode

```python
from PIL import Image
import numpy as np

foto = Image.open("IMG_5611.PNG")
data = np.array(foto.convert("RGB"))     # foto -> angka
print(data.shape, data.dtype)            # (tinggi, lebar, 3) uint8

r, g, b = data[100, 200]                 # satu piksel (baris 100, kolom 200)
negatif = 255 - data                     # ubah angka -> gambar berubah

Image.fromarray(negatif).save("hasil_negatif.png")
```

---

## Hasil Pengujian

Diuji dengan foto `IMG_9164.PNG` (1737 × 3088 piksel, 5.363.856 piksel):

| Pengamatan | Hasil |
|---|---|
| Bentuk array | `(3088, 1737, 3)`, tipe `uint8` |
| Ukuran array vs file | 16.091.568 byte vs 11.754.613 byte (PNG dikompresi tanpa mengubah angka) |
| Rekonstruksi PNG | Array → PNG → array identik (`True`) |
| Byte awal file | `89 50 4E 47 ...` (tanda tangan PNG) |

Hasil lengkap dan pembahasannya ada di laporan (`Laporan_Foto_adalah_Angka.pdf`).

---

## Pemecahan Masalah

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError: No module named 'tkinter'` | Linux: `sudo apt install python3-tk`. Windows/macOS: pasang ulang Python dari python.org dan pastikan opsi tcl/tk ikut terpasang. |
| `ModuleNotFoundError: No module named 'PIL'` atau `'numpy'` | Jalankan `pip install pillow numpy`. |
| Dialog pilih file muncul terus saat dijalankan | File foto tidak ditemukan. Cek `NAMA_FILE_DEFAULT` dan lokasi fotonya. |
| GPS dan EXIF "tidak tersedia" | Foto tidak membawa metadata. Pakai file asli dari kamera. |
| Foto terbuka tetapi terlalu besar | Tidak masalah: tampilan otomatis diperkecil, sedangkan nilai piksel tetap dibaca dari resolusi aslinya. |
| Kotak merah tidak terlihat | Area kotak (baris dan kolom 50 sampai 149) berada di luar foto yang sangat kecil. Gunakan foto yang lebih besar. |

---

## Pembuat

**Khaerul Akbar**, Teknik Informatika, Universitas Nahdlatul Ulama Indonesia (UNUSIA).
Tugas mata kuliah Pengolahan Citra Digital, 2026.
