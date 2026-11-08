#!/usr/bin/env python3
"""
Builder EFI OpenCore untuk Dell Inspiron 15 3511 (i3-1115G4 / Tiger Lake)
Target: macOS Monterey 12.7.6 + WhateverXe 0.7.0
Basis  : EFI Samsung Book (cost-12) yang sudah diadaptasi ke hardware Dell.
"""
import os, shutil, plistlib, subprocess, sys

BASE    = "/home/ditzz/Documents/project/efi-dell-3511"
SAMSUNG = f"{BASE}/efi-dellku/samsung-efi/EFI"
DELLXE  = f"{BASE}/efi-dell-3511-xe/EFI"
OCREL   = "/tmp/oc/X64/EFI"
WEX     = "/tmp/wex/WhateverXe.kext"
AMFIMOD = "/tmp/amfimod/AMFIPass.kext"
OUT     = f"{BASE}/EFI-Dell-3511-Monterey"

# ---------------------------------------------------------------- SMBIOS
SMBIOS = {
    "SystemProductName": "MacBookAir9,1",
    "SystemSerialNumber": "FVFDV0L2MNHP",
    "MLB": "FVF051700GU0000JA",
    "SystemUUID": "E5840D9F-EF63-4C05-9DD9-323614F41952",
    "ROM": bytes.fromhex("e2b26d551c41"),
}

# ---------------------------------------------------------------- ACPI
# Diambil dari EFI Dell sebelumnya (SSDT-PNLF versi Dell), sudah dibersihkan
# dari SSDT khusus Samsung (VOLKEYSS, SMSG, TPD0, FPDT, ALS0, BAT, dll).
ACPI_FILES = [
    "SSDT-PLUG.aml",        # CPU power management
    "SSDT-EC.aml",          # fake EC untuk AppleACPIEC
    "SSDT-PNLF.aml",        # backlight (wajib untuk WhateverXe)
    "SSDT-XOSI.aml",        # _OSI override
    "SSDT-PMC.aml",         # NVRAM support
    "SSDT-RHUB.aml",        # reset USB 500-series
    "SSDT-GPRW.aml",        # fix sleep/wake
    "SSDT-USBX.aml",        # properti power USB
    "SSDT-RTCAWAC.aml",     # RTC/AWAC fix
    "SSDT-SBUS-MCHC.aml",   # SMBus/MCHC
]

ACPI_PATCHES = [
    ("Change _OSI to XOSI",              b"_OSI", b"XOSI", b"DSDT"),
    ("change Method(GPRW,2,N) to XPRW",  b"GPRW", b"XPRW", b"DSDT"),
    ("Rename HDAS to HDEF (Audio)",      b"HDAS", b"HDEF", b"DSDT"),
]

# ---------------------------------------------------------------- KEXT
# (nama folder, enabled, min, max, comment)
KEXTS = [
    ("Lilu.kext",                                        True,  "",        "",        "Patch engine (WAJIB pertama)"),
    ("VirtualSMC.kext",                                  True,  "",        "",        "Emulasi SMC"),
    ("SMCProcessor.kext",                                True,  "",        "",        "Sensor CPU"),
    ("SMCBatteryManager.kext",                           True,  "",        "",        "Baterai"),
    ("WhateverXe.kext",                                  True,  "",        "",        "Akselerasi iGPU Xe-LP (Tiger Lake)"),
    ("AMFIPass.kext",                                    True,  "20.0.0",  "25.99.99","AMFI pass untuk root patch WEX"),
    ("AppleALC.kext",                                    True,  "",        "",        "Audio ALC236 (ALC3204)"),
    ("NVMeFix.kext",                                     True,  "",        "",        "Power management NVMe"),
    ("ECEnabler.kext",                                   True,  "",        "",        "Baca EC >8-bit (baterai)"),
    ("BrightnessKeys.kext",                              True,  "",        "",        "Fn brightness"),
    ("VoodooPS2Controller.kext",                         True,  "",        "",        "Keyboard PS2"),
    ("VoodooPS2Controller.kext/Contents/PlugIns/VoodooPS2Keyboard.kext", True, "", "", "Keyboard plugin"),
    ("VoodooI2C.kext",                                   True,  "",        "",        "I2C touchpad"),
    ("VoodooI2C.kext/Contents/PlugIns/VoodooGPIO.kext",  True,  "",        "",        "GPIO untuk I2C"),
    ("VoodooI2C.kext/Contents/PlugIns/VoodooI2CServices.kext", True, "", "", "I2C services"),
    ("VoodooI2C.kext/Contents/PlugIns/VoodooInput.kext", True,  "",        "",        "Input abstraction"),
    ("VoodooI2CHID.kext",                                True,  "",        "",        "Touchpad HID"),
    ("USBMap.kext",                                      False, "",        "",        "Port map (belum dimapping utk Dell - nonaktif)"),
    ("RestrictEvents.kext",                              True,  "",        "",        "Nama CPU / OTA"),
    ("CPUFriend.kext",                                   True,  "",        "",        "Power management"),
    ("CPUFriendDataProvider.kext",                       True,  "",        "",        "Profil PM i3-1115G4"),
    ("RTCMemoryFixup.kext",                              True,  "",        "",        "Fix RTC"),
    ("HoRNDIS.kext",                                     True,  "",        "",        "USB tethering Android (pengganti ethernet)"),
]

# ---------------------------------------------------------------- DRIVERS
DRIVERS = [
    ("OpenRuntime.efi",           True),
    ("HfsPlus.efi",               True),
    ("OpenCanopy.efi",            True),
    ("ResetNvramEntry.efi",       True),
    ("AudioDxe.efi",              True),
    ("FirmwareSettingsEntry.efi", True),
    ("OpenLinuxBoot.efi",         True),
    ("Ext4Dxe.efi",               True),
    ("btrfs_x64.efi",             True),
    ("UsbMouseDxe.efi",           True),
    ("OpenUsbKbDxe.efi",          False),
]

TOOLS = [("CleanNvram.efi", True), ("ResetSystem.efi", True), ("OpenShell.efi", True)]

BOOT_ARGS = ("-v -allow3d -disablegfxfirmware -igfxdvmt keepsyms=1 -amfipassbeta")


def kext_exec_path(kext_dir, bundle_path):
    """Baca CFBundleExecutable dari Info.plist."""
    p = os.path.join(kext_dir, "Contents", "Info.plist")
    if not os.path.exists(p):
        return ""
    with open(p, "rb") as f:
        info = plistlib.load(f)
    exe = info.get("CFBundleExecutable")
    return f"Contents/MacOS/{exe}" if exe else ""


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    for d in ("EFI/BOOT", "EFI/OC/ACPI", "EFI/OC/Drivers", "EFI/OC/Kexts",
              "EFI/OC/Tools", "EFI/OC/Resources"):
        os.makedirs(f"{OUT}/{d}", exist_ok=True)

    # --- bootloader ---
    shutil.copy2(f"{OCREL}/BOOT/BOOTx64.efi", f"{OUT}/EFI/BOOT/BOOTx64.efi")
    shutil.copy2(f"{OCREL}/OC/OpenCore.efi",  f"{OUT}/EFI/OC/OpenCore.efi")

    # --- drivers ---
    for name, _ in DRIVERS:
        src = None
        for cand in (f"{OCREL}/OC/Drivers/{name}", f"{SAMSUNG}/OC/Drivers/{name}"):
            if os.path.exists(cand):
                src = cand
                break
        if not src:
            print(f"!! driver tidak ditemukan: {name}")
            continue
        shutil.copy2(src, f"{OUT}/EFI/OC/Drivers/{name}")

    # --- tools ---
    for name, _ in TOOLS:
        src = f"{OCREL}/OC/Tools/{name}"
        if os.path.exists(src):
            shutil.copy2(src, f"{OUT}/EFI/OC/Tools/{name}")

    # --- resources (tema OpenCanopy) ---
    for sub in ("Font", "Image", "Label", "Audio"):
        s = f"{SAMSUNG}/OC/Resources/{sub}"
        if os.path.isdir(s):
            shutil.copytree(s, f"{OUT}/EFI/OC/Resources/{sub}", dirs_exist_ok=True)

    # --- ACPI ---
    for f in ACPI_FILES:
        shutil.copy2(f"{DELLXE}/OC/ACPI/{f}", f"{OUT}/EFI/OC/ACPI/{f}")

    # --- kexts ---
    for bundle, _, _, _, _ in KEXTS:
        top = bundle.split("/")[0]
        src = f"{SAMSUNG}/OC/Kexts/{top}"
        if top == "WhateverXe.kext":
            src = WEX
        elif top == "AMFIPass.kext":
            src = AMFIMOD
        elif top == "USBMap.kext":
            src = f"{DELLXE}/OC/Kexts/{top}"
        dst = f"{OUT}/EFI/OC/Kexts/{top}"
        if not os.path.exists(dst):
            if not os.path.exists(src):
                print(f"!! kext tidak ditemukan: {top}")
                continue
            shutil.copytree(src, dst)

    # --- config.plist ---
    with open(f"{SAMSUNG}/OC/config.plist", "rb") as f:
        cfg = plistlib.load(f)

    # buang komentar bawaan base EFI
    for k in [k for k in cfg if k.startswith("#")]:
        del cfg[k]

    # ---------- ACPI ----------
    cfg["ACPI"]["Add"] = [
        {"Comment": f, "Enabled": True, "Path": f} for f in ACPI_FILES
    ]
    cfg["ACPI"]["Patch"] = [
        {"Base": "", "BaseSkip": 0, "Comment": c, "Count": 0, "Enabled": True,
         "Find": find, "Limit": 0, "Mask": b"", "OemTableId": b"",
         "Replace": repl, "ReplaceMask": b"", "Skip": 0,
         "TableLength": 0, "TableSignature": sig}
        for c, find, repl, sig in ACPI_PATCHES
    ]
    cfg["ACPI"]["Delete"] = []

    # ---------- Booter ----------
    cfg["Booter"]["Quirks"].update({
        "AvoidRuntimeDefrag": True, "DevirtualiseMmio": True,
        "EnableWriteUnprotector": False, "ProtectUefiServices": True,
        "ProvideCustomSlide": True, "RebuildAppleMemoryMap": True,
        "SetupVirtualMap": True, "SyncRuntimePermissions": True,
        "EnableSafeModeSlide": True, "ResizeAppleGpuBars": -1,
    })

    # ---------- DeviceProperties ----------
    cfg["DeviceProperties"]["Add"] = {
        "PciRoot(0x0)/Pci(0x2,0x0)": {
            # DVMT Dell terkunci 60MB -> workaround WEX
            "framebuffer-patch-enable": bytes.fromhex("01000000"),
            "framebuffer-stolenmem":    bytes.fromhex("0000C003"),
            "AAPL,slot-name": "Internal@0,2,0",
        },
        "PciRoot(0x0)/Pci(0x1F,0x3)": {
            "layout-id": bytes.fromhex("0b000000"),   # 11 = ALC236/ALC3204
            "AAPL,slot-name": "Internal@0,31,3",
        },
    }
    cfg["DeviceProperties"]["Delete"] = {}

    # ---------- Kernel ----------
    add = []
    for bundle, enabled, mn, mx, comment in KEXTS:
        # path bundle relatif terhadap folder Kexts -> baca Info.plist-nya langsung
        exe = kext_exec_path(f"{OUT}/EFI/OC/Kexts/{bundle}", bundle)
        add.append({
            "Arch": "Any", "BundlePath": bundle, "Comment": comment,
            "Enabled": enabled, "ExecutablePath": exe,
            "MaxKernel": mx, "MinKernel": mn, "PlistPath": "Contents/Info.plist",
        })
    cfg["Kernel"]["Add"] = add

    cfg["Kernel"]["Patch"] = []

    cfg["Kernel"]["Quirks"].update({
        "AppleCpuPmCfgLock": False, "AppleXcpmCfgLock": True,
        "AppleXcpmExtraMsrs": False, "AppleXcpmForceBoost": False,
        "CustomSMBIOSGuid": True, "DisableIoMapper": True,
        "DisableIoMapperMapping": False, "DisableLinkeditJettison": True,
        "DisableRtcChecksum": False, "ExtendBTFeatureFlags": False,
        "PanicNoKextDump": True, "PowerTimeoutKernelPanic": True,
        "ProvideCurrentCpuInfo": True, "SetApfsTrimTimeout": -1,
        "XhciPortLimit": False,
    })

    # ---------- Misc ----------
    cfg["Misc"]["Boot"].update({
        "HideAuxiliary": True, "LauncherOption": "Short", "PickerMode": "External",
        "PickerVariant": "Acidanthera\\GoldenGateExt", "PickerAttributes": 147,
        "ShowPicker": True, "Timeout": 5, "TakeoffDelay": 0,
        "PollAppleHotKeys": True, "PickerAudioAssist": False,
    })
    cfg["Misc"]["Security"].update({
        "SecureBootModel": "Disabled", "Vault": "Optional",
        "DmgLoading": "Signed", "ScanPolicy": 0, "BlacklistAppleUpdate": True,
    })
    cfg["Misc"]["Debug"]["Target"] = 0

    # ---------- NVRAM ----------
    apple = cfg["NVRAM"]["Add"].setdefault("7C436110-AB2A-4BBB-A880-FE41995C9F82", {})
    apple["boot-args"] = BOOT_ARGS
    apple["csr-active-config"] = bytes.fromhex("03080000")
    apple["prev-lang:kbd"] = "en-US:0"
    apple["run-efi-updater"] = "No"
    apple["ForceDisplayRotationInEFI"] = 0
    oc = cfg["NVRAM"]["Add"].setdefault("4D1FDA02-38C7-4A6A-9CC6-4BCCA8B30102", {})
    oc["revcpu"] = 1
    oc["revcpuname"] = "3.00GHz Intel Core i3 Dual-Core"
    oc["revpatch"] = "sbvmm,cpuname"

    # ---------- PlatformInfo ----------
    g = cfg["PlatformInfo"]["Generic"]
    g.update(SMBIOS)
    g["SpoofVendor"] = True
    g["ProcessorType"] = 0
    g["SystemMemoryStatus"] = "Auto"
    cfg["PlatformInfo"]["UpdateSMBIOSMode"] = "Custom"
    cfg["PlatformInfo"]["Automatic"] = True

    # ---------- UEFI ----------
    cfg["UEFI"]["Drivers"] = [
        {"Arguments": "", "Comment": n, "Enabled": e, "LoadEarly": False,
         "Path": n} for n, e in DRIVERS
    ]
    cfg["UEFI"]["Output"].update({
        "Resolution": "1920x1080", "ProvideConsoleGop": True,
        "TextRenderer": "BuiltinGraphics", "DirectGopRendering": False,
        "UIScale": -1,
    })
    cfg["UEFI"]["Quirks"].update({
        "EnableVectorAcceleration": True, "ReleaseUsbOwnership": True,
        "RequestBootVarRouting": True, "ResizeGpuBars": -1,
        "DisableSecurityPolicy": True,
    })
    cfg["UEFI"]["APFS"]["EnableJumpstart"] = True

    with open(f"{OUT}/EFI/OC/config.plist", "wb") as f:
        plistlib.dump(cfg, f, fmt=plistlib.FMT_XML, sort_keys=False)

    print(f"OK -> {OUT}")
    print(f"   ACPI   : {len(ACPI_FILES)} file")
    print(f"   Kexts  : {len([k for k in KEXTS if k[1]])} aktif / {len(KEXTS)} total")
    print(f"   Serial : {SMBIOS['SystemSerialNumber']} / {SMBIOS['MLB']}")


if __name__ == "__main__":
    main()
