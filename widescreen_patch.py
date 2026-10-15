#!/usr/bin/env python3
# Scripts.rxdata의 Settings::SCREEN_WIDTH 패치 (와이드 해상도용, 재사용 가능)
# 사용법: python3 widescreen_patch.py <Scripts.rxdata 경로> <너비픽셀>
# - 이미 패치된 값이면 다른 값으로 교체, 원본은 <경로>.orig 으로 자동 보존(최초 1회)
import sys, re, zlib, os
from rubymarshal.reader import load
from rubymarshal.writer import write

rxdata, width = sys.argv[1], int(sys.argv[2])
PAT = re.compile(rb"SCREEN_WIDTH(\s*)=\s*\d+")
backup = rxdata + ".orig"
if not os.path.exists(backup):
    import shutil; shutil.copy2(rxdata, backup)
    print(f"원본 백업: {backup}")

def inflate(d):
    try: return zlib.decompress(d), 15
    except Exception: return zlib.decompress(d, -15), -15

def deflate(src, wbits):
    return zlib.compress(src, 6) if wbits == 15 else (lambda c: c.compress(src)+c.flush())(zlib.compressobj(6, zlib.DEFLATED, -15))

with open(backup if False else rxdata, "rb") as f:   # 현재 파일 기준
    scripts = load(f)
before, after, hits = None, None, []
for s in scripts:
    src, wbits = inflate(bytes(s[2]))
    m = PAT.search(src)
    if not m: continue
    hits.append((s[0], s[1], m.group(0)))
    assert len(hits) == 1, f"대입이 {len(hits)}곳: {hits}"
    before = m.group(0)
    s[2] = deflate(PAT.sub(f"SCREEN_WIDTH\\1= {width}".encode(), src, count=1), wbits)
assert hits, "SCREEN_WIDTH 대입 없음 — Scripts.rxdata가 아님"
with open(rxdata, "wb") as f: write(f, scripts)
with open(rxdata, "rb") as f:
    for s in load(f):
        t, _ = inflate(bytes(s[2]))
        m = PAT.search(t)
        if m:
            after = m.group(0)
            assert s[0] == hits[0][0]
assert after == f"SCREEN_WIDTH  = {width}".encode()
print(f"패치 완료: 섹션 {hits[0][0]}({hits[0][1].decode(errors='replace')}) {before.decode()} -> {after.decode()}")
