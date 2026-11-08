# EFI Hackintosh — Dell Inspiron 15 3511

**Target OS:** macOS **Monterey 12.7.6**
**OpenCore:** 1.0.7 · **WhateverXe:** 0.7.0 + WhateverXe Graphics 0.4.0
**Basis:** EFI Samsung Book i3-1115G4 (cost-12) — sudah diadaptasi ke hardware Dell ini

---

## 1. Hardware terdeteksi

| Komponen | Detail | Status di macOS |
|---|---|---|
| Laptop | Dell Inspiron 15 3511 (`05PD08`) | — |
| BIOS | Dell 1.48.0 | — |
| CPU | Intel Core i3-1115G4 (Tiger Lake-UP3, 2C/4T) | ✅ native |
| iGPU | Intel UHD Graphics G4 `[8086:9A78]`, 48 EU | ✅ **akselerasi via WhateverXe** |
| RAM | 8 GB DDR4 | ✅ |
| Storage | NVMe Lexar NM610 PRO `[1d97:1202]` | ✅ (NVMeFix) |
| Audio | Realtek ALC3204 = **ALC236** `[10ec:0236]` | ✅ layout-id **11** |
| Ethernet | **tidak ada** | — (driver dihapus) |
| WiFi/BT | Realtek RTL8821CE `[10ec:c821]` | ❌ tidak didukung macOS |
| Keyboard | PS/2 | ✅ VoodooPS2 |
| Touchpad | I2C HID | ✅ VoodooI2C + VoodooI2CHID |
| Webcam | Microdia USB 0c45:6d1a | ✅ UVC native |
| Card reader | tidak ada | — |

---

## 2. Yang diubah dari EFI Samsung

### Dihapus (khusus Samsung / tidak relevan)
- **ACPI:** `DSDT.aml`, `facp.aml`, `mcfg.aml`, `nhlt.aml`, `ssdt_data.aml`, `ssdtCPU*`, `ssdtTGLU6`, `ssdtTCSS5`, `ssdtSEC8`, `ssdtTHER7`, `ssdtPM_REF*`, `ssdtADEB11`, `ssdtIgfx4`, `ssdtDPTF2`, `ssdtsleep3`, `ssdtRHUB10`, `ssdtTypeC9`
- **`SSDT-VOLKEYSS.aml`** → dihapus (sesuai permintaan; tombol volume Samsung)
- **`SSDT-SMSG.aml`** → dihapus (sesuai permintaan; SMBus khusus Samsung)
- **`SSDT-TPD0` / `SSDT-FPDT` / `SSDT-ALS0`** → touchpad & fingerprint & sensor cahaya Samsung
- **Kext:** `RealtekRTL8111` (tidak ada ethernet), semua `AirportItlwm*`, `AirportBrcmFixup`, `BrcmFirmwareData`, `BrcmPatchRAM3`, `BlueToolFixup`, `IntelBluetooth*`, `IntelBTPatcher`, `IO80211FamilyLegacy`, `IOSkywalkFamily`, `NootedBlue`, `WhateverGreen`, `CtlnaAHCIPort`, `EmeraldSDHC`, `SMCSuperIO`, `SMCLightSensor`, `HibernationFixup`, `FeatureUnlock`, `NoTouchID`, `USBWakeFixup`, `SystemProfilerMemoryFixup`, `ForgedInvariant`, `HWPEnabler`, `DisplayMergeNub`, `EFICheckDisabler`, `XHCI-unsupported`
- **DeviceProperties** Samsung: spoof WiFi BCM4360, EDID panel Samsung, OZ711 SD reader, model string Samsung

### Ditambah / diganti
- **WhateverXe 0.7.0** menggantikan WhateverGreen (Tiger Lake Xe-LP)
- **AMFIPass 1.4.1 Mod** (wajib untuk root patch WEX)
- **HoRNDIS** aktif — pengganti ethernet (USB tethering HP Android)
- **SSDT-PNLF versi Dell** (backlight)
- **layout-id 11** untuk ALC236
- **DVMT 60 MB workaround**: `-igfxdvmt` + `framebuffer-stolenmem`
- **SMBIOS baru**: `MacBookAir9,1` (2-core, paling dekat dengan i3-1115G4)
- **ACPI patch** dibersihkan: hanya `_OSI→XOSI`, `GPRW→XPRW`, `HDAS→HDEF`

---

## 3. SMBIOS yang sudah digenerate

| Field | Nilai |
|---|---|
| SystemProductName | `MacBookAir9,1` |
| SystemSerialNumber | `FVFDV0L2MNHP` |
| MLB | `FVF051700GU0000JA` |
| SystemUUID | `E5840D9F-EF63-4C05-9DD9-323614F41952` |
| ROM | `e2b26d551c41` (MAC WiFi laptop ini) |

> Serial di atas digenerate dengan `macserial` (OpenCore 1.0.7) dan checksum MLB valid.
> Kalau mau generate ulang: `./macserial -m MacBookAir9,1 -n 1`, lalu ganti 4 field itu
> di `PlatformInfo > Generic`.

---

## 4. Dua fase config

EFI ini punya **2 config** karena WhateverXe hanya jalan di macOS **12.7.6**,
sedangkan image recovery-nya 12.5.1.

| File | Dipakai kapan | GPU stack | boot-args |
|---|---|---|---|
| `config.plist` | **fase instalasi** (sekarang aktif) | WhateverGreen + VESA | `-v keepsyms=1 -igfxvesa watchdog=0 -vi2c-force-polling alcid=11` |
| `config-WEX.plist` | **setelah macOS 12.7.6 terpasang** | WhateverXe + AMFIPass | `-v -allow3d -disablegfxfirmware -igfxdvmt keepsyms=1 -amfipassbeta` |

Cara pindah fase (dari Linux, USB terpasang):
```bash
cd /run/media/$USER/<USB>/EFI/OC
cp config.plist config-installer-backup.plist
cp config-WEX.plist config.plist
```

| Arg | Fungsi |
|---|---|
| `-igfxvesa` | pakai framebuffer VESA (tanpa akselerasi) — cukup untuk instalasi |
| `-allow3d` | **wajib WEX** — aktifkan jalur 3D driver Apple |
| `-disablegfxfirmware` | **wajib WEX** — matikan loading firmware GPU |
| `-igfxdvmt` | DVMT Dell terkunci 60 MB |
| `-vi2c-force-polling` | bantu VoodooI2C kalau interupsi tidak jalan |
| `watchdog=0` | matikan watchdog panic |
| `keepsyms=1` | simbol kernel saat panic (debug) |

`csr-active-config = 03080000` (0x803) — wajib untuk root patch WEX.

> **Quirks penting (fix freeze `[EB|LOG:EXITBS:START]`):**
> `EnableWriteUnprotector=true`, `RebuildAppleMemoryMap=false`,
> `DevirtualiseMmio=false`, `SetupVirtualMap=true`, `ProtectUefiServices=false`.
> Profil ini diambil dari laporan solved untuk laptop Tiger Lake
> (github.com/nullmoth/1401/issues/102) — kombinasi memory-map yang salah
> membuat kernel tidak pernah jalan.

---

## 5. Langkah instalasi

### 5.1 BIOS (F2 saat nyala)
- **Secure Boot** → Disabled
- **SATA Operation** → AHCI
- **Fast Boot** → Thorough
- **Virtualization** → Enabled (opsional)
- Simpan & exit

### 5.2 Buat USB (dari Linux)
```bash
cd /home/ditzz/Documents/project/efi-dell-3511/installer
sudo bash buat-usb.sh /dev/sdX      # ganti sdX dengan USB Anda
```
Cek dulu device-nya: `lsblk -o NAME,SIZE,TYPE,MODEL`

Script akan membuat 1 partisi FAT32 2 GB berisi:
```
/EFI/                          <- OpenCore
/com.apple.recovery.boot/      <- image recovery Monterey
/WhateverXe-Graphics-0.4.0.pkg <- dipasang nanti
```

### 5.3 Boot installer
1. F12 → pilih USB (mode **UEFI**)
2. Picker OpenCore → pilih **macOS Recovery** (image: Monterey **12.5.1 / 21G83**)
3. Recovery butuh internet untuk mengunduh macOS 12.7.6 (±12 GB):
   - colok HP Android → aktifkan **USB Tethering**
   - HoRNDIS akan muncul sebagai interface Ethernet
4. `Disk Utility` → erase NVMe sebagai **APFS** (GUID)
5. `Reinstall macOS Monterey` → pilih disk → tunggu

> Installer akan menarik versi **12.7.6 (21G1320)** dari katalog Apple — itu versi
> yang dibutuhkan WhateverXe. Setelah selesai, cek di  → About This Mac.
> Kalau ternyata masih 12.5.1, jalankan **System Update** ke 12.7.6 dulu
> **sebelum** memasang WhateverXe Graphics.

> Kalau tidak mau internet saat install, lihat bagian 8 (installer offline).

### 5.4 Setelah macOS terpasang
1. Boot lagi dari USB, lalu salin EFI ke partisi EFI SSD:
   ```bash
   diskutil list                     # cari disk0s1 (EFI)
   sudo diskutil mount disk0s1
   cp -R /Volumes/OC-INSTALLER/EFI /Volumes/EFI/
   ```
2. **WAJIB untuk akselerasi GPU** — pasang paket grafis:
   ```
   buka WhateverXe-Graphics-0.4.0.pkg dari USB → install → restart
   ```
   Setelah restart: Metal, OpenGL, decode H.264/HEVC, HDMI, brightness aktif.

---

## 6. Yang belum jalan / catatan

| Fitur | Status |
|---|---|
| WiFi RTL8821CE | ❌ tidak ada driver. Pakai USB tethering, dongle WiFi USB, atau ganti kartu ke Intel AX210/Broadcom |
| Bluetooth RTL8821CE | ❌ tidak didukung |
| Sleep/wake | ⚠️ belum teruji penuh (WEX: system sleep masih riset) |
| iMessage/FaceTime | ⚠️ butuh serial valid + Apple ID (di luar cakupan EFI) |
| Sidecar/AirPlay ke Mac | ❌ butuh WiFi |
| HDMI | ✅ setelah root patch WEX |
| Brightness Fn | ✅ SSDT-PNLF + BrightnessKeys (setelah root patch) |

---

## 7. Troubleshooting

| Gejala | Solusi |
|---|---|
| Stuck di `[EB|#LOG:EXITBS:START]` | **Sudah diperbaiki** lewat profil quirks TGL: `EnableWriteUnprotector=true`, `RebuildAppleMemoryMap=false`, `DevirtualiseMmio=false`, `ProtectUefiServices=false`. Kalau masih: cek RAM (butuh ≥8 GB untuk ramdisk 3,2 GB) |
| Panic `AppleIntelTGLGraphics` | pastikan `WhateverGreen` **tidak** ada di folder Kexts |
| Layar hitam setelah picker | tambah `-igfxvesa` sementara, atau cek DVMT |
| Audio tidak keluar | coba `layout-id` 13 / 69 / 21 di `DeviceProperties` |
| Trackpad tidak jalan | Touchpad = **Goodix I2C HID** (`DELL0AB0`, `27C6:0D43`). Cek `SSDT-XOSI` + patch `_OSI→XOSI` aktif, `VoodooI2C` + `VoodooI2CHID` enabled. Kalau tetap gagal, coba `force-polling` di `DeviceProperties` I2C0, atau fallback `VoodooPS2Mouse.kext` (mode PS/2) |
| Touchpad jalan tapi tidak ada klik | aktifkan `VoodooI2CHID` (sudah aktif) + cek `force-polling` |
| USB mati setelah install | mapping ulang pakai USBToolBox, aktifkan `USBMap.kext` |

---

## 8. Media installer

Image siap-`dd` di folder `installer/`:

| Image | Ukuran | USB minimal | Isi | Install |
|---|---|---|---|---|
| `BaseSystem-3.0GiB.img` | 3,0 GiB | **4 GB** | Recovery macOS Monterey 12.5.1 (bootable) | online (unduh 12.7.6 ±12 GB) |

Image sudah berisi GPT sendiri: partisi 1 = **EFI (FAT32 200 MB, kosong)**,
partisi 2 = volume HFS+ "macOS Base System" (2,68 GiB, 45.670 file, ada `boot.efi`).
Jadi tidak perlu `parted`/format — cukup `dd`, EFI disalin otomatis oleh skrip.

```bash
cd /home/ditzz/Documents/project/efi-dell-3511/installer
sudo bash tulis-ke-usb.sh BaseSystem-3.0GiB.img /dev/sdX
```

> **Kenapa bukan `com.apple.recovery.boot` lagi?**
> Cara DMG menaruh image ke **ramdisk 3,0 GiB**. Laptop ini RAM-nya cuma 4 GB
> (3,6 GiB) → kernel tidak kebagian memori, berhenti di `[EB|LOG:EXITBS:START]`.
> Dengan `.img` ini sistem **boot langsung dari partisi disk**, bukan ramdisk.

> **Soal full installer offline:** tidak bisa dibuat dari Linux. Sudah diperiksa isi
> `InstallAssistant.pkg` (produk `062-40406`): `SharedSupport.dmg` di dalamnya hanya
> berisi volume *payload* (`com_apple_MobileAsset_MacSoftwareUpdate`) **tanpa `boot.efi`**
> — bukan volume bootable. Yang menggabungkan BaseSystem + payload menjadi installer
> bootable adalah `createinstallmedia`, dan itu **hanya ada di macOS**.
> File `InstallAssistant-Monterey-12.7.6.pkg` (12,4 GB) tetap disimpan kalau nanti
> ada akses ke Mac / VM macOS untuk membuat installer offline.

Asal-usul image (untuk reproduksi):
- `BaseSystem-3.0GiB.img` ← `macrecovery.py` (Monterey 12.5.1, build 21G83,
  terverifikasi 63/63 chunk chunklist Apple) → `dmg2raw.py`

---

## 9. Referensi
- WhateverXe — https://github.com/b00t0x/WhateverXe (0.7.0, dukung Monterey 12.7.6)
- WhateverXe Graphics — https://github.com/b00t0x/WhateverXe-Graphics
- EFI basis Samsung — https://github.com/cost-12/Hackintosh-Samsung-Book-INTEL-CORE-I3-1115G4-11TH
- Dortania OpenCore Guide — https://dortania.github.io/OpenCore-Install-Guide/
- OpenCore 1.0.7 — https://github.com/acidanthera/OpenCorePkg
