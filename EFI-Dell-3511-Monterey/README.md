# Hackintosh EFI — Dell Inspiron 15 3511

**English** · [Bahasa Indonesia](README.id.md)

**Target OS:** macOS **Monterey 12.7.6**
**OpenCore:** 1.0.7 · **WhateverXe:** 0.7.0 + WhateverXe Graphics 0.4.0
**Base:** Samsung Book i3-1115G4 EFI (cost-12) — fully adapted to this Dell hardware

> ✅ **Verified 2026-11-07:** this EFI boots into macOS Recovery on this laptop.

---

## 1. Detected hardware

| Component | Detail | Status in macOS |
|---|---|---|
| Laptop | Dell Inspiron 15 3511 (`05PD08`) | — |
| BIOS | Dell 1.48.0 | — |
| CPU | Intel Core i3-1115G4 (Tiger Lake-UP3, 2C/4T) | ✅ native |
| iGPU | Intel UHD Graphics G4 `[8086:9A78]`, 48 EU | ✅ **accelerated via WhateverXe** |
| RAM | 4 GB (3.6 GiB) | ⚠️ tight — see section 8 |
| Storage | NVMe Lexar NM610 PRO `[1d97:1202]` | ✅ (NVMeFix) |
| Audio | Realtek ALC3204 = **ALC236** `[10ec:0236]` | ✅ layout-id **11** |
| Ethernet | **none** | — (driver removed) |
| WiFi/BT | Realtek RTL8821CE `[10ec:c821]` | ❌ unsupported by macOS |
| Keyboard | PS/2 | ✅ VoodooPS2 |
| Touchpad | Goodix I2C HID (`DELL0AB0`, `27C6:0D43`) | ✅ VoodooI2C + VoodooI2CHID |
| Webcam | Microdia USB 0c45:6d1a | ✅ native UVC |
| Card reader | none | — |

---

## 2. Changes vs. the Samsung EFI

### Removed (Samsung-specific / irrelevant)
- **ACPI:** `DSDT.aml`, `facp.aml`, `mcfg.aml`, `nhlt.aml`, `ssdt_data.aml`, `ssdtCPU*`, `ssdtTGLU6`, `ssdtTCSS5`, `ssdtSEC8`, `ssdtTHER7`, `ssdtPM_REF*`, `ssdtADEB11`, `ssdtIgfx4`, `ssdtDPTF2`, `ssdtsleep3`, `ssdtRHUB10`, `ssdtTypeC9`
- **`SSDT-VOLKEYSS.aml`** → removed (requested; Samsung volume keys)
- **`SSDT-SMSG.aml`** → removed (requested; Samsung SMBus)
- **`SSDT-TPD0` / `SSDT-FPDT` / `SSDT-ALS0`** → Samsung touchpad, fingerprint, ambient light sensor
- **Kexts:** `RealtekRTL8111` (no ethernet), all `AirportItlwm*`, `AirportBrcmFixup`, `BrcmFirmwareData`, `BrcmPatchRAM3`, `BlueToolFixup`, `IntelBluetooth*`, `IntelBTPatcher`, `IO80211FamilyLegacy`, `IOSkywalkFamily`, `NootedBlue`, `WhateverGreen` (in the WEX phase), `CtlnaAHCIPort`, `EmeraldSDHC`, `SMCSuperIO`, `SMCLightSensor`, `HibernationFixup`, `FeatureUnlock`, `NoTouchID`, `USBWakeFixup`, `SystemProfilerMemoryFixup`, `ForgedInvariant`, `HWPEnabler`, `DisplayMergeNub`, `EFICheckDisabler`, `XHCI-unsupported`
- **Samsung DeviceProperties:** BCM4360 WiFi spoof, Samsung panel EDID, OZ711 SD reader, Samsung model strings

### Added / replaced
- **WhateverXe 0.7.0** instead of WhateverGreen (Tiger Lake Xe-LP)
- **AMFIPass 1.4.1 Mod** (required for the WEX root patch)
- **HoRNDIS** enabled — replaces ethernet (Android USB tethering)
- **Dell-specific SSDT-PNLF** (backlight)
- **layout-id 11** for ALC236
- **DVMT 60 MB workaround**: `-igfxdvmt` + `framebuffer-stolenmem`
- **New SMBIOS**: `MacBookAir9,1` (2-core, closest match to i3-1115G4)
- **ACPI patches cleaned up**: only `_OSI→XOSI`, `GPRW→XPRW`, `HDAS→HDEF`

---

## 3. Generated SMBIOS

| Field | Value |
|---|---|
| SystemProductName | `MacBookAir9,1` |
| SystemSerialNumber | `FVFDV0L2MNHP` |
| MLB | `FVF051700GU0000JA` |
| SystemUUID | `E5840D9F-EF63-4C05-9DD9-323614F41952` |
| ROM | `e2b26d551c41` (this laptop's WiFi MAC) |

> Generated with `macserial` (OpenCore 1.0.7); MLB checksum is valid.
> To regenerate: `./macserial -m MacBookAir9,1 -n 1`, then replace those 4 fields
> under `PlatformInfo > Generic`.

---

## 4. Two config phases

This EFI ships **2 configs** because WhateverXe only runs on macOS **12.7.6**,
while the recovery image is 12.5.1.

| File | When | GPU stack | boot-args |
|---|---|---|---|
| `config.plist` | **installation phase** (currently active) | WhateverGreen + VESA | `-v keepsyms=1 -igfxvesa watchdog=0 -vi2c-force-polling alcid=11` |
| `config-WEX.plist` | **after macOS 12.7.6 is installed** | WhateverXe + AMFIPass | `-v -allow3d -disablegfxfirmware -igfxdvmt keepsyms=1 -amfipassbeta` |

Switching phase (from Linux, USB mounted):
```bash
cd /run/media/$USER/<USB>/EFI/OC
cp config.plist config-installer-backup.plist
cp config-WEX.plist config.plist
```

| Arg | Purpose |
|---|---|
| `-igfxvesa` | use the VESA framebuffer (no acceleration) — enough for installation |
| `-allow3d` | **WEX required** — enable Apple driver's 3D path |
| `-disablegfxfirmware` | **WEX required** — skip GPU firmware loading |
| `-igfxdvmt` | Dell DVMT is locked at 60 MB |
| `-vi2c-force-polling` | helps VoodooI2C when interrupts do not work |
| `watchdog=0` | disable watchdog panic |
| `keepsyms=1` | kernel symbols on panic (debug) |

`csr-active-config = 03080000` (0x803) — required for the WEX root patch.

> **Key quirks (fix for the `[EB|LOG:EXITBS:START]` freeze):**
> `EnableWriteUnprotector=true`, `RebuildAppleMemoryMap=false`,
> `DevirtualiseMmio=false`, `SetupVirtualMap=true`, `ProtectUefiServices=false`.
> Profile taken from a solved Tiger Lake report
> (github.com/nullmoth/1401/issues/102) — a wrong memory-map combination means
> the kernel never starts.
>
> ✅ **VERIFIED 2026-11-07 — this EFI boots into macOS Recovery on this
> Dell Inspiron 15 3511.**

---

## 5. Installation steps

### 5.1 BIOS (F2 at boot)
- **Secure Boot** → Disabled
- **SATA Operation** → AHCI
- **Fast Boot** → Thorough
- **Virtualization** → Enabled (optional)
- Save & exit

### 5.2 Create the USB (from Linux)
```bash
cd /home/ditzz/Documents/project/efi-dell-3511/installer
sudo bash tulis-ke-usb.sh BaseSystem-3.0GiB.img /dev/sdX    # USB >= 4 GB
```
Check the device first: `lsblk -o NAME,SIZE,TYPE,MODEL`

The image already contains its own GPT: partition 1 is the **EFI (FAT32 200 MB)**
and partition 2 is the HFS+ recovery volume. The script writes the image, fixes
the backup GPT, then copies `EFI/` onto the EFI partition.

> Legacy alternative: `sudo bash buat-usb.sh /dev/sdX` creates a plain FAT32
> partition and copies `EFI/` + `com.apple.recovery.boot/`. That path loads the
> DMG into a ramdisk.

### 5.3 Boot the installer
1. F12 → select the USB (mode **UEFI**)
2. OpenCore picker → select **macOS Recovery** / **macOS Base System** (Monterey **12.5.1 / 21G83**)
3. Recovery needs internet to download macOS 12.7.6 (~12 GB):
   - plug in an Android phone → enable **USB Tethering**
   - HoRNDIS appears as an Ethernet interface
4. `Disk Utility` → **erase only the target partition/free space** as **APFS** (GUID)
5. `Reinstall macOS Monterey` → select that volume → wait

> ⚠️ **Do not erase the whole disk.** On a dual-boot machine that destroys
> Fedora and Windows. Free up space first (shrink a partition), then erase only
> the new empty partition.

> The installer pulls **12.7.6 (21G1320)** from Apple's catalog — that is the
> build WhateverXe requires. After it finishes, check  → About This Mac.
> If it is still 12.5.1, run **System Update** to 12.7.6 **before** installing
> WhateverXe Graphics.

### 5.4 After macOS is installed
1. Boot from the USB again, then copy EFI to the SSD EFI partition:
   ```bash
   diskutil list                     # find disk0s1 (EFI)
   sudo diskutil mount disk0s1
   cp -R /Volumes/OC-INSTALLER/EFI /Volumes/EFI/
   ```
2. **Required for GPU acceleration** — install the graphics package:
   ```
   open WhateverXe-Graphics-0.4.0.pkg from the USB → install → restart
   ```
   After the restart: Metal, OpenGL, H.264/HEVC decode, HDMI and brightness work.

---

## 6. Not working / notes

| Feature | Status |
|---|---|
| WiFi RTL8821CE | ❌ no driver. Use USB tethering, a USB WiFi dongle, or swap the card for Intel AX210 / Broadcom |
| Bluetooth RTL8821CE | ❌ unsupported |
| Sleep/wake | ⚠️ not fully tested (WEX: system sleep still under research) |
| iMessage/FaceTime | ⚠️ needs a valid serial + Apple ID (outside EFI scope) |
| Sidecar/AirPlay to a Mac | ❌ needs WiFi |
| HDMI | ✅ after the WEX root patch |
| Fn brightness | ✅ SSDT-PNLF + BrightnessKeys (after root patch) |

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| Stuck at `[EB|#LOG:EXITBS:START]` | ✅ **Solved and verified** on this laptop with the Tiger Lake quirk profile: `EnableWriteUnprotector=true`, `RebuildAppleMemoryMap=false`, `DevirtualiseMmio=false`, `ProtectUefiServices=false` |
| `AppleIntelTGLGraphics` panic | make sure `WhateverGreen` is **not** enabled in the Kexts folder |
| Black screen after the picker | add `-igfxvesa` temporarily, or check DVMT |
| No audio | try `layout-id` 13 / 69 / 21 under `DeviceProperties` |
| Touchpad not working | Touchpad is **Goodix I2C HID** (`DELL0AB0`, `27C6:0D43`). Check that `SSDT-XOSI` + the `_OSI→XOSI` patch are active and `VoodooI2C` + `VoodooI2CHID` are enabled. If it still fails, try `force-polling` on I2C0 in `DeviceProperties`, or fall back to `VoodooPS2Mouse.kext` (PS/2 mode) |
| Touchpad works but no click | enable `VoodooI2CHID` (already enabled) + check `force-polling` |
| USB dead after install | remap with USBToolBox, then enable `USBMap.kext` |

---

## 8. Installer media

Two options, both in `installer/`:

| Media | Size | Min USB | Content | Install |
|---|---|---|---|---|
| `BaseSystem-3.0GiB.img` | 3.0 GiB | **4 GB** | Monterey 12.5.1 recovery volume (bootable, boots from disk) | online (~12 GB download) |
| `com.apple.recovery.boot/` | 653 MB | **1 GB** | same recovery, loaded into a **3.0 GiB ramdisk** | online |

```bash
cd /home/ditzz/Documents/project/efi-dell-3511/installer
sudo bash tulis-ke-usb.sh BaseSystem-3.0GiB.img /dev/sdX
```

> **Which one?** The `.img` boots the recovery straight from a disk partition, so
> no ramdisk is allocated — useful on this 4 GB machine, where a 3.0 GiB ramdisk
> leaves very little memory for the kernel.

> **Offline full installer:** cannot be built from Linux. Inspected
> `InstallAssistant.pkg` (Apple product `062-40406`): its `SharedSupport.dmg`
> only holds a *payload* volume (`com_apple_MobileAsset_MacSoftwareUpdate`)
> **without `boot.efi`** — not bootable. Combining BaseSystem + payload into a
> bootable installer is what `createinstallmedia` does, and that exists on macOS
> only. `InstallAssistant-Monterey-12.7.6.pkg` (12.4 GB) is archived separately
> in case a Mac / macOS VM becomes available.

Image provenance (for reproduction):
- `BaseSystem-3.0GiB.img` ← `macrecovery.py` (Monterey 12.5.1, build 21G83,
  verified against Apple's signed chunklist, 63/63 chunks) → `dmg2raw.py`

---

## 9. References
- WhateverXe — https://github.com/b00t0x/WhateverXe (0.7.0, supports Monterey 12.7.6)
- WhateverXe Graphics — https://github.com/b00t0x/WhateverXe-Graphics
- Base Samsung EFI — https://github.com/cost-12/Hackintosh-Samsung-Book-INTEL-CORE-I3-1115G4-11TH
- Dortania OpenCore Guide — https://dortania.github.io/OpenCore-Install-Guide/
- OpenCore 1.0.7 — https://github.com/acidanthera/OpenCorePkg
