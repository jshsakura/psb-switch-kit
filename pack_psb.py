#!/usr/bin/env python3
# PSB -> Switch SD packaging (faithful Python port of rgss-switch Empaquetar.ps1, loose-folder mode)
# Personal-use port of the unpacked "Pokemon Survivor Burst 9.0.3 Alt Windows" build.
import fnmatch, json, os, re, shutil, struct, subprocess, sys, time, unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
GAME = BASE / "game"                # assembled PC game folder
ENTREGA = BASE / "rgss-switch-0.1.0"
OUT = BASE / "out"

def verificar_todo():
    """배포 전 관문: 실제 ruby로 ① 전 .rb 문법검사 ② 심 행동 테스트.
    실패하면 예외로 빌드 중단 — 기기에 안 올리는 것이 원칙."""
    ruby = shutil.which("ruby")
    if not ruby:
        raise SystemExit("VERIFICA FALLO: ruby 없음 — sudo apt-get install ruby-full")
    rubies = [p for p in GAME.rglob("*.rb") if "lib" in p.parts or "Plugins" in p.parts]
    for p in rubies:
        r = subprocess.run([ruby, "-c", str(p)], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"VERIFICA FALLO: 문법오류 {p}:\n{r.stderr[:500]}")
    t = subprocess.run([ruby, str(BASE / "tests/nx_shims_test.rb"), str(GAME)],
                       capture_output=True, text=True)
    if t.returncode != 0:
        raise SystemExit("VERIFICA FALLO: 심 테스트 실패:\n" + t.stdout[-1500:] + t.stderr[-500:])
    print(f"   verifica: {len(rubies)} .rb 문법 OK + 심 테스트 통과")

verificar_todo()


SLUG = "pokemon-survivor-burst"
NOMBRE = "Pokémon Survivor Burst"
AUTOR = "Personal port"  # 브랜드명 금지(서비스 사칭 방지) — Nintendo 언급 없는 이름만
VERSION = "9.0.3"  # 게임 버전(NACP 표시). 엔진 버전(rgss-switch 0.1.0)과 무관하게 게임 기준.

NOCOPIAR = ["*.exe", "*.dll", "*.pdf", "*.lnk", "*.rar", "*.zip", "*.7z",
            "Thumbs.db", "desktop.ini", "*.parcial", ".nomedia"]
RECURSOS = ["Data", "Graphics", "Audio", "Fonts", "Movies"]
EXCLUIR = {"PBS", "DataBackup", "DataExport", "dist", "Credits"}
CLAVES_JUEGO = ["windowTitle", "defScreenW", "defScreenH", "rgssVersion",
                "SESourceCount", "BGMTrackCount", "midiSoundFont", "midiChorus",
                "midiReverb", "subImageFix", "enableBlitting", "maxTextureSize",
                "bindingNames", "inputRepeatStart", "inputRepeatDelay", "patches",
                "execName", "solidFonts", "fontSub", "useScriptNames",
                "JITEnable", "JITMaxCache", "JITMinCalls"]

def descarta(nombre):
    return any(fnmatch.fnmatch(nombre, p) for p in NOCOPIAR)

def lee_texto(p: Path) -> str:
    b = p.read_bytes()
    if b.startswith(b"\xef\xbb\xbf"):
        return b[3:].decode("utf-8")
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1252")

def limpia_json5(t: str) -> str:
    out, i, n, cadena, esc = [], 0, len(t), False, False
    while i < n:
        c = t[i]
        if cadena:
            out.append(c)
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': cadena = False
            i += 1; continue
        if c == '"':
            cadena = True; out.append(c); i += 1; continue
        if c == "/" and i + 1 < n:
            if t[i+1] == "/":
                while i < n and t[i] != "\n": i += 1
                continue
            if t[i+1] == "*":
                i += 2
                while i + 1 < n and not (t[i] == "*" and t[i+1] == "/"): i += 1
                i += 2; continue
        out.append(c); i += 1
    s = "".join(out)
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    return s

def lee_json5(p: Path):
    t = limpia_json5(lee_texto(p)).strip()
    return json.loads(t) if t else None

# ---------- 1. copy resources + loose dirs + root files ----------
def copia_arbol(origen: Path, destino: Path):
    n = 0
    for src in origen.rglob("*"):
        rel = src.relative_to(origen)
        if src.is_dir():
            continue
        if descarta(src.name):
            continue
        dst = destino / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    return n

dest = OUT / "switch" / SLUG
if dest.exists():
    shutil.rmtree(dest)
dest.mkdir(parents=True)

total = 0
print("1/4 recursos y carpetas sueltas")
for c in RECURSOS:
    if (GAME / c).is_dir():
        k = copia_arbol(GAME / c, dest / c)
        total += k
        print(f"   {c:10s} {k:5d} ficheros")

print("2/4 raiz + carpetas no-recurso (sueltas)")
for f in sorted(GAME.iterdir()):
    if f.is_file():
        if f.name.lower() == "mkxp.json":
            continue  # se compone
        if descarta(f.name):
            continue
        shutil.copy2(f, dest / f.name)
        total += 1
for d in sorted(GAME.iterdir()):
    if d.is_dir() and d.name not in RECURSOS and d.name not in EXCLUIR:
        k = copia_arbol(d, dest / d.name)
        total += k
        print(f"   {d.name:10s} {k:5d} ficheros (suelta)")

# mtime 제어: 플러그인 소스(2027-01-01)가 PluginScripts.rxdata(2025-01-01)보다 새면
# 부팅 시 1회 재컴파일 → 소스 수정본(예: background:aiwide)이 반영되고
# 이후 기기가 쓴 새 rxdata가 다시 최신이 되어 안정화된다. loose 모드라 쓰기 가능.
OLD = time.mktime((2027, 1, 1, 0, 0, 0, 0, 0, -1))
RX_OLD = time.mktime((2025, 1, 1, 0, 0, 0, 0, 0, -1))
nplug = 0
for f in (dest / "Plugins").rglob("*"):
    if f.is_file():
        os.utime(f, (OLD, OLD)); nplug += 1
rx = dest / "Data/PluginScripts.rxdata"
if rx.exists():
    os.utime(rx, (RX_OLD, RX_OLD))
print(f"   mtimes: {nplug} ficheros de Plugins -> 2027-01-01, PluginScripts.rxdata -> 2025-01-01 (recompila 1 vez al arrancar)")

# ---------- 3. mkxp.json (4 capas) ----------
print("3/4 mkxp.json compuesto")
cfg = lee_json5(ENTREGA / "mkxp.base.json")
capa2 = []
suyo = GAME / "mkxp.json"
if suyo.exists():
    j = lee_json5(suyo)
    for k, v in j.items():
        if k not in CLAVES_JUEGO:
            continue
        if k == "midiSoundFont" and v and not (GAME / str(v)).exists():
            print(f"   aviso: midiSoundFont '{v}' no existe; fuera")
            continue
        cfg[k] = v; capa2.append(k)
cfg["preloadScript"] = ["lib/nx-compat.rb", "lib/nx-teclado.rb", "lib/nx-rutas.rb", "lib/nx-psb-fixes.rb"]
cfg["rubyLoadpath"] = ["lib"]
if not cfg.get("windowTitle"):
    cfg["windowTitle"] = NOMBRE
body = json.dumps(cfg, ensure_ascii=False, indent=4)
cab = "\r\n".join([
    "// mkxp.json generado por pack_psb.py (adaptacion de Empaquetar.ps1).",
    "// Capas: 1 mkxp.base.json / 2 mkxp.json del juego / 3 perfil (generico) / 4 preload+loadpath.",
    f"// Juego: {NOMBRE}   slug: {SLUG}   familia: ruby31   perfil: generico",
    "",
])
mkxp_txt = cab + body + "\r\n"
(dest / "mkxp.json").write_bytes(mkxp_txt.encode("utf-8"))
print(f"   capa 2 (del juego): {', '.join(capa2)}")

# ---------- 4. motor: lib/ + NRO ----------
print("4/4 motor (lib/, NRO, icono)")
libd = dest / "lib"
copiado = copia_arbol(ENTREGA / "lib", libd)
print(f"   lib/: {copiado} ficheros")

# icono: title.png recortado a 256x256 baseline JPEG
icono = ENTREGA / "motor/icono.jpg"
try:
    from PIL import Image
    im = Image.open(GAME / "Graphics/Titles/title.png").convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((256, 256), Image.LANCZOS)
    tmp = dest.parent / "icono_psb.jpg"
    im.save(tmp, "JPEG", quality=90)  # baseline por defecto
    icono = tmp
    print("   icono: Graphics/Titles/title.png -> 256x256")
except Exception as e:
    print(f"   aviso icono ({e}); uso el del motor")

nro_src = (ENTREGA / "motor/rgss-switch.nro").read_bytes()
assert nro_src[0x10:0x14] == b"NRO0", "no es un NRO"
tam = struct.unpack_from("<I", nro_src, 0x18)[0]
assert nro_src[tam:tam+4] == b"ASET", "sin ASET"

def u64s(b): return struct.unpack_from("<QQ", b)

# ASET: [0x00 "ASET"][0x08 ver][0x10 icon_sz][0x18 nacp_off][0x20 nacp_sz][0x28 romfs_off][0x30 romfs_sz]
_ver, _isz, _noff, _nsz, rom_off, rom_sz = struct.unpack_from("<QQQQQQ", nro_src, tam + 8)
assert _nsz == 0x4000, f"NACP del motor inesperado: {_nsz}"
romfs = nro_src[tam + rom_off: tam + rom_off + rom_sz]
nacp = bytearray(nro_src[tam + _noff: tam + _noff + _nsz])
assert len(nacp) == 0x4000

def pon_cadena(b, off, tamcampo, s):
    b[off:off + tamcampo] = bytes(tamcampo)
    u = s.encode("utf-8")
    if len(u) >= tamcampo:
        raise ValueError(f"'{s}' no cabe en {tamcampo}B")
    b[off:off + len(u)] = u

for i in range(16):
    o = i * 0x300
    if nacp[o] == 0 and i not in (0, 5, 6):
        continue
    pon_cadena(nacp, o, 0x200, NOMBRE)
    pon_cadena(nacp, o + 0x200, 0x100, AUTOR)
pon_cadena(nacp, 0x3060, 0x10, VERSION)

ico = icono.read_bytes()
assert ico[:2] == b"\xff\xd8", "el icono no es JPEG"

cab = bytearray(0x38)
cab[0:4] = b"ASET"
struct.pack_into("<Q", cab, 0x08, 0x38)
struct.pack_into("<Q", cab, 0x10, len(ico))
struct.pack_into("<Q", cab, 0x18, 0x38 + len(ico))
struct.pack_into("<Q", cab, 0x20, len(nacp))
if len(romfs) > 0:
    struct.pack_into("<Q", cab, 0x28, 0x38 + len(ico) + len(nacp))
    struct.pack_into("<Q", cab, 0x30, len(romfs))

parcial = dest / (SLUG + ".nro.parcial")
with parcial.open("wb") as f:
    f.write(nro_src[:tam]); f.write(cab); f.write(ico); f.write(nacp)
    if len(romfs) > 0:
        f.write(romfs)
parcial.rename(dest / (SLUG + ".nro"))
print(f"   {SLUG}.nro ({(dest / (SLUG + '.nro')).stat().st_size:,} B) romfs del motor (arranque por hbmenu)")

# ---------- verificación ----------
print("\n=== verificación ===")
b = (dest / (SLUG + ".nro")).read_bytes()
tam2 = struct.unpack_from("<I", b, 0x18)[0]
assert b[0x10:0x14] == b"NRO0" and b[tam2:tam2+4] == b"ASET"
_v, isz, no, ns, _ro, rs = struct.unpack_from("<QQQQQQ", b, tam2 + 8)
assert ns == 0x4000
assert b[tam2 + 0x38: tam2 + 0x38 + 2] == b"\xff\xd8"        # icono JPEG tras la cabecera
assert isz + 0x38 == no                                        # nacp justo tras el icono
n2 = b[tam2 + no: tam2 + no + ns]
assert n2[:0x200].split(b"\0")[0].decode() == NOMBRE
assert n2[0x3060:0x3070].split(b"\0")[0].decode() == VERSION
print(f"   NRO ok: NRO0={tam2:,}B + ASET(icono {isz}B, NACP {ns}B, romfs {rs}B); nombre='{NOMBRE}' version='{VERSION}'")

mk = limpia_json5(lee_texto(dest / "mkxp.json"))
json.loads(mk)
print("   mkxp.json: JSON valido tras quitar comentarios")
assert cfg["preloadScript"] == ["lib/nx-compat.rb", "lib/nx-teclado.rb", "lib/nx-rutas.rb", "lib/nx-psb-fixes.rb"]
for s in cfg["preloadScript"]:
    assert (dest / s).exists(), f"falta {s}"
print("   preloadScript presente en lib/")

malos = [str(p) for p in dest.rglob("*") if p.is_file() and descarta(p.name)]
assert not malos, f"quedaron excluidos: {malos[:5]}"
nfiles = sum(1 for p in dest.rglob("*") if p.is_file())
bytes_ = sum(p.stat().st_size for p in dest.rglob("*") if p.is_file())
print(f"   instalacion: {nfiles:,} ficheros, {bytes_/2**30:.2f} GiB, cero .exe/.dll/desktop.ini")
assert (dest / "Game.ini").exists() and (dest / "soundfont.sf2").exists()
assert (dest / "Data/PluginScripts.rxdata").exists()
rx2 = dest / "Data/PluginScripts.rxdata"
recompila = any(f.stat().st_mtime > rx2.stat().st_mtime for f in (dest / "Plugins").rglob("*") if f.is_file())
print(f"   Plugins mas nuevos que PluginScripts.rxdata (recompilacion 1x al arrancar): {recompila}")
assert recompila
print("\nLISTO ->", dest)
