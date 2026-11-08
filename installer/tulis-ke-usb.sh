#!/usr/bin/env bash
# =============================================================================
#  Tulis image installer macOS ke USB, lalu pasang EFI OpenCore.
#
#  Pakai:
#     sudo bash tulis-ke-usb.sh <image.img> /dev/sdX
#
#  Contoh:
#     sudo bash tulis-ke-usb.sh SharedSupport-12.2GiB.img /dev/sdc   # full installer, USB >= 16 GB
#     sudo bash tulis-ke-usb.sh BaseSystem-3.0GiB.img     /dev/sdc   # recovery, USB >= 4 GB
#
#  Image sudah berisi GPT sendiri: partisi 1 = EFI (FAT32 200 MB),
#  partisi 2 = volume macOS. Jadi tidak perlu format/parted.
# =============================================================================
set -euo pipefail

IMG="${1:-}"; DEV="${2:-}"
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EFI_SRC="$PROJ/EFI-Dell-3511-Monterey/EFI"
MNT=/mnt/usb-macos

if [[ -z "$IMG" || -z "$DEV" ]]; then
    echo "Pakai: sudo bash $0 <image.img> /dev/sdX"
    echo; lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL
    exit 1
fi
[[ -f "$IMG" ]] || { echo "ERROR: image tidak ada: $IMG"; exit 1; }
[[ -b "$DEV" ]] || { echo "ERROR: $DEV bukan block device"; exit 1; }
[[ -d "$EFI_SRC" ]] || { echo "ERROR: folder EFI tidak ada: $EFI_SRC"; exit 1; }

# tolak partisi (harus disk utuh) & disk sistem
[[ "$(lsblk -dno TYPE "$DEV")" == "disk" ]] || { echo "ERROR: berikan disk utuh (mis. /dev/sdc), bukan partisi"; exit 1; }
ROOT_DISK="$(lsblk -no PKNAME "$(findmnt -no SOURCE /)" | head -1)"
[[ "/dev/$ROOT_DISK" == "$DEV" ]] && { echo "ERROR: $DEV adalah disk sistem. Dibatalkan."; exit 1; }

IMG_B=$(stat -c%s "$IMG"); DEV_B=$(blockdev --getsize64 "$DEV")
echo "Image  : $IMG  ($((IMG_B/1024/1024)) MiB)"
echo "Target : $DEV  ($((DEV_B/1024/1024)) MiB)  $(lsblk -dno MODEL "$DEV" 2>/dev/null)"
if (( DEV_B < IMG_B )); then
    echo "ERROR: USB terlalu kecil. Butuh minimal $(( (IMG_B+1024*1024-1)/1024/1024 )) MiB."
    exit 1
fi
echo
read -rp "Ketik 'YA' untuk menulis (SEMUA DATA di $DEV hilang): " ok
[[ "$ok" == "YA" ]] || { echo "Dibatalkan."; exit 1; }

echo ">> menulis image (beberapa menit)..."
dd if="$IMG" of="$DEV" bs=8M conv=fsync status=progress
sync

# perbaiki backup GPT agar sesuai ukuran USB sebenarnya
if command -v sgdisk >/dev/null; then
    echo ">> memperbaiki backup GPT..."; sgdisk -e "$DEV" >/dev/null 2>&1 || true
fi
partprobe "$DEV" 2>/dev/null || blockdev --rereadpt "$DEV" 2>/dev/null || true
sleep 2

# cari partisi EFI (partisi 1)
PART=""
for p in "${DEV}1" "${DEV}p1"; do [[ -b "$p" ]] && PART="$p" && break; done
[[ -n "$PART" ]] || { echo "ERROR: partisi EFI tidak muncul."; exit 1; }

echo ">> memasang EFI OpenCore ke $PART ..."
mkdir -p "$MNT"
mount "$PART" "$MNT"
rm -rf "$MNT/EFI"
cp -r "$EFI_SRC" "$MNT/EFI"
sync
umount "$MNT"

echo
echo "=============================================================="
echo " SELESAI."
echo " USB berisi: partisi EFI (OpenCore) + volume macOS"
echo
echo " Langkah:"
echo "   1. BIOS (F2): Secure Boot OFF, SATA AHCI, Fast Boot Thorough"
echo "   2. F12 -> pilih USB (UEFI)"
echo "   3. Picker OpenCore -> pilih 'Install macOS Monterey' / 'macOS Base System'"
echo "=============================================================="
