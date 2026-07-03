---
name: ue5-8-mcp
description: >-
  Field manual of engine-level gotchas for driving Unreal Engine 5 through MCP. Server-agnostic:
  applies to UE 5.8's official ModelContextProtocol plugin AND UE 5.7 community servers
  (VibeUE, UnrealClaude). Use whenever working with UE5 / UE 5.7 / UE 5.8, Blueprints, Niagara,
  MetaSound, materials, UMG, level/actor editing, or any Unreal editor automation over MCP.
  Injects gotchas (silent no-ops, crash patterns, reflection rules) and the tool-search
  workflow so the agent does not rediscover them every session.
---

# UE 5.8 공식 MCP — 에이전트 필드 매뉴얼

UE 5.8에 내장된 Epic 공식 `ModelContextProtocol` 플러그인("Unreal MCP")으로 에디터를 구동할 때의
엔진 레벨 지식 모음. 서버 레벨 기능이 아니라 **엔진 자체의 함정**을 다룬다. 실제 툴 이름/스키마는
환경마다 다르므로 항상 `list_toolsets` / `describe_toolset`로 확인할 것.

> 핵심 명제 3가지: ① **무엇이 조용히 실패하는가** ② **무엇이 에디터를 크래시시키는가**
> ③ **무엇이 실제로 동작하는가(정확한 호출 순서)**.

---

## 1. 공식 플러그인 토폴로지 (UE 5.8)
- 플러그인 식별자 `ModelContextProtocol`(표시명 "Unreal MCP"), **Toolset Registry** 플러그인에 의존(자동 활성).
- ⚠️ **작업 툴셋은 별도 활성화 필요:** `.uproject`에 **`EditorToolset`을 켜야** 씬/액터/블루프린트 등 작업 툴셋이 등록된다. 안 켜면 `AgentSkillToolset` 하나만 보임(§2 참조).
- MCP 서버는 **에디터 프로세스 내부**에서 실행. 기본 바인딩 `http://127.0.0.1:8000/mcp`, serverInfo.name=`unreal-mcp`.
- 전송: **HTTP + SSE만 지원**. `stdio` / WebSocket 미지원.
- **loopback 전용, 인증 없음** → 외부 노출 금지.
- MCP **Resources / Prompts는 노출 안 함** (Tools만).
- 서버는 Tool 호출을 **게임 스레드에서 직렬 실행** → 클라이언트는 **중첩 Tool 호출을 보내면 안 됨**.

### 콘솔 명령 (에디터 콘솔, 백틱 `` ` ``)
| 명령 | 용도 |
|---|---|
| `ModelContextProtocol.StartServer [port]` | 서버 시작 (포트 선택) |
| `ModelContextProtocol.StopServer` | 서버 정지 |
| `ModelContextProtocol.RefreshTools` | 툴 레지스트리 재폴링 (툴셋 추가/핫리로드 후) |
| `ModelContextProtocol.GenerateClientConfig <Client\|All>` | 클라이언트 설정 파일 생성 |

- `GenerateClientConfig`의 클라이언트: `ClaudeCode`, `Cursor`, `VSCode`, `Gemini`, `Codex`, `All`.
- `ClaudeCode`로 생성하면 프로젝트 루트에 `.mcp.json` 작성:
  ```json
  { "mcpServers": { "unreal-mcp": { "type": "http", "url": "http://127.0.0.1:8000/mcp" } } }
  ```
- **에이전트는 `.mcp.json`이 있는 프로젝트 루트에서 실행**해야 연결됨.
- Editor Preferences > General > Model Context Protocol: `Auto Start Server`, `Server Port`(8000), `URL Path`(/mcp), `Enable Tool Search`(기본 true).

## 2. Tool Search 모드 (토큰 절약 핵심)
`Enable Tool Search`가 켜져 있으면 `tools/list`가 전체 스키마 대신 **메타툴 3개**만 반환:
- `list_toolsets` — 툴셋 이름/설명
- `describe_toolset` — 해당 툴셋의 툴 스키마
- `call_tool` — 이름으로 디스패치, 같은 턴에 결과 반환

**작업 패턴:** `list_toolsets` 1회 → 필요한 툴셋만 `describe_toolset` → `call_tool`. 전부 펼치면 스키마 수만 토큰을 쓴다.

### ⚠️ 툴셋은 기본 탑재가 아니다 (검증됨 2026-06-29, 소스빌드)
- UE 5.8은 작업 툴셋을 `Engine/Plugins/Experimental/Toolsets/` 아래 **개별 플러그인**으로 제공(약 26개): `EditorToolset`, `NiagaraToolsets`, `UMGToolSet`, `PhysicsToolsets`, `GASToolsets` … **전체 메타 = `AllToolsets`**.
- `.uproject`에 **`ModelContextProtocol`만** 켜면 의존성으로 딸려온 **`AgentSkillToolset` 하나만** `list_toolsets`에 뜬다(작업 툴셋 전무).
- `.uproject`에 **`EditorToolset` 추가 + 에디터 재시작** → `SceneTools`/`ActorTools`/`ObjectTools`/`MaterialTools`/`MaterialInstanceTools`/`BlueprintTools`/`StaticMeshTools`/`SkeletalMeshTools`/`AssetTools`/`PrimitiveTools`/`TextureTools`/`Data·Curve·StringTableTools`/`ProgrammaticToolset`/`EditorAppToolset`/`LogsToolset` 등 **~19개** 등록 확인.
- **함정:** 이 상태에서 `RefreshTools`는 **소용없다** — 등록할 Python 코드 자체가 로드 안 된 것이라 재폴링할 대상이 없음. 해결은 플러그인 활성화 + 재시작뿐.
- Niagara/UMG/Physics 작업이 필요하면 해당 툴셋 플러그인도 함께 활성화.

## 3. 리플렉션(reflection) 규칙 — 조용한 실패의 원천
- **이름 표기 정확성:** UE 리플렉션은 정확한 표기를 요구. 잘못된 케이싱/스펠은 **에러 없이 no-op**.
- **블루프린트 클래스 경로엔 `_C` 접미사** 필수: `/Game/X/BP_Foo.BP_Foo_C`. 빼면 클래스 못 찾음(조용히).
- **그래프 변경 3단계:** 노드 생성 → 핀 연결 → **컴파일**. 컴파일 빠뜨리면 반영 안 됨.
- **변수 기본값(내용물)은 툴로 안 채워질 때 Python으로 CDO에 넣는다.** 변수 생성 툴이 default 인자를 안 받으면 값이 빈 채로 남는다(사람이 Details 패널에 손으로 넣어야 하는 병목). 해결:
  - 순서 **변수 추가 → `compile_blueprint` → CDO에 `set_editor_property` → 저장 → read-back**. 컴파일 전엔 CDO에 프로퍼티가 없어 실패.
  - 클래스는 `_C`로 로드해 CDO를 얻고, 직접 대입 대신 `set_editor_property`(변경 이벤트+dirty).
  ```python
  import unreal
  bp = unreal.load_asset('/Game/BP/BP_Foo'); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
  cdo = unreal.get_default_object(unreal.load_object(None, '/Game/BP/BP_Foo.BP_Foo_C'))
  cdo.set_editor_property("Health", 100.0)      # 배열/구조체면 list/dict/struct
  unreal.EditorAssetSubsystem().save_asset('/Game/BP/BP_Foo')
  ```
- **프로퍼티 변경 후 `PostEditChangeProperty`** 필요한 경우 있음. 에디터/직렬화에 반영 안 되면 이걸 의심.
- **비동기 에셋 작업은 블로킹 안 함** → 생성 직후 바로 참조하면 아직 로드 전일 수 있음. 완료 확인 후 사용.

## 4. 크래시 패턴 (에디터 다운 = 미저장 작업 날아감)
- **참조 중인 메시/에셋 삭제** → 크래시. 삭제 전 의존성 그래프 확인, 참조 0일 때만.
- **액터 연타(rapid ops)** → 크래시. 대량 작업은 배치를 쪼개고 사이에 검증.
- **MetaSound: 스칼라를 오디오 핀에 직결**(예: Multiply 출력 → Audio 핀) → 크래시. 핀 타입 정확히.
- **Niagara / MetaSound는 편집 후 PIE 전에 Save** 안 하면 크래시/무동작.

### 모달 다이얼로그 = MCP 정지 (게임 스레드 블로킹)
- 모달(`FMessageDialog`)은 게임 스레드를 막는다. MCP 툴도 게임 스레드에서 직렬 실행되므로 **모달이 떠 있으면 MCP 서버가 응답을 멈춘다**(연결 hang) → 에이전트가 그 창을 못 닫는다. 사람이 눌러야 진행됨.
- **예방:** MCP 자동화 세션은 에디터를 **`-unattended`**로 실행 → `FMessageDialog`/`EditorDialog`가 즉시 DefaultValue 반환(모달 안 뜸). 단 기본값 자동응답이라 "저장?" 류 프롬프트 주의.
- **탐지:** 모달에 의존하지 말고 **각 mutate 뒤 Output Log(`LogsToolset`)를 read**해 Error/Warning을 잡는다(모달 유발 에러는 보통 로그에도 남음).

## 5. 서브시스템별 함정
- **Niagara:** "빈 것에서 생성"은 컴파일되지만 **입자 방출 안 함** → 동작 템플릿을 **복제**해서 수정. `script_usage`/dynamic input 제약 주의.
- **Material:** 이미시브로 **bloom 내려면 값 > 1** (임계). 반투명은 translucent shading 설정 필요.
- **UMG:** `CreateWidget`는 **올바른 owner(PlayerController 등) 컨텍스트** 필요. 월드에 붙이는 위젯은 Widget Component 사용.
- **AudioComponent:** 리플렉션상 정확한 컴포넌트/프로퍼티 이름 사용(추측 금지).
- **Lumen:** 라이트/메시 **mobility(Static vs Movable)** 안 맞으면 GI/반사 결과가 다르게 나옴.
- **블루프린트 인스턴스 오버라이드**는 stale될 수 있음 → 변경 후 read-back으로 실제 값 확인.

## 6. Python ↔ MCP 데이터 채널
- 에디터 Python `print()`는 **MCP로 안 돌아오고 UE 로그로 감**.
- 결과를 에이전트가 받아야 하면: **Actor Tag에 값을 써서 다시 읽기**, 또는 툴의 **구조화된 return 값** 사용.

## 7. 안전·검증 패턴 (반드시)
- **verify-after-mutate:** 변경 직후 read-back으로 확인. "성공했다고 가정" 금지.
- **FScopedTransaction**으로 묶어 Undo 가능하게 (커스텀 C++ 툴 작성 시).
- **재귀/반복 캡** 둬서 무한 루프·폭주 방지.
- **파괴적 작업은 사용자 확인** 후. feature 브랜치 + 마일스톤마다 commit.
- **중첩 Tool 호출 금지** (1번 참조) — 한 번에 하나.

## 8. 시각 검증 루프
- 결과는 **뷰포트 캡쳐 → 읽기 → 수정**으로 자기 검증. 캡쳐 툴 없으면 콘솔 `HighResShot 1920x1080`.
- 배치/충돌 애매하면 **line trace로 실제 지오메트리 측정** 후 보정(추측 배치 금지).

## 9. 커스텀 툴셋 추가 (확장)
- Python: 플러그인 `Content/Python/`에 모듈, `unreal.ToolsetDefinition` 상속, 각 함수에 `@toolset_registry.tool_call` + `@staticmethod`. 타입힌트/Google 스타일 docstring이 스키마가 됨.
- C++: `UToolsetDefinition` 상속, `UCLASS(BlueprintType, Hidden)`, static `UFUNCTION(meta=(AICallable))`.
- 추가 후 `ModelContextProtocol.RefreshTools`. **새 `UFUNCTION` 추가는 에디터 재시작** 필요(Live Coding은 기존 함수 본문만 반영).
- Claude Code의 `unreal-mcp` 플러그인엔 `create-toolset` 스킬이 있어 보일러플레이트 생략 가능.

## 10. 디버깅
- 시작 시 **Output Log**에 바인드 주소/포트 로그. 바인드 실패(포트 사용중/의존 플러그인 누락)도 여기.
- `Log LogModelContextProtocol Verbose`로 상세 로그.
- **MCP Inspector**: `npx @modelcontextprotocol/inspector` → `http://127.0.0.1:8000/mcp`를 **Streamable HTTP**로 연결. AI 해석을 배제하고 툴 스키마/호출을 직접 확인.

---

## 부록: UE 5.7 ↔ 5.8 차이 (마이그레이션 시)
- 공식 내장 MCP는 **5.8부터**(experimental). 5.7은 커뮤니티 서버(UnrealClaude+VibeUE, StraySpark, chongdashu 등).
- 5.8은 기본 **tool-search 모드** + Toolset Registry 구조 → 5.7 커뮤니티 서버의 고정 툴 카탈로그와 발견 방식이 다름.
- 마이너 버전 간 툴 표면이 미묘하게 바뀌므로 `.engineVersion` 고정 권장. 한 버전 API로 학습한 호출이 다른 버전에서 없을 수 있음.

## 출처
- Epic 공식: https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor
- 엔진 gotcha 원본(MIT, server-agnostic): https://github.com/ibrews/ue5-mcp
- 실사용 후기·CLAUDE.md 패턴: https://www.top3d.ai/learn/claude-code-unreal-engine
- 셋업/안전 규칙: https://www.strayspark.studio/blog/unreal-mcp-setup-claude-code-2026
