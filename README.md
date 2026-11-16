# Hackintosh — Dell Inspiron 15 3511 (Tiger Lake)

**English** · [Bahasa Indonesia](README.id.md)

OpenCore EFI + installer media for running **macOS Monterey 12.7.6** on a
Dell Inspiron 15 3511. Starting point: Samsung Book i3-1115G4 EFI, fully
adapted to Dell hardware.

> **Status:** EFI verified to boot into macOS Recovery on this laptop (2026-11-07).

## Target hardware

| Component | Detail | Status |
|---|---|---|
| Laptop | Dell Inspiron 15 3511 (board `05PD08`, BIOS 1.48.0) | — |
| CPU | Intel Core i3-1115G4 (Tiger Lake-UP3, 2C/4T) | ✅ |
| iGPU | Intel UHD Graphics G4 `8086:9A78` (48 EU) | ✅ via WhateverXe |
| RAM | 4 GB (3.6 GiB) | ⚠️ tight — see RAM note |
| Storage | NVMe Lexar NM610 PRO `1d97:1202` | ✅ |
| Audio | Realtek ALC3204 = **ALC236** `10ec:0236` | ✅ layout-id 11 |
| WiFi/BT | Realtek RTL8821CE `10ec:c821` | ❌ unsupported by macOS |
| Ethernet | none | → HoRNDIS (USB tethering) |
| Touchpad | Goodix I2C HID `DELL0AB0` (`27C6:0D43`) | ✅ VoodooI2C+HID |

## Layout

```
EFI-Dell-3511-Monterey/     ready-to-use EFI + full README
  EFI/BOOT/                 BOOTx64.efi
  EFI/OC/                   config.plist, config-WEX.plist, ACPI, Kexts, Drivers
efi-dell-3511-xe/           first attempt (Big Sur + WhateverXe 0.2.3)
installer/
  tulis-ke-usb.sh           write image to USB + install EFI
  dmg2raw.py                Apple DMG -> raw converter (pure Python)
  buat-usb.sh               legacy method (com.apple.recovery.boot folder)
build-efi.py                EFI builder from the Samsung base
fix-exitbs.py               Tiger Lake quirk patch + 2 config variants
```

## Component versions

| Component | Version |
|---|---|
| OpenCore | 1.0.7 |
| WhateverXe | 0.7.0 |
| WhateverXe Graphics | 0.4.0 |
| AMFIPass | 1.4.1 Mod |
| SMBIOS | MacBookAir9,1 |

## Two config phases

| File | Phase | GPU stack | boot-args |
|---|---|---|---|
| `config.plist` | installation | WhateverGreen + VESA | `-v keepsyms=1 -igfxvesa watchdog=0 -vi2c-force-polling alcid=11` |
| `config-WEX.plist` | after 12.7.6 is installed | WhateverXe + AMFIPass | `-v -allow3d -disablegfxfirmware -igfxdvmt keepsyms=1 -amfipassbeta` |

WhateverXe only supports specific builds (Monterey **12.7.6**), while the
recovery image is 12.5.1 — that is why the installation phase uses WhateverGreen.

## Important notes

### 1. Freeze at `[EB|LOG:EXITBS:START]` — ✅ SOLVED

The cause was a **wrong combination of memory-map quirks**, not a firmware
limitation. The profile used (proven on another Tiger Lake laptop,
[nullmoth/1401#102](https://github.com/nullmoth/1401/issues/102)):

```
EnableWriteUnprotector = true
RebuildAppleMemoryMap = false
DevirtualiseMmio     = false
SetupVirtualMap      = true
ProtectUefiServices  = false
```

**Verified 2026-11-07:** this EFI boots into macOS Recovery on this laptop.

### 2. 4 GB RAM vs ramdisk

`BaseSystem.dmg` expands to a **3.0 GiB ramdisk**, which is very tight on a
3.6 GiB machine. If you hit memory-related failures, boot the recovery from a
**disk partition** instead (`installer/BaseSystem-3.0GiB.img`) — no ramdisk involved.

### 3. Full offline installer

Cannot be built from Linux. `SharedSupport.dmg` inside `InstallAssistant.pkg`
only contains a payload volume (`com_apple_MobileAsset_MacSoftwareUpdate`)
**without `boot.efi`**. Combining BaseSystem + payload into a bootable installer
is what `createinstallmedia` does, and it exists on macOS only.

## Quick start

```bash
# 1. write recovery image to USB (>= 4 GB)
cd installer
sudo bash tulis-ke-usb.sh BaseSystem-3.0GiB.img /dev/sdX

# 2. BIOS: Secure Boot OFF, SATA AHCI, Fast Boot Thorough
# 3. F12 -> boot USB -> OpenCore -> "macOS Base System"
# 4. Disk Utility -> erase the target partition as APFS -> Reinstall macOS Monterey
#    (needs internet / USB tethering)
# 5. once on the desktop: copy EFI to the SSD EFI partition
# 6. swap config.plist <- config-WEX.plist, then install WhateverXe-Graphics-0.4.0.pkg
```

Full details: `EFI-Dell-3511-Monterey/README.md`.

## Not tracked by this repo

| Item | Size | Reason |
|---|---|---|
| `installer/*.img` | 3.0 GB | binary image, rebuilt with `dmg2raw.py` |
| `installer/com.apple.recovery.boot/` | 627 MB | output of `macrecovery.py` |
| `installer/*.pkg` | 91 MB | third-party release packages |
| `efi/`, `efi-dellku/`, `hackmate/`, `WhateverXe/`, `GenSMBIOS/` | ~1 GB | upstream repos with their own `.git` |
| `backup/`, `backup (Copy)/` | 71 MB | snapshots, superseded by git history |

## Credits

- [WhateverXe](https://github.com/b00t0x/WhateverXe) & [WhateverXe Graphics](https://github.com/b00t0x/WhateverXe-Graphics)
- [OpenCore](https://github.com/acidanthera/OpenCorePkg)
- Base EFI: [cost-12/Hackintosh-Samsung-Book-INTEL-CORE-I3-1115G4-11TH](https://github.com/cost-12/Hackintosh-Samsung-Book-INTEL-CORE-I3-1115G4-11TH)
- [Dortania OpenCore Install Guide](https://dortania.github.io/OpenCore-Install-Guide/)
