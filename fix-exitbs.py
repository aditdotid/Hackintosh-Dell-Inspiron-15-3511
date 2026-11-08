#!/usr/bin/env python3
"""
Perbaikan freeze [EB|LOG:EXITBS:START] pada Tiger Lake.

Basis: laporan solved di github.com/nullmoth/1401/issues/102
(EXITBS freeze pada laptop Tiger Lake = mismatch memory-map quirks,
 fixed dengan profil quirks dari Lenovo 15IHU6 i5-11320H).

Menghasilkan 2 config:
  config.plist       -> FASE INSTALASI : WhateverGreen + -igfxvesa (framebuffer VESA)
  config-WEX.plist   -> FASE PAKAI     : WhateverXe + -allow3d (butuh macOS 12.7.6)
"""
import plistlib, shutil, os

BASE = "/home/ditzz/Documents/project/efi-dell-3511"
EFI = f"{BASE}/EFI-Dell-3511-Monterey/EFI"
SAMSUNG = f"{BASE}/efi-dellku/samsung-efi/EFI"

BOOTER = {
    "AvoidRuntimeDefrag": True,
    "EnableWriteUnprotector": True,     # <- kunci perbaikan
    "RebuildAppleMemoryMap": False,     # <- kunci perbaikan
    "SetupVirtualMap": True,
    "DevirtualiseMmio": False,          # <- kunci perbaikan
    "AllowRelocationBlock": False,
    "ProtectUefiServices": False,
    "ProvideCustomSlide": True,
    "SyncRuntimePermissions": True,
    "EnableSafeModeSlide": True,
    "FixupAppleEfiImages": True,
    "ResizeAppleGpuBars": -1,
}

KERNEL_Q = {
    "AppleCpuPmCfgLock": False,
    "AppleXcpmCfgLock": True,
    "AppleXcpmExtraMsrs": True,
    "AppleXcpmForceBoost": False,
    "CustomSMBIOSGuid": True,
    "DisableIoMapper": True,
    "DisableIoMapperMapping": False,
    "DisableLinkeditJettison": True,
    "DisableRtcChecksum": True,
    "ExtendBTFeatureFlags": False,
    "PanicNoKextDump": True,
    "PowerTimeoutKernelPanic": True,
    "ProvideCurrentCpuInfo": True,
    "SetApfsTrimTimeout": -1,
    "XhciPortLimit": False,
}

ARGS_INSTALL = "-v keepsyms=1 -igfxvesa watchdog=0 -vi2c-force-polling alcid=11"
ARGS_WEX     = "-v -allow3d -disablegfxfirmware -igfxdvmt keepsyms=1 -amfipassbeta"


def kext_exe(kdir):
    p = os.path.join(kdir, "Contents", "Info.plist")
    if not os.path.exists(p):
        return ""
    d = plistlib.load(open(p, "rb"))
    e = d.get("CFBundleExecutable")
    return f"Contents/MacOS/{e}" if e else ""


def main():
    # 1) tambahkan WhateverGreen (dari EFI Samsung) kalau belum ada
    dst = f"{EFI}/OC/Kexts/WhateverGreen.kext"
    if not os.path.isdir(dst):
        shutil.copytree(f"{SAMSUNG}/OC/Kexts/WhateverGreen.kext", dst)
        print("+ WhateverGreen.kext ditambahkan")

    cfg = plistlib.load(open(f"{EFI}/OC/config.plist", "rb"))

    cfg["Booter"]["Quirks"].update(BOOTER)
    cfg["Kernel"]["Quirks"].update(KERNEL_Q)

    # 2) daftar kext: tambahkan WG, WEX tetap ada tapi dimatikan saat install
    add = cfg["Kernel"]["Add"]
    if not any(e["BundlePath"] == "WhateverGreen.kext" for e in add):
        idx = next(i for i, e in enumerate(add) if e["BundlePath"] == "WhateverXe.kext")
        add.insert(idx, {
            "Arch": "Any", "BundlePath": "WhateverGreen.kext",
            "Comment": "Framebuffer VESA saat instalasi (-igfxvesa)",
            "Enabled": True, "ExecutablePath": kext_exe(dst),
            "MaxKernel": "", "MinKernel": "", "PlistPath": "Contents/Info.plist",
        })
    for e in add:
        if e["BundlePath"] == "WhateverGreen.kext":
            e["Enabled"] = True
        if e["BundlePath"] == "WhateverXe.kext":
            e["Enabled"] = False
        if e["BundlePath"] == "AMFIPass.kext":
            e["Enabled"] = False          # belum perlu sebelum root patch

    nv = cfg["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
    nv["boot-args"] = ARGS_INSTALL
    plistlib.dump(cfg, open(f"{EFI}/OC/config.plist", "wb"),
                  fmt=plistlib.FMT_XML, sort_keys=False)
    print("config.plist        -> INSTALASI (WG + igfxvesa)")

    # 3) varian untuk setelah macOS terpasang
    cfg2 = plistlib.load(open(f"{EFI}/OC/config.plist", "rb"))
    for e in cfg2["Kernel"]["Add"]:
        if e["BundlePath"] == "WhateverGreen.kext":
            e["Enabled"] = False
        if e["BundlePath"] == "WhateverXe.kext":
            e["Enabled"] = True
        if e["BundlePath"] == "AMFIPass.kext":
            e["Enabled"] = True
    nv2 = cfg2["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
    nv2["boot-args"] = ARGS_WEX
    plistlib.dump(cfg2, open(f"{EFI}/OC/config-WEX.plist", "wb"),
                  fmt=plistlib.FMT_XML, sort_keys=False)
    print("config-WEX.plist    -> PAKAI (WhateverXe + allow3d)")


if __name__ == "__main__":
    main()
