# Hackintosh — Dell Inspiron 15 3511 (Tiger Lake)

[English](README.md) · **Bahasa Indonesia**

EFI OpenCore + media installer untuk menjalankan **macOS Monterey 12.7.6** di
Dell Inspiron 15 3511. Basis awal: EFI Samsung Book i3-1115G4, diadaptasi total
ke hardware Dell.

> **Status:** EFI terverifikasi berhasil boot ke macOS Recovery di laptop ini (2026-11-07).

## Hardware target

| Komponen | Detail | Status |
|---|---|---|
| Laptop | Dell Inspiron 15 3511 (board `05PD08`, BIOS 1.48.0) | — |
| CPU | Intel Core i3-1115G4 (Tiger Lake-UP3, 2C/4T) | ✅ |
| iGPU | Intel UHD Graphics G4 `8086:9A78` (48 EU) | ✅ via WhateverXe |
| RAM | 4 GB (3,6 GiB) | ⚠️ mepet — lihat catatan RAM |
| Storage | NVMe Lexar NM610 PRO `1d97:1202` | ✅ |
| Audio | Realtek ALC3204 = **ALC236** `10ec:0236` | ✅ layout-id 11 |
| WiFi/BT | Realtek RTL8821CE `10ec:c821` | ❌ tidak didukung macOS |
| Ethernet | tidak ada | → HoRNDIS (USB tethering) |
| Touchpad | Goodix I2C HID `DELL0AB0` (`27C6:0D43`) | ✅ VoodooI2C+HID |

## Struktur

```
EFI-Dell-3511-Monterey/     EFI siap pakai + README lengkap
  EFI/BOOT/                 BOOTx64.efi
  EFI/OC/                   config.plist, config-WEX.plist, ACPI, Kexts, Drivers
efi-dell-3511-xe/           EFI percobaan pertama (Big Sur + WhateverXe 0.2.3)
installer/
  tulis-ke-usb.sh           tulis image ke USB + pasang EFI
  dmg2raw.py                konverter Apple DMG -> raw (murni Python)
  buat-usb.sh               cara lama (folder com.apple.recovery.boot)
build-efi.py                builder EFI dari basis Samsung
fix-exitbs.py               patch quirks Tiger Lake + 2 varian config
```

## Versi komponen

| Komponen | Versi |
|---|---|
| OpenCore | 1.0.7 |
| WhateverXe | 0.7.0 |
| WhateverXe Graphics | 0.4.0 |
| AMFIPass | 1.4.1 Mod |
| SMBIOS | MacBookAir9,1 |

## Dua fase config

| File | Fase | GPU stack | boot-args |
|---|---|---|---|
| `config.plist` | instalasi | WhateverGreen + VESA | `-v keepsyms=1 -igfxvesa watchdog=0 -vi2c-force-polling alcid=11` |
| `config-WEX.plist` | setelah 12.7.6 terpasang | WhateverXe + AMFIPass | `-v -allow3d -disablegfxfirmware -igfxdvmt keepsyms=1 -amfipassbeta` |

WhateverXe hanya mendukung build tertentu (Monterey **12.7.6**), sedangkan image
recovery 12.5.1 — karena itu fase instalasi memakai WhateverGreen.

## Catatan penting

### 1. Freeze `[EB|LOG:EXITBS:START]` — ✅ TERATASI

Penyebabnya **kombinasi quirks memory-map yang salah**, bukan firmware. Profil yang
dipakai (terbukti pada laptop Tiger Lake lain,
[nullmoth/1401#102](https://github.com/nullmoth/1401/issues/102)):

```
EnableWriteUnprotector = true
RebuildAppleMemoryMap = false
DevirtualiseMmio     = false
SetupVirtualMap      = true
ProtectUefiServices  = false
```

**Terverifikasi 2026-11-07:** EFI ini berhasil boot ke macOS Recovery di laptop ini.

### 2. RAM 4 GB vs ramdisk

`BaseSystem.dmg` mengembang menjadi **ramdisk 3,0 GiB**, sangat mepet di mesin
3,6 GiB. Kalau muncul kegagalan terkait memori, boot recovery dari **partisi disk**
(`installer/BaseSystem-3.0GiB.img`) — tanpa ramdisk.

### 3. Full installer offline

Tidak bisa dibuat dari Linux. `SharedSupport.dmg` di dalam `InstallAssistant.pkg`
hanya berisi volume payload (`com_apple_MobileAsset_MacSoftwareUpdate`) **tanpa
`boot.efi`**. Yang menggabungkan BaseSystem + payload adalah `createinstallmedia`
(macOS saja).

## Alur pakai singkat

```bash
# 1. tulis image recovery ke USB (>= 4 GB)
cd installer
sudo bash tulis-ke-usb.sh BaseSystem-3.0GiB.img /dev/sdX

# 2. BIOS: Secure Boot OFF, SATA AHCI, Fast Boot Thorough
# 3. F12 -> boot USB -> OpenCore -> "macOS Base System"
# 4. Disk Utility -> erase partisi target sebagai APFS -> Reinstall macOS Monterey
#    (butuh internet / USB tethering)
# 5. setelah masuk desktop: salin EFI ke partisi EFI SSD
# 6. tukar config.plist <- config-WEX.plist, lalu install WhateverXe-Graphics-0.4.0.pkg
```

Detail lengkap ada di `EFI-Dell-3511-Monterey/README.id.md`.

## Yang tidak di-track repo ini

| Item | Ukuran | Alasan |
|---|---|---|
| `installer/*.img` | 3,0 GB | image biner, dibuat ulang via `dmg2raw.py` |
| `installer/com.apple.recovery.boot/` | 627 MB | hasil `macrecovery.py` |
| `installer/*.pkg` | 91 MB | paket rilis pihak ketiga |
| `efi/`, `efi-dellku/`, `hackmate/`, `WhateverXe/`, `GenSMBIOS/` | ~1 GB | repo upstream, punya `.git` sendiri |
| `backup/`, `backup (Copy)/` | 71 MB | snapshot, digantikan riwayat git |

## Kredit

- [WhateverXe](https://github.com/b00t0x/WhateverXe) & [WhateverXe Graphics](https://github.com/b00t0x/WhateverXe-Graphics)
- [OpenCore](https://github.com/acidanthera/OpenCorePkg)
- EFI basis: [cost-12/Hackintosh-Samsung-Book-INTEL-CORE-I3-1115G4-11TH](https://github.com/cost-12/Hackintosh-Samsung-Book-INTEL-CORE-I3-1115G4-11TH)
- [Dortania OpenCore Install Guide](https://dortania.github.io/OpenCore-Install-Guide/)
