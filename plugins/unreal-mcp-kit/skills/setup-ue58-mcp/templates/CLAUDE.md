# CLAUDE.md — UE 5.8 공식 MCP 프로젝트 플레이북

> **사용법:** 이 파일을 **언리얼 프로젝트 루트**(`.uproject` 옆)에 `CLAUDE.md`로 복사. Claude Code가 세션마다 자동으로 읽음.
> 환경: RTX 4070 Ti / Ryzen 9 7900X3D / RAM 128GB / Windows 11, UE 5.8 + 공식 `ModelContextProtocol` 플러그인.

---

## ⚑ 신규 프로젝트 셋업 체크리스트 (1순위)
1. **`.uproject` Plugins에 `EditorToolset` 활성화** ← **가장 중요.** 안 켜면 작업 툴셋이 하나도 안 뜬다(아래 §2). 필요 시 `NiagaraToolsets`/`UMGToolSet`/`PhysicsToolsets`도 추가.
   ```json
   { "Name": "EditorToolset", "Enabled": true }
   ```
2. `ModelContextProtocol` 플러그인 활성화 + Editor Preferences에서 `Auto Start Server` ON.
3. 콘솔 `ModelContextProtocol.GenerateClientConfig ClaudeCode` → 프로젝트 루트에 `.mcp.json` 생성.
4. **에디터 재시작** 후 `ModelContextProtocol.StartServer` → 프로젝트 루트에서 에이전트 실행.

## 0. 이 프로젝트에서 너(Claude)의 동작 원칙
- **항상 feature 브랜치에서 작업**하고, 동작하는 단계마다 git commit 한다. main 직접 작업 금지.
- **파괴적 작업(삭제/덮어쓰기/리셋) 전에는 반드시 사용자에게 확인**받는다. 자동 승인하지 않는다.
- 에셋을 **수정한 직후 반드시 읽어서(read-back) 결과를 검증**한다. "했다고 가정"하지 않는다.
- **MCP Tool 호출은 한 번에 하나씩**. 동시/중첩 호출 금지 (서버가 게임 스레드에서 직렬 처리하므로 겹치면 꼬임).
- 모르는 엔진 API는 추측하지 말고 `tools/list` → `describe_toolset`로 **실제 시그니처를 확인 후** 호출.
- 문제를 한참 디버깅해서 해결하면, 그 해결책을 **이 CLAUDE.md의 "9. 누적 gotcha"에 한 줄로 추가**한다. (self-growing)

---

## 1. MCP 연결 상태 빠른 확인
- 에디터가 켜져 있고 MCP 서버가 `http://127.0.0.1:8000/mcp`에서 떠 있어야 함.
- 안 보이면 사용자에게:
  1. 에디터 콘솔(백틱 `` ` ``)에서 `ModelContextProtocol.StartServer`
  2. `.mcp.json`이 있는 **프로젝트 루트에서 `claude` 실행**했는지 확인 (다른 폴더면 연결 안 됨)
  3. 그래도 안 되면 `ModelContextProtocol.RefreshTools` 후 Claude Code 재연결
- **`list_toolsets`에 `AgentSkillToolset` 하나만 보이면** → `RefreshTools`는 소용없다(등록할 코드 자체가 로드 안 됨). **`.uproject` Plugins에 `EditorToolset`이 있는지 먼저 확인**하고, 없으면 추가 후 **에디터 재시작** → `StartServer`. (가장 흔한 함정. §2 참조)

## 2. 도구 발견 규칙 (Tool Search 모드)
- 이 플러그인은 기본 **tool-search 모드**라 `tools/list`가 전체 스키마가 아니라 메타툴 3개만 준다:
  - `list_toolsets` — 사용 가능한 툴셋 목록/설명
  - `describe_toolset` — 특정 툴셋의 툴 스키마
  - `call_tool` — 이름으로 툴 실행
- **작업 시작 시 `list_toolsets`로 한 번 훑고**, 쓸 툴셋만 `describe_toolset`으로 펼쳐라. 전부 펼치지 마라(토큰 낭비).
- **작업 툴셋은 기본 탑재가 아니다.** UE 5.8은 작업 툴셋을 `Engine/Plugins/Experimental/Toolsets/` 아래 **개별 플러그인**으로 제공한다(`EditorToolset`, `NiagaraToolsets`, `UMGToolSet`, `PhysicsToolsets`, `GASToolsets` … 전체 메타 = `AllToolsets`).
  - `.uproject`에 `ModelContextProtocol`만 켜면 의존성으로 딸려온 **`AgentSkillToolset` 하나만** 보인다.
  - `.uproject`에 **`EditorToolset`을 추가 + 에디터 재시작**하면 `SceneTools`/`ActorTools`/`ObjectTools`/`MaterialTools`/`MaterialInstanceTools`/`BlueprintTools`/`StaticMeshTools`/`SkeletalMeshTools`/`AssetTools`/`PrimitiveTools`/`TextureTools`/`LogsToolset` 등 **~19개**가 등록된다.

## 3. 표준 작업 루프 (반드시 이 순서)
1. **계획**: 무엇을 만들지 + 어떤 툴셋/툴 쓸지 한 줄 요약.
2. **실행**: 툴 하나씩 호출.
3. **검증**: 변경한 에셋/액터를 read-back + **Output Log에서 Error/Warning 확인**. 가능하면 뷰포트 캡쳐 또는 자동화 테스트로 눈으로 확인.
4. **보고**: 빌드/컴파일 로그 결과를 사용자에게 보고.
5. **커밋**: 동작하면 `git commit -m "..."`.

## 4. 블루프린트 작업 규칙
- 블루프린트 클래스 **경로 참조는 `_C` 접미사** 필요(예: `/Game/BP/BP_Foo.BP_Foo_C`). 빼면 조용히 실패.
- 노드 그래프 변경은 **3단계(노드 추가 → 핀 연결 → 컴파일)**를 반드시 다 거친다. 컴파일 안 하면 반영 안 됨.
- **변수는 만들기만 하지 말고 기본값(내용물)까지 채운다.** 변수 생성 툴에 default 인자가 있으면 그걸로 넣고, 없으면 **Python으로 CDO에 직접** 넣는다(에디터에 손으로 넣게 두지 말 것 — 그게 병목):
  - 순서: **변수 추가 → 컴파일 → CDO에 `set_editor_property` → 저장 → read-back 검증**. (컴파일 전엔 CDO에 그 프로퍼티가 없음)
  - 클래스는 `_C`로 로드. 직접 대입 말고 `set_editor_property` 사용(변경 이벤트+dirty 반영).
  ```python
  import unreal
  bp = unreal.load_asset('/Game/BP/BP_Foo')
  unreal.BlueprintEditorLibrary.compile_blueprint(bp)
  cdo = unreal.get_default_object(unreal.load_object(None, '/Game/BP/BP_Foo.BP_Foo_C'))
  cdo.set_editor_property("Health", 100.0)          # 배열/구조체면 list/dict/struct 그대로
  unreal.EditorAssetSubsystem().save_asset('/Game/BP/BP_Foo')
  ```
- 프로퍼티 변경 후 `PostEditChangeProperty`가 필요한 케이스가 있다 — 에디터에 반영 안 되면 의심.
- **노드 레이아웃 정리는 기대하지 마라.** 로직 우선, 보기 좋은 정렬은 사용자가 수동으로. (실사용 후기: 정리 요청은 대부분 실패)
- **Play(PIE) 중에는 블루프린트 편집 잠김**. 편집은 Stop 후에.

## 5. 시각 검증 (Self-review)
- 변경 결과는 말로 "됐다"가 아니라 **뷰포트를 캡쳐해서 직접 보고 판단**한다.
- 캡쳐 툴이 없으면 콘솔 `HighResShot 1920x1080`로 스크린샷 후 경로를 읽어 확인.
- 위치/충돌이 애매하면 **line trace로 실제 지오메트리를 측정**해서 배치(추측 금지).

## 6. Python 사용 시 데이터 채널 주의
- 에디터 Python의 `print()` 출력은 **MCP로 안 돌아오고 UE 로그로 감**.
- 결과를 Claude가 받아야 하면 **Actor Tag에 써서 다시 읽는** 우회 패턴을 쓰거나, 툴의 구조화된 return 값을 사용.

## 7. 안정성 (크래시 회피)
- **참조 중인 메시/에셋 삭제 금지** → 먼저 의존성 그래프 확인 후 참조 없을 때만 삭제.
- **액터 대량 작업은 빠르게 연타하지 말 것** (rapid actor ops 크래시 패턴). 배치는 나눠서.
- **Niagara / MetaSound는 편집 후 PIE 전에 저장(Save)**. 안 하면 크래시/무동작.
- Niagara를 **"빈 것에서 생성"하면 컴파일은 되지만 입자가 안 나옴** → 동작하는 템플릿을 **복제(duplicate)** 해서 수정.
- MetaSound: 스칼라(Multiply 등)를 **오디오 핀에 바로 연결하면 크래시**. 핀 타입 정확히 맞춰라.

### 모달/에러 창 병목 회피
- **이미 떠 있는 모달은 Claude가 못 닫는다.** 모달(`FMessageDialog`)은 게임 스레드를 막고 MCP 툴도 게임 스레드에서 도니, 모달이 뜬 동안 MCP가 멈춰서 사람이 눌러야 한다. → **예방 + 로그 탐지**로 간다.
- **예방:** MCP 자동화 세션은 에디터를 **`-unattended`로 실행** → `FMessageDialog`/`EditorDialog`가 사람을 안 기다리고 기본값을 반환(모달 안 뜸). ⚠️ 자동으로 기본값을 답하므로 "저장할까요?" 같은 **파괴적 프롬프트에 주의**(기본값이 원치 않는 쪽일 수 있음). 일반 편집 세션엔 굳이 안 씀.
- **탐지:** **각 mutate 뒤 Output Log를 read**해 Error/Warning을 확인하고 있으면 보고·수정한다(모달을 띄우는 에러는 대개 로그에도 남는다). `LogsToolset` 또는 콘솔 로그 사용.

## 8. 컨텍스트 / 토큰 관리
- 언리얼 세션은 컨텍스트(~200k)를 빨리 먹는다.
- **같은 작업 계속**이면 `/compact`, **다른 작업으로 전환**이면 새 채팅이 더 깨끗하다.
- 큰 에셋 덤프를 통째로 읽지 말고, 필요한 필드만 조회.

## 9. 누적 gotcha (여기에 계속 추가)
> 형식: `- [날짜] 증상 → 원인 → 해결`
- (예시) [2026-06-27] 버튼 OnClicked가 조용히 no-op → 바인딩 누락 → 위젯 그래프에서 이벤트 재바인딩 후 컴파일.
- [2026-06-29] `list_toolsets`에 `AgentSkillToolset`만 → `EditorToolset` 플러그인 꺼짐 → `.uproject`에 추가 + 재시작 → 19개 정상.
-

---

### 참고 출처
- Epic 공식 문서: https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor
- 엔진 gotcha 스킬(server-agnostic): https://github.com/ibrews/ue5-mcp
- 실사용 후기/CLAUDE.md 패턴: https://www.top3d.ai/learn/claude-code-unreal-engine
- 셋업 베스트프랙티스: https://www.strayspark.studio/blog/unreal-mcp-setup-claude-code-2026
