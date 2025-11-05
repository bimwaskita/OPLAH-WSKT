# link-list.py

Script kecil untuk membuat CSV berisi daftar gambar (image files) yang ada di sebuah folder/subfolder pada repository GitHub.

Kolom CSV: folder, subfolder, subfolder, nama gambar, url

Contoh penggunaan:

```
python link-list.py --owner myuser --repo myrepo --branch main --path path/to/folder --output images.csv
```

Opsi penting:
- --token: token GitHub (opsional). Berguna untuk menghindari batasan rate limit API.
- --path: path di dalam repo (kosong = root)

Catatan:
- Script menggunakan GitHub API untuk membaca isi folder secara rekursif.
- URL pada kolom `url` adalah raw URL (https://raw.githubusercontent.com/...)
