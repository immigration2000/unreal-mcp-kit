---
name: setup-ue58-mcp
description: >-
  Bootstrap a new Unreal Engine 5.8 project for official ModelContextProtocol (Unreal MCP)
  work in one step. Use when the user opens Claude Code in a UE project folder and asks to
  "set up MCP", "셋업", "wire up Unreal MCP", enable the MCP plugins/toolsets, generate
  .mcp.json, or drop in the CLAUDE.md playbook. Enables ModelContextProtocol + EditorToolset
  (and optional Niagara/UMG/Physics toolsets) in the .uproject, writes .mcp.json, and copies
  the CLAUDE.md template.
---

# UE 5.8 MCP 프로젝트 원클릭 셋업

사용자가 언리얼 프로젝트 폴더에서 "MCP 셋업해줘" / "셋업" 등을 요청하면, 아래 순서로 처리한다.

## 실행 절차
1. 현재 작업 폴더(또는 사용자가 지정한 폴더)에 `.uproject`가 있는지 확인. 없으면 프로젝트 루트로 이동하라고 안내.
2. 이 스킬 폴더 안의 `scripts/setup_project.py`를 실행 (경로는 이 SKILL.md와 같은 폴더 기준):
   ```bash
   # 플러그인으로 설치된 경우
   python "${CLAUDE_PLUGIN_ROOT}/skills/setup-ue58-mcp/scripts/setup_project.py" .
   # ~/.claude/skills 에 직접 둔 경우
   python "$HOME/.claude/skills/setup-ue58-mcp/scripts/setup_project.py" .
   ```
   - Niagara/UMG/Physics 작업이 예상되면 플래그 추가: `--niagara --umg --physics`
   - 포트를 바꿔야 하면 `--port <n>` (기본 8000).
   - 기존 `CLAUDE.md`를 덮어써야 하면 `--force`.
3. 스크립트가 하는 일:
   - **`.uproject.bak` 백업** 후, `Plugins`에 **`ModelContextProtocol` + `EditorToolset`**(+옵션) 을 `Enabled:true`로 추가/보정. 기존 플러그인은 삭제하지 않음(없는 것만 추가, 꺼진 것만 켬). (idempotent)
   - 프로젝트 루트에 **`.mcp.json`**(`unreal-mcp` → `http://127.0.0.1:8000/mcp`) 작성.
   - **`CLAUDE.md`** 템플릿을 프로젝트 루트에 복사(이미 있으면 건너뜀).
   - **Auto Start Server 자동 설정** — `Config/DefaultEditorPerProjectUserSettings.ini`에 `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings] bAutoStartServer=True` 병합(기존 내용 보존). `--no-autostart`로 생략.
4. 스크립트 출력의 "남은 단계"를 사용자에게 그대로 전달:
   - **에디터 (재)시작**해 플러그인 로드(첫 셋업 1회 필수). Auto Start Server는 위에서 설정됐으니 **재시작만 하면 서버 자동 기동**(수동 체크 불필요).
5. **셋업 검증:** 에디터를 켠 뒤 `--verify`로 파일/서버 상태를 자동 진단.
   ```bash
   python "<스크립트 경로>/setup_project.py" . --verify
   ```
   - **툴셋 로드 여부의 정식 판정은 연결된 에이전트가 `list_toolsets`를 직접 호출**하는 것이다(에이전트 자체 MCP 클라이언트라 가장 정확). 작업 툴셋(SceneTools/ActorTools/BlueprintTools 등, ~19개)이 보이면 성공, `AgentSkillToolset` 하나뿐이면 `EditorToolset` 미로드.
   - `--verify --deep`는 이 UE 5.8 서버에선 raw HTTP로 툴셋 결과를 못 받아(`tools/call`=SSE·빈 POST 본문) **안내만 출력**한다. 판정에 쓰지 말 것 — 툴셋 확인은 위 `list_toolsets`가 정답.

## 핵심 주의 (검증됨)
- **`EditorToolset`을 꼭 켜야** 씬/액터/블루프린트 툴셋이 뜬다. 안 켜면 `list_toolsets`에 `AgentSkillToolset` 하나뿐이고, 이때 `RefreshTools`는 소용없다(플러그인 활성 + 재시작이 정답).
- `.mcp.json`은 에디터 콘솔 `GenerateClientConfig` 없이 스크립트가 직접 써도 동일하게 동작한다(정적 파일).
- 엔진 레벨 gotcha는 별도 지식 스킬 `ue5-8-mcp`(전역 설치) 참고.

## 왜 이렇게?
매 프로젝트마다 손으로 플러그인 켜고 `.mcp.json`/`CLAUDE.md` 넣는 수고를 없애기 위함.
지식 스킬은 `~/.claude/skills/`에 한 번만 두면 전 프로젝트 공유되고, 이 셋업 스킬로 프로젝트별 파일만 한 방에 깐다.
