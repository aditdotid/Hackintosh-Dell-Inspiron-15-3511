#!/usr/bin/env python3
"""
dmg2raw.py — konversi Apple UDIF (.dmg) menjadi raw disk image, murni Python.

Pengganti dmg2img (yang tidak tersedia / butuh root untuk install).
Mendukung chunk: zero, raw/copy, zlib, bzip2, LZMA, ADC tidak didukung.

Pakai:
    python3 dmg2raw.py BaseSystem.dmg BaseSystem.img
"""
import base64, bz2, lzma, os, plistlib, struct, sys, zlib

SECTOR = 512
KOLY = 512


def read_koly(f, size):
    """Ambil XML blkx. Tangani DMG yang 'tertanam' (xmlOffset absolut)."""
    f.seek(-KOLY, os.SEEK_END)
    k = f.read(KOLY)
    if k[:4] != b"koly":
        raise SystemExit("bukan file UDIF/DMG (signature 'koly' tidak ada)")
    xml_off, xml_len = struct.unpack(">QQ", k[0xD8:0xE8])

    if xml_off + xml_len <= size:          # normal
        f.seek(xml_off)
        return f.read(xml_len)

    # DMG tertanam: offset absolut terhadap container -> cari plist di ekor
    tail_len = min(size, 8 * 1024 * 1024)
    f.seek(size - tail_len)
    tail = f.read(tail_len)
    i = tail.rfind(b"<?xml")
    if i < 0:
        i = tail.rfind(b"<plist")
    if i < 0:
        raise SystemExit("XML blkx tidak ditemukan (offset koly tidak valid)")
    j = tail.find(b"</plist>", i)
    if j < 0:
        raise SystemExit("XML blkx terpotong")
    return tail[i:j + 8]


def parse_blkx(xml):
    pl = plistlib.loads(xml)
    rf = pl.get("resource-fork") or {}
    blocks = rf.get("blkx") or []
    out = []
    for b in blocks:
        data = b.get("Data")
        if isinstance(data, str):
            data = base64.b64decode(data)
        out.append((b.get("Name", "?"), data))
    return out


def parse_mish(buf):
    if buf[:4] != b"mish":
        raise SystemExit("blkx bukan 'mish'")
    first_sector, sector_count, data_start = struct.unpack(">QQQ", buf[8:32])
    run_count = struct.unpack(">I", buf[200:204])[0]
    runs = []
    off = 204
    for _ in range(run_count):
        typ, _cmt, sec, cnt, coff, clen = struct.unpack(">IIQQQQ", buf[off:off + 40])
        runs.append((typ, sec, cnt, coff, clen))
        off += 40
    return data_start, first_sector, runs


def _copy_stream(f, o, n, blk=4 << 20):
    """Salin n byte dari f ke o tanpa memuat seluruh chunk ke RAM."""
    while n > 0:
        b = f.read(min(n, blk))
        if not b:
            break
        o.write(b)
        n -= len(b)


def _inflate_stream(f, o, n, dec, blk=4 << 20):
    """Dekompres stream chunk secara bertahap (RAM aman)."""
    while n > 0:
        b = f.read(min(n, blk))
        if not b:
            break
        n -= len(b)
        o.write(dec.decompress(b))
    try:
        o.write(dec.flush())
    except AttributeError:
        pass


def convert(src, dst):
    with open(src, "rb") as f:
        size = os.fstat(f.fileno()).st_size
        xml = read_koly(f, size)
        blocks = parse_blkx(xml)

        total_out = 0
        with open(dst, "wb") as o:
            for name, buf in blocks:
                data_start, first_sector, runs = parse_mish(buf)
                for typ, sec, cnt, coff, clen in runs:
                    if typ == 0xFFFFFFFF:                     # terminator
                        break
                    if typ == 0x7FFFFFFE:                     # komentar
                        continue
                    sec = first_sector + sec                  # relatif ke awal disk
                    o.seek(sec * SECTOR)
                    if typ == 0x00000000:                     # zero fill
                        o.write(b"\0" * (cnt * SECTOR))
                    elif typ == 0x00000002:                   # ignore
                        pass
                    elif typ == 0x00000001:                   # raw/copy
                        f.seek(data_start + coff)
                        _copy_stream(f, o, clen)
                    elif typ == 0x80000005:                   # zlib
                        f.seek(data_start + coff)
                        _inflate_stream(f, o, clen, zlib.decompressobj())
                    elif typ == 0x80000006:                   # bzip2
                        f.seek(data_start + coff)
                        _inflate_stream(f, o, clen, bz2.BZ2Decompressor())
                    elif typ == 0x80000004:                   # lzma/xz
                        f.seek(data_start + coff)
                        _inflate_stream(f, o, clen, lzma.LZMADecompressor())
                    elif typ == 0x80000007:                   # LZFSE (opsional)
                        try:
                            import lzfse
                        except ImportError:
                            raise SystemExit("chunk LZFSE butuh modul lzfse")
                        f.seek(data_start + coff)
                        o.write(lzfse.decompress(f.read(clen)))
                    else:
                        raise SystemExit(f"tipe chunk tidak dikenal: {hex(typ)}")
                    total_out = max(total_out, (sec + cnt) * SECTOR)
            o.truncate(total_out)
    return total_out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    n = convert(sys.argv[1], sys.argv[2])
    print(f"OK -> {sys.argv[2]}  ({n/2**30:.2f} GiB)")
