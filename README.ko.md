# PSB Switch Port Kit

변환 도구 모음: Windows용 팬게임 **Pokémon Survivor Burst**(itch.io 무료 배포)을
닌텐도 스위치 홈브루(rgss-switch 엔진)로 **개인용으로 변환**하기 위한 파이프라인.

[English documentation](README.md)

> **본 레포는 게임을 포함하지 않는다.** 게임 파일·파생 이미지·바이너리는
> 1바이트도 배포하지 않는다. 사용자가 itch.io에서 직접 받은 사본을 사용자
> 컴퓨터에서 변환한다. 본 키트는 변환 스크립트와 런타임 심, 검증 테스트만 담는다.

## 면책

- 비공식 개인용 변환 도구. Nintendo / GAME FREAK inc. / The Pokémon Company /
  캡콤 및 게임 원작자와 무관하며 어떠한 보증도 없다.
- 닌텐도 SDK·자산을 사용하지 않는다(홈브루 툴체인: devkitPro/libnx 기반 엔진).
- 게임은 각 저작권자의 소유물이며, 변환 결과물의 재배포는 금지된다.

## 요구 사양

- Python 3.10+ (`rubymarshal`, `evbunpack`, `pillow`) — 원본 언팩용
- Ruby 3.x (검증 게이트: `sudo apt-get install ruby-full`)
- rgss-switch v0.1.0 릴리즈 — `./rgss-switch-0.1.0/` 에 해제 (GPLv2+, 링크는 NOTICE 참조)
- Windows판 게임 — itch.io에서 다운로드 후 Enigma Virtual Box 언팩 → `./game/`

## 사용법

### 준비 (1회)

```bash
# Python 도구 (언팩 + 아이콘 생성)
python3 -m venv venv
venv/bin/pip install rubymarshal evbunpack pillow

# 검증 게이트용 ruby (없으면 빌드가 중단됨)
sudo apt-get install ruby-full        # Debian/Ubuntu
```

### 변환

```bash
# 1. 게임 확보: itch.io에서 PSB 배포본 다운로드 (무료, 사용자 본인 계정으로)

# 2. 언팩 (Enigma Virtual Box 풀기) → ./game/
venv/bin/evbunpack "게임실행파일.exe" game

# 3. 심 설치: 이름 입력(키보드) 문제와 화면 중앙 정렬 패치
mkdir -p game/lib && cp lib/nx-psb-fixes.rb game/lib/

# 4. (선택) 와이드 683x384 — 기본은 원본 512x384
venv/bin/python widescreen_patch.py game/Data/Scripts.rxdata 683

# 5. 변환 (빌드 전 자동 검증: 전 .rb 문법 + 심 행동 테스트, 실패 시 중단)
venv/bin/python pack_psb.py
#    산출: out/switch/pokemon-survivor-burst/
```

### 스위치 설치

```
out/switch/pokemon-survivor-burst/ 폴더를 통째로
SD카드 /switch/ (또는 /homebrew/) 에 복사
→ 게임(또는 hbmenu) 아이콘에 올려 R 길게 눌러 기동
   (앨범 애플릿 모드는 메모리 부족으로 금지)
부팅 시 플러그인 재컴파일이 1회(수 초) 실행될 수 있음 — 정상.
```

### 이름 입력 조작 (변환본)

| 버튼 | 동작 |
|---|---|
| **A / B** | 다음 단계 — 이름이 비어 있으면 화상키보드 호출, 입력돼 있으면 확정 |
| **X / Y** | 한 글자 지우기 |
| **L / R** | 화상키보드 다시 열기 (실수로 닫혔을 때) |
| 키보드 안 | 터치로 글자 입력 가능 |

## 런타임 심 (lib/nx-psb-fixes.rb)

플러그인 재컴파일과 무관하게 **프리로드로 항상 적용**되는 패치:

| 문제 | 조치 |
|---|---|
| 이름 입력이 물리 키보드 전용이라 콘솔에서 갇힘 | A/B = 다음 단계(빈 이름→화상키보드 재호출, 글자 있으면 확정), X/Y = 지우기, L/R = 키보드 재호출 |
| 스플래시 그림 좌측 쏠림 | 중앙 정렬 |
| 로드 화면(이어하기/새게임) 좌측 쏠림 | 뷰포트째 중앙 이동 |

버튼 배치 진실(mkxp-z keybindings.cpp + SDL): A동=`Input::B`, B남=`Input::C`,
X북=`Input::X`, Y서=`Input::A`, L/R=`Input::L/R`. `Input::START`는 없음.
터치는 스크립트에 노출되지 않음(화상 키보드 내부에서만 유효).

## 검증 게이트

`pack_psb.py` 는 빌드 전에 ① lib/Plugins 전 .rb `ruby -c` ② RGSS 스텁 행동
테스트(`tests/nx_shims_test.rb`)를 수행하고, 실패 시 빌드를 중단한다.
**검증 없이는 기기에 아무것도 안 간다**가 이 키트의 원칙이다.

## 라이선스

**GPLv2+** (`LICENSE`). rgss-switch(본 키트가 포팯하는 `Empaquetar.ps1` 포함)가
GPLv2+이므로 그 파생인 본 키트도 같은 조건으로 공개된다. 크레딧은 `NOTICE.md`.
