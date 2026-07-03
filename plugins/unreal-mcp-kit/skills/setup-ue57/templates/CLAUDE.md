# CLAUDE.md — UE 5.7 (VibeUE + UnrealClaude) 프로젝트 플레이북

> 프로젝트 루트에 `CLAUDE.md`로 복사. UE 5.7은 공식 MCP가 없어 **커뮤니티 서버**로 동작한다.
> VibeUE 공식 지침은 아래 import로 자동 포함된다(있을 때).

@Plugins/VibeUE/Content/samples/AGENTS.md.sample

---

## 0. 동작 원칙
- **feature 브랜치 + 마일스톤마다 commit.** main 직접 작업 금지.
- **파괴적 작업(삭제/덮어쓰기) 전 사용자 확인.** 자동 승인 금지.
- 에셋/액터 **변경 직후 read-back으로 검증**한다("됐다고 가정" 금지).
- 모르는 API는 추측하지 말고 서버가 노출한 툴 목록을 먼저 확인.

## 1. 연결 상태
- **서버는 에디터가 열려 있을 때만 동작한다.** 안 뜨면 에디터부터 켠다.
- VibeUE: `http://127.0.0.1:8088/mcp` (Project Settings > Plugins > VibeUE > Enable MCP Server, Port 8088).
- UnrealClaude(선택): 포트 3000 자동 기동. 블루프린트 툴이 안 보이면 `Plugins/UnrealClaude/Resources/mcp-bridge`에서 `npm install`.
- 빠른 확인: `curl http://127.0.0.1:8088/mcp` / `curl http://localhost:3000/mcp/status`. Claude Code에선 `/mcp`.

## 2. 역할 분담
- **VibeUE** — 블루프린트/에셋/머티리얼/에디터 조작·Python 실행.
- **UnrealClaude** — 뷰포트 캡쳐(시각 검증) + 액터 스폰/이동.
- 시각 확인이 필요한 작업은 UnrealClaude 캡쳐로 결과를 눈으로 검증.

## 3. 블루프린트 규칙 (엔진 공통)
- 블루프린트 클래스 경로는 **`_C` 접미사** 필요(`/Game/BP/BP_Foo.BP_Foo_C`). 빼면 조용히 실패.
- 그래프 변경은 **노드 추가 → 핀 연결 → 컴파일** 3단계 필수.
- 프로퍼티 변경 후 반영 안 되면 `PostEditChangeProperty` 의심.
- **노드 레이아웃 정리는 기대하지 말 것**(로직 우선). **Play(PIE) 중 편집 잠김**.

## 4. 안정성 (엔진 공통)
- 참조 중인 메시/에셋 삭제 금지(의존성 먼저 확인). 액터 대량작업은 배치로.
- Niagara "빈 것에서 생성"은 입자 안 나옴 → 동작 템플릿 복제. 편집 후 PIE 전 **Save**.
- MetaSound 스칼라를 오디오 핀에 직결 시 크래시.

## 5. 컨텍스트/토큰
- 긴 세션은 `/compact`(같은 작업) 또는 새 채팅(작업 전환). 큰 에셋 덤프 통째로 읽지 말 것.

## 6. 누적 gotcha (여기에 계속 추가)
> 형식: `- [날짜] 증상 → 원인 → 해결`
-
-

---
### 참고
- 엔진 gotcha 상세: 지식 스킬 `ue5-8-mcp`(server-agnostic, 5.7 적용) / https://github.com/ibrews/ue5-mcp
- VibeUE 5.7: https://www.vibeue.com/v5-7/docs  ·  UnrealClaude: https://github.com/Natfii/UnrealClaude
