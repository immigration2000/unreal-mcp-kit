---
name: setup-ue57
description: >-
  Set up Claude + Unreal Engine 5.7 using community MCP servers (VibeUE + optional UnrealClaude),
  because UE 5.7 has NO official ModelContextProtocol plugin (that ships in 5.8). Use when the
  user works in a UE 5.7 project and wants MCP/Claude Code control: install VibeUE (Blueprint/
  asset/editor tools, HTTP MCP on :8088) and optionally UnrealClaude (viewport capture + actor
  manipulation, MCP on :3000), connect Claude Code, and drop in project instructions.
  ONLY for UE 5.7 (no official MCP). For UE 5.8+, use the setup-ue58-mcp skill instead.
---

# UE 5.7 셋업 — 커뮤니티 MCP 서버 (VibeUE + UnrealClaude)

⚠️ **UE 5.7에는 공식 `ModelContextProtocol`이 없다**(5.8부터). 그래서 `setup-ue58-mcp`(공식 MCP)는 5.7에서 못 쓴다.
대신 **커뮤니티 서버**를 쓴다. 엔진 레벨 gotcha 지식은 `ue5-8-mcp` 스킬이 그대로 적용된다(server-agnostic, 5.7 커버).

## 서버 선택
- **VibeUE** (권장 기본) — 블루프린트/에셋/에디터 툴, 네이티브 C++ MCP 서버, **HTTP `http://127.0.0.1:8088/mcp`**. Python 불필요.
- **UnrealClaude** (선택 보완) — **뷰포트 캡쳐 + 액터 조작**, MCP **포트 3000**. Claude Code 인증 사용(별도 키 X).
- 둘은 보완 관계. 최소는 VibeUE만으로 시작, 시각 검증/액터 이동이 필요하면 UnrealClaude 추가.

---

## A. VibeUE 설치 (기본)
사전: UE 5.7+, Git, Node.js, MCP 클라이언트(Claude Code).
1. 플러그인 설치(택1):
   - **Fab**(권장): 에디터 Window > FAB → "VibeUE" → Add to Project.
   - **Git**: 프로젝트 `Plugins/`에서
     ```bash
     cd /path/to/YourProject/Plugins
     git clone https://github.com/kevinpbuckley/VibeUE.git
     cd VibeUE && buildplugin.bat
     ```
     자동감지 실패 시: `buildplugin.bat "C:\Program Files\Epic Games\UE_5.7"`
2. **Edit > Plugins**에서 VibeUE 활성 → 에디터 재시작.
3. **MCP 서버 켜기**: Project Settings > Plugins > VibeUE → **Enable MCP Server**(기본 ON), Port **8088**, API Key(선택 Bearer).
   서버는 **에디터가 열려 있을 때만** `http://127.0.0.1:8088/mcp`(Streamable HTTP)로 동작.
4. (선택) 무료 API 키 — vibeue.com 로그인 후 발급. **호스팅 지형 툴/인에디터 챗에만 필요**, 대부분의 에디터 툴은 키 없이 동작.

### Claude Code 연결 (VibeUE)
터미널에서 1회 등록(스킬은 mcp-remote 브리지로 http+auth를 중계):
```bash
claude mcp add --scope user --transport stdio VibeUE-Claude -- npx -y mcp-remote http://127.0.0.1:8088/mcp --transport http-only --allow-http --header "Authorization:Bearer YOUR_API_KEY"
```
- API 키 안 썼으면 `--header ...` 부분 생략.
- 특정 프로젝트로 한정하려면 `--scope project`.

### 프로젝트 지침 (VibeUE)
프로젝트 루트 `CLAUDE.md`에 VibeUE 샘플을 import(@ 지시어로 자동 인라인):
```markdown
# My Unreal Project
@Plugins/VibeUE/Content/samples/AGENTS.md.sample
```
(샘플엔 VibeUE 스킬·MCP 툴 사용법·로그 읽기 지침이 들어있고 업데이트에 맞춰 최신 유지됨.)

> 팁: 서버는 에디터가 켜져야 뜨므로, 켜기 전에도 툴 목록을 유지하려면 VibeUE **MCP Proxy**를 쓴다.

---

## B. UnrealClaude 추가 (뷰포트 캡쳐·액터 조작, 선택)
사전: Claude Code CLI(`npm install -g @anthropic-ai/claude-code`) + `claude auth login`.
1. 소스 클론(서브모듈 포함) + 빌드:
   ```bash
   git clone --recurse-submodules https://github.com/Natfii/UnrealClaude.git
   # Windows 빌드:
   Engine\Build\BatchFiles\RunUAT.bat BuildPlugin -Plugin="PATH\TO\UnrealClaude\UnrealClaude\UnrealClaude.uplugin" -Package="OUTPUT\PATH" -TargetPlatforms=Win64
   ```
2. 빌드 산출물을 프로젝트 `Plugins/UnrealClaude/`로 복사.
3. **MCP 브리지 의존성 설치**(블루프린트 툴에 필수):
   ```bash
   cd YourProject/Plugins/UnrealClaude/Resources/mcp-bridge && npm install
   ```
4. 에디터 실행 → 플러그인 자동 로드, **MCP 서버 포트 3000 자동 기동**. Claude Code 인증을 그대로 사용.

---

## C. 검증
에디터가 **열려 있는 상태**에서:
```bash
curl http://127.0.0.1:8088/mcp          # VibeUE (405/200 = 살아있음)
curl http://localhost:3000/mcp/status   # UnrealClaude (JSON = OK)
```
Claude Code에서 `/mcp`로 연결 서버 확인 → "무슨 툴 쓸 수 있어?" 또는 간단 작업(에셋 나열 등)으로 실동작 확인.

## 5.8과의 차이 요약
- 서버: 공식 내장 X → VibeUE(:8088) [+ UnrealClaude(:3000)]
- 설치: `.uproject` 토글 X → `Plugins/`에 **소스 클론+빌드**(buildplugin.bat / RunUAT), UnrealClaude는 **npm install** 필요
- 연결: `.mcp.json` 자동 X → `claude mcp add`(mcp-remote) / 지침은 `@AGENTS.md.sample` import
- 서버는 **에디터가 열려 있을 때만** 동작

## 흔한 문제
- 툴 안 뜸: 플러그인 활성+재시작 확인, VibeUE MCP 서버 ON 확인. UnrealClaude는 `mcp-bridge`에서 `npm install` 했는지.
- UnrealClaude 서버 안 뜸: 포트 3000 사용 중인지, Output Log `LogUnrealClaude` 확인.
- OneDrive/Dropbox 동기화 폴더에 두면 요청 hang 가능 → 로컬 디스크로.

## 출처
- VibeUE 5.7 아카이브: https://www.vibeue.com/v5-7/docs/installation , https://www.vibeue.com/v5-7/docs/ai-clients
- UnrealClaude: https://github.com/Natfii/UnrealClaude
