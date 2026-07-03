# unreal-mcp-kit

> **English (quick):** A Claude Code kit that sets up Unreal Engine 5.8's official MCP
> (`ModelContextProtocol`) in one command and injects engine-level gotcha knowledge.
> Install: `/plugin marketplace add immigration2000/unreal-mcp-kit` → `/plugin install unreal-mcp-kit@unreal-mcp-kit`
> (or clone + `install.sh`/`install.ps1`). Then, in a UE project folder, say "set up UE MCP".
> The `setup-ue58-mcp` script enables `ModelContextProtocol` + `EditorToolset` in the `.uproject`
> (preserving existing plugins, with `.uproject.bak` backup), writes `.mcp.json`, and drops in
> `CLAUDE.md`. Run `python .../setup_project.py . --verify` to diagnose. Requires UE 5.8 + Python 3.
> The `ue5-8-mcp` skill adds reflection rules, crash patterns, and the tool-search workflow. MIT.

**UE 5.8 공식 MCP(ModelContextProtocol)를 한 방에 셋업하고, Claude에게 언리얼 엔진 함정 지식을 주입하는 Claude Code 키트.**

매 프로젝트마다 플러그인 켜고 `.mcp.json` 만들고 `CLAUDE.md` 넣는 반복 작업을, 프로젝트 폴더에서 **"UE MCP 셋업해줘"** 한마디로 끝냅니다.

포함된 스킬 2개:
- **`setup-ue58-mcp`** — `.uproject`에 `ModelContextProtocol` + `EditorToolset` 활성화, `.mcp.json` 생성, `CLAUDE.md` 복사까지 자동(idempotent).
- **`ue5-8-mcp`** — reflection 규칙·크래시 패턴·tool-search 워크플로우 등 엔진 레벨 gotcha를 미리 주입해 매 세션 재발견 방지.

---

## 설치 (3가지 중 택1)

### A. 플러그인 마켓플레이스 (권장, 자동 업데이트)
Claude Code에서:
```
/plugin marketplace add immigration2000/unreal-mcp-kit
/plugin install unreal-mcp-kit@unreal-mcp-kit
```
> 리포를 push한 뒤 GitHub 사용자명/리포명에 맞게 위 명령을 바꾸세요.

### B. 클론 + 설치 스크립트 (스킬을 `~/.claude/skills`로 복사)
```bash
git clone https://github.com/immigration2000/unreal-mcp-kit.git
cd unreal-mcp-kit
# Windows
powershell -ExecutionPolicy Bypass -File .\install.ps1
# macOS/Linux
bash install.sh
```

### C. 개발/테스트용 (설치 없이 바로 로드)
```bash
claude --plugin-dir ./unreal-mcp-kit/plugins/unreal-mcp-kit
```

설치 후 Claude Code 재시작 또는 `/reload-plugins`.

---

## 사용법

1. **새 UE 5.8 프로젝트 폴더**에서 Claude Code 열기.
2. 이렇게 말하기: **"이 프로젝트 UE MCP 셋업해줘"** (또는 `/unreal-mcp-kit:setup-ue58-mcp`).
   - Niagara/UMG/Physics도 필요하면 "니아가라·UMG·피직스 툴셋도" 라고 덧붙이면 `--niagara --umg --physics`로 실행됩니다.
   - 스크립트가 `.uproject.bak` 백업 후, 기존 플러그인은 보존하고 필요한 것만 추가합니다.
3. **에디터 (재)시작**해 플러그인 로드 (첫 셋업 시 1회 필수).
   - **Auto Start Server는 셋업이 자동 설정**합니다(`Config/DefaultEditorPerProjectUserSettings.ini`) → 재시작만 하면 서버가 자동 기동. 수동 체크 불필요.
4. **검증(권장):** 셋업이 조용히 반쪽만 됐는지 자동 진단.
   ```bash
   python plugins/unreal-mcp-kit/skills/setup-ue58-mcp/scripts/setup_project.py . --verify
   ```
   - 플러그인 활성 / `.mcp.json` / 서버 응답을 OK·실패로 보고하고 실패 시 조치를 알려줍니다.
5. 통과하면 프로젝트 루트에서 Claude Code로 `list_toolsets` 확인 → 작업 시작.

### 스크립트 직접 실행 옵션
```bash
python .../setup_project.py .                       # 셋업 (현재 폴더)
python .../setup_project.py . --niagara --umg --physics   # 옵션 툴셋
python .../setup_project.py . --verify              # 진단 (파일 수정 안 함)
python .../setup_project.py . --verify --deep       # 안내만(이 서버는 raw HTTP 툴셋 프로브 미지원)
python .../setup_project.py . --force               # CLAUDE.md 덮어쓰기
python .../setup_project.py . --port 8000           # 포트 지정
python .../setup_project.py . --no-backup           # .uproject 백업 생략
python .../setup_project.py . --no-autostart        # Auto Start Server 자동설정 생략
```

---

## 이 킷이 해결하는 핵심 함정

- **`list_toolsets`에 `AgentSkillToolset` 하나만 뜨는 문제** → UE 5.8은 작업 툴셋을 개별 플러그인으로 제공. `.uproject`에 **`EditorToolset`을 켜야** 씬/액터/블루프린트 등 ~19개 툴셋이 등록됨. 이 상태에서 `RefreshTools`는 무효(플러그인 활성 + 재시작이 정답). → 셋업 스크립트가 자동 처리.
- **기존 플러그인 보존** — 스크립트는 `.uproject`의 기존 플러그인을 지우지 않고, 없는 것만 추가하고 꺼진 것만 켭니다.

---

## 안전

- 스크립트는 `.uproject`를 수정하므로 **실행 전 `git commit`** 권장(되돌리기 쉽게).
- MCP 서버는 **loopback(127.0.0.1) 전용, 인증 없음** — 외부 노출 금지.
- 에이전트에 파괴적 툴 자동승인 금지, feature 브랜치 작업 권장(`CLAUDE.md`에 규칙 포함).

## 요구 사항

- Unreal Engine **5.8** (공식 `ModelContextProtocol` 플러그인 내장; 소스빌드에서 검증됨).
- Claude Code (CLI 또는 데스크탑 앱 Code 탭).
- Python 3.8+ (셋업 스크립트 실행용).

## 크레딧 / 참고

- Epic 공식 문서: https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor
- 엔진 gotcha 접근법 참고(MIT): https://github.com/ibrews/ue5-mcp

## 라이선스

MIT — [LICENSE](LICENSE)
