# NOTICE — 크레딧과 라이선스 지도

## 이 키트가 배포하는 것 (전부 GPLv2+)

- `pack_psb.py` — rgss-switch의 `Empaquetar.ps1`(GPLv2+)을 Python으로 포팅·확장
- `widescreen_patch.py` — Scripts.rxdata 화면폭 패처 (원작)
- `lib/nx-psb-fixes.rb` — 스위치 입력/화면 런타임 심 (원작)
- `tests/nx_shims_test.rb` — RGSS 스텁 행동 테스트 (원작)

## 배포하지 않는 것 (사용자가 각자 입수)

| 구성 | 권리자 | 입수처 |
|---|---|---|
| 게임 본체(Pokémon Survivor Burst) | 원작자 + 포켓몬 IP 권리자(Nintendo·GAME FREAK·TPC) | itch.io (무료) |
| rgss-switch 엔진 (NRO + lib/ + mkxp.base.json) | randygil 외 (GPLv2+) | rgss-switch 릴리즈 |
| Pokémon Essentials / RPG Maker XP 스크립트 | 각 권리자 | 게임에 포함됨(비배포) |

## 핵심 원칙

1. 게임에서 파생된 파일(그래픽·오디오·Data·아이콘 원본)은 레포에 넣지 않는다.
   NRO 아이콘도 빌드 시 사용자 사본의 title.png에서 그 자리에서 만든다.
2. 엔진 바이너리(NRO)도 재배포하지 않는다 — 링크로 안내한다. (GPL은 재배포를
   의무하지 않고, 링크가 가장 단순하다. 재배포하려면 대응 소스 제공 의무가 붙는다.)
3. 닌텐도 SDK·폐쇄 자산 미사용. devkitPro/libnx(오픈소스) 기반 엔진만 사용.
4. 상표: 레포명·문서에서 "Pokémon" 등록상표는 필요 최소한으로, 비공식임을 명시.

## 감사

- **PSB 원작자** — 훌륭한 팬게임을 무료로 공개해 주신 것에
- **randygil / rgss-switch** — mkxp-z + CRuby 3.1의 스위치 네이티브 포트와 패키저
- **mkxp-z** (mkxp 계열, GPLv2+), **CRuby** (Ruby License/BSD-2), **SDL2** (zlib),
  **devkitPro/libnx** 커뮤니티
- **Pokémon Essentials** 커뮤니티 — 게임의 기반 키트
