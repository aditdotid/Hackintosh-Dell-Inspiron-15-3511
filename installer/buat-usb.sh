#!/usr/bin/env bash
# =============================================================================
#  Buat USB Installer Hackintosh — Dell Inspiron 15 3511
#  macOS Monterey 12.7.6  +  OpenCore 1.0.7
# =============================================================================
#  Cara pakai:
#     sudo bash buat-usb.sh /dev/sdX
#
#  PERINGATAN: SEMUA DATA DI /dev/sdX AKAN DIHAPUS.
#  Pastikan /dev/sdX adalah USB flash drive, BUKAN disk internal.
#  Cek dulu dengan:  lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL
# =============================================================================
set -euo pipefail

DEV="${1:-}"
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EFI_SRC="$PROJ/EFI-Dell-3511-Monterey/EFI"
REC_SRC="$PROJ/installer/com.apple.recovery.boot"
MNT="/mnt/usb-hackintosh"

if [[ -z "$DEV" ]]; then
    echo "Pemakaian: sudo bash $0 /dev/sdX"
    echo
    lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL
    exit 1
fi

if [[ ! -b "$DEV" ]]; then
    echo "ERROR: $DEV bukan block device."
    exit 1
fi

# --- pengaman: tolak disk yang menampung sistem berjalan ---
ROOT_DISK="$(lsblk -no PKNAME "$(findmnt -no SOURCE /)" | head -1)"
if [[ "/dev/$ROOT_DISK" == "$DEV" ]]; then
    echo "ERROR: $DEV adalah disk sistem yang sedang dipakai. Dibatalkan."
    exit 1
fi

if [[ ! -d "$EFI_SRC" ]]; then
    echo "ERROR: folder EFI tidak ditemukan di $EFI_SRC"
    exit 1
fi

echo "Target  : $DEV  ($(lsblk -dno SIZE,MODEL "$DEV" 2>/dev/null))"
echo "EFI     : $EFI_SRC"
echo "Recovery: $REC_SRC"
echo
read -rp "Ketik 'YA' untuk lanjut (semua data di $DEV hilang): " konfirmasi
[[ "$konfirmasi" == "YA" ]] || { echo "Dibatalkan."; exit 1; }

# --- lepas semua mount point di device ini ---
while read -r part; do
    [[ -n "$part" ]] && umount -f "/dev/$part" 2>/dev/null || true
done < <(lsblk -lno NAME "$DEV" | tail -n +2)

echo ">> Menghapus partisi lama..."
wipefs -a "$DEV" >/dev/null 2>&1 || true
dd if=/dev/zero of="$DEV" bs=1M count=16 status=none

echo ">> Membuat tabel partisi GPT + partisi FAT32 2 GB..."
parted -s "$DEV" mklabel gpt
parted -s "$DEV" mkpart ESP fat32 1MiB 2049MiB
parted -s "$DEV" set 1 esp on
sleep 1
PART="${DEV}1"
[[ -b "$PART" ]] || PART="${DEV}p1"
mkfs.vfat -F 32 -n "OC-INSTALLER" "$PART" >/dev/null

echo ">> Menyalin EFI + recovery image (bisa beberapa menit)..."
mkdir -p "$MNT"
mount "$PART" "$MNT"
cp -r "$EFI_SRC" "$MNT/EFI"
if [[ -d "$REC_SRC" ]]; then
    cp -r "$REC_SRC" "$MNT/com.apple.recovery.boot"
else
    echo "!! Folder recovery belum ada — lewati."
fi
# salin paket grafis (dipasang nanti dari dalam macOS)
if [[ -f "$PROJ/installer/WhateverXe-Graphics-0.4.0.pkg" ]]; then
    cp "$PROJ/installer/WhateverXe-Graphics-0.4.0.pkg" "$MNT/" || true
fi
sync
umount "$MNT"

echo
echo "=============================================================="
echo " SELESAI. USB siap dipakai."
echo " Isi USB : EFI/  +  com.apple.recovery.boot/"
echo
echo " Langkah berikutnya:"
echo "   1. Masuk BIOS Dell (F2): matikan Secure Boot, Fast Boot -> Thorough,"
echo "      SATA -> AHCI, simpan."
echo "   2. Tekan F12 saat boot -> pilih USB (UEFI)."
echo "   3. Di picker OpenCore pilih 'macOS Recovery'."
echo "=============================================================="
