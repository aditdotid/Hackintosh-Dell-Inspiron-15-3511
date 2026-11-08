# EFI Dell Inspiron 15 3511 — Xe iGPU Acceleration

> **Target OS**: macOS Big Sur **11.7.10 (build 20G1443)**  
> **OpenCore**: 1.0.7  
> **WhateverXe**: 0.2.3  
> **Status iGPU**: ✅ Akselerasi GPU bekerja (setelah OCLP root patch)

---

## Spesifikasi Hardware

| Komponen | Detail |
|----------|--------|
| **Laptop** | Dell Inspiron 15 3511 |
| **CPU** | Intel Core i3-1115G4 (Tiger Lake, 2C/4T, 3.0–4.1GHz) |
| **iGPU** | Intel UHD Graphics G4 `[8086:9a78]` — Xe-LP |
| **RAM** | 8 GB DDR4 |
| **Storage** | Lexar NM610 PRO NVMe `[1d97:1202]` |
| **Audio** | Realtek ALC236 (ALC3204) `[10ec:0236]` |
| **WiFi** | Realtek RTL8821CE `[10ec:c821]` |
| **USB** | Intel 500 Series xHCI `[8086:a0ed]` |
| **BIOS** | Dell v1.44.0 |

---

## Status Fitur

| Fitur | Status | Catatan |
|-------|--------|---------|
| Boot macOS | ✅ Working | |
| iGPU Acceleration (QE/CI) | ✅ Working | Setelah OCLP Xe root patch |
| Metal / OpenGL | ✅ Working | Setelah OCLP Xe root patch |
| Hardware Video Decode | ✅ Working | H.264, HEVC |
| Audio (Speaker + Headphone) | ✅ Working | ALC236, layout-id 11 |
| Keyboard | ✅ Working | VoodooPS2 |
| Trackpad | ✅ Working | VoodooI2C |
| Fn Brightness Keys | ✅ Working | BrightnessKeys.kext |
| Battery Indicator | ✅ Working | SMCBatteryManager |
| USB Ports | ✅ Working | USBMap |
| NVMe SSD | ✅ Working | NVMeFix |
| Sleep / Wake | ⚠️ Partial | Masih dalam pengujian |
| HDMI Output | ✅ Working | Setelah OCLP root patch |
| WiFi | ⚠️ Manual | Build Feixiao kext setelah install |
| Bluetooth | ❌ Tidak bekerja | RTL8821CE BT tidak didukung |

---

## ⚠️ Hal yang HARUS Dilakukan Sebelum Boot

### 1. Generate SMBIOS Baru (WAJIB)

**Jangan boot dengan serial yang terisi `FILL_IN_WITH_GENSMBIOS`!**

Download [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) dan jalankan di macOS/Linux/Windows:

```bash
python3 GenSMBIOS.py
# Pilih: 1 (Install MacSerial)
# Pilih: 3 (Generate SMBIOS)
# Ketik: MacBookAir9,1
```

Isi hasil output ke `config.plist` di bagian `PlatformInfo > Generic`:
- `SystemSerialNumber` → Serial Number
- `MLB` → Board Serial Number  
- `SystemUUID` → SmUUID

Untuk `ROM` — isi dengan MAC address network card Anda (dalam hex binary, base64):
```bash
# Di Linux/macOS, ganti 'eth0' atau 'wlan0' sesuai interface:
cat /sys/class/net/wlan0/address | tr -d ':' | xxd -r -p | base64
```

### 2. BIOS Settings (WAJIB)

Masuk BIOS Dell (F2 saat boot) dan set:
- **SATA Mode** → AHCI
- **Secure Boot** → Disabled
- **Fast Boot** → Disabled / Thorough
- **DVMT Pre-Allocated** → Jika bisa diubah, set ke **96MB** (lalu hapus `-igfxdvmt` dan `framebuffer-stolenmem` dari boot-args dan DeviceProperties)

> **DVMT Note**: BIOS Dell biasanya terkunci di 60MB. EFI ini sudah menggunakan workaround `-igfxdvmt` + `framebuffer-stolenmem`. Jika nanti berhasil ubah ke 96MB via RU.efi, hapus kedua parameter tersebut.

---

## Panduan Instalasi

### Step 1 — Buat USB Installer

Download macOS Big Sur **11.7.10** (build `20G1443`) — versi ini WAJIB untuk WhateverXe.

```bash
# Di macOS lain atau menggunakan macrecovery:
python3 macrecovery.py -b Mac-E43C1C25D4880AD6 -m 00000000000000000 download
```

Atau gunakan [OCLP fork dari b00t0x](https://github.com/b00t0x/OpenCore-Legacy-Patcher/releases) untuk membuat installer.

Format USB (minimal 16GB) sebagai `Mac OS Extended (Journaled)` + `GUID Partition Map`, lalu copy installer dan EFI ini.

### Step 2 — Boot Installer

Boot dari USB → pilih "Install macOS Big Sur" → install ke NVMe.

Koneksi internet saat install: gunakan **USB tethering dari HP** (HoRNDIS sudah disertakan).

### Step 3 — Copy EFI ke SSD

Setelah install selesai, copy folder `EFI/` ini ke partisi EFI SSD:
```bash
# Mount EFI partition dulu
sudo diskutil mount /dev/disk0s1
cp -r /Volumes/USB/EFI /Volumes/EFI/
```

### Step 4 — Jalankan OCLP Xe Root Patch (WAJIB untuk iGPU)

Download **OpenCore Legacy Patcher fork oleh b00t0x** (bukan OCLP resmi!):
- https://github.com/b00t0x/OpenCore-Legacy-Patcher/releases

Jalankan OCLP → **Post Install Root Patch** → apply patch → **Reboot**.

Setelah reboot, iGPU acceleration akan aktif penuh (Metal, OpenGL, hardware decode).

### Step 5 — Install Feixiao (WiFi RTL8821CE)

Build Feixiao kext di macOS setelah install:

```bash
# Install Xcode Command Line Tools dulu:
xcode-select --install

# Clone dan build Feixiao:
git clone https://github.com/thegwchr/Feixiao.git
cd Feixiao
git submodule update --recursive
git clone https://github.com/thegwchr/rtw88-stable.git ../rtw88-stable

# Build:
make all

# Install:
sudo cp -r rtw88.kext /Library/Extensions/
sudo kextcache -i /
```

---

## Struktur Kext

| Kext | Versi | Fungsi |
|------|-------|--------|
| Lilu | latest | Framework (load PERTAMA) |
| VirtualSMC | latest | SMC emulation |
| SMCBatteryManager | latest | Battery % |
| SMCProcessor | latest | CPU monitoring |
| **WhateverXe** | **0.2.3** | **Xe iGPU acceleration** |
| **AMFIPass** | **1.4.1-Mod** | **OCLP root patch support** |
| AppleALC | latest | Audio ALC236 |
| NVMeFix | latest | NVMe PM |
| ECEnabler | latest | EC battery |
| BrightnessKeys | latest | Fn keys |
| VoodooPS2Controller | latest | Keyboard |
| VoodooI2C | latest | Trackpad I2C |
| VoodooI2CHID | latest | Trackpad HID |
| USBMap | custom | USB mapping |
| RestrictEvents | latest | OTA fix |
| CPUFriend | latest | CPU PM |
| CPUFriendDataProvider | custom | PM data |
| RTCMemoryFixup | latest | RTC fix |
| HoRNDIS | latest | USB tethering |

---

## Boot Arguments

```
-allow3d -disablegfxfirmware -igfxdvmt keepsyms=1 -amfipassbeta
```

| Argument | Keterangan |
|----------|-----------|
| `-allow3d` | Aktifkan 3D path Apple driver (WhateverXe wajib) |
| `-disablegfxfirmware` | Disable Apple driver firmware loading path |
| `-igfxdvmt` | Workaround DVMT 60MB (hapus jika sudah 96MB) |
| `keepsyms=1` | Debug kernel symbols |
| `-amfipassbeta` | Allow AMFIPass Mod |

---

## DVMT Upgrade ke 96MB (Opsional, via RU.efi)

Jika ingin meningkatkan DVMT dari 60MB ke 96MB:

1. Boot OpenCore → pilih `CleanNvram` atau `Shell` dari Tools
2. Gunakan RU.efi untuk akses hidden BIOS menu
3. Ubah DVMT Pre-Allocated dari `02` → `03`
4. Setelah berhasil, edit `config.plist`:
   - Hapus `-igfxdvmt` dari `boot-args`
   - Hapus `framebuffer-patch-enable` dari DeviceProperties iGPU
   - Hapus `framebuffer-stolenmem` dari DeviceProperties iGPU

---

## Referensi

- [WhateverXe by b00t0x](https://github.com/b00t0x/WhateverXe)
- [OCLP fork by b00t0x](https://github.com/b00t0x/OpenCore-Legacy-Patcher)
- [Reddit: Tiger Lake Xe iGPU Acceleration](https://www.reddit.com/r/hackintosh/comments/1x26ygh/tiger_lake_alder_laken_xe_igpu_acceleration/)
- [Feixiao WiFi Driver](https://github.com/thegwchr/Feixiao)
- [Dortania OpenCore Guide](https://dortania.github.io/OpenCore-Install-Guide/)
- [EFI Base (Samsung Book i3-1115G4)](https://github.com/cost-12/Hackintosh-Samsung-Book-INTEL-CORE-I3-1115G4-11TH)
