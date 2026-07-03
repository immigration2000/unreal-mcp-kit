#!/usr/bin/env python3
"""
UE 5.8 공식 MCP 프로젝트 셋업 + 진단 (단일 스크립트, 파이썬 표준 라이브러리만 사용).

동작(모두 idempotent — 여러 번 실행 안전):
  기본(셋업):
    1. .uproject 를 .uproject.bak 로 백업(--no-backup 로 끔).
    2. .uproject Plugins 에 ModelContextProtocol + EditorToolset(+옵션) 을 Enabled=true 로 추가/보정.
       기존 플러그인은 절대 삭제하지 않음(없는 것만 추가, 꺼진 것만 켬).
    3. 프로젝트 루트에 .mcp.json (unreal-mcp → http://127.0.0.1:<port>/mcp) 병합 작성.
    4. templates/CLAUDE.md 를 프로젝트 루트에 복사(있으면 --force 아닌 한 건너뜀).
  진단(--verify): 파일을 건드리지 않고 아래를 점검하고 OK/실패 로 보고.
    - .uproject 에 ModelContextProtocol / EditorToolset 활성 여부
    - .mcp.json / CLAUDE.md 존재 및 URL
    - MCP 서버가 127.0.0.1:<port> 에서 응답하는지(에디터를 켠 뒤 확인용)

사용:
  python setup_project.py [폴더]                 # 셋업 (기본: 현재 폴더)
  python setup_project.py . --niagara --umg --physics
  python setup_project.py . --force              # CLAUDE.md 덮어쓰기
  python setup_project.py . --port 8000
  python setup_project.py . --verify             # 셋업 결과/연결 진단
"""
import argparse, json, shutil, sys, re, urllib.request, urllib.error
from pathlib import Path

CORE = ["ModelContextProtocol", "EditorToolset"]
OPTIONAL = {"niagara": "NiagaraToolsets", "umg": "UMGToolSet", "physics": "PhysicsToolsets"}
OK, BAD, WARN = "  [OK] ", "  [!!] ", "  [~] "


def find_uproject(root: Path) -> Path:
    ups = sorted(root.glob("*.uproject"))
    if not ups:
        sys.exit(f"[ERROR] .uproject 를 못 찾음: {root}  (프로젝트 루트에서 실행하세요)")
    if len(ups) > 1:
        print(f"[warn] .uproject 여러 개, 첫 번째 사용: {ups[0].name}")
    return ups[0]


def load_plugins(uproject: Path):
    try:
        data = json.loads(uproject.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"[ERROR] .uproject JSON 파싱 실패({e}). 파일 손상 여부를 확인하세요 (.uproject.bak 로 복구 가능).")
    return data, {p.get("Name"): p for p in data.get("Plugins", [])}


# ---------- 셋업 ----------
def ensure_plugins(uproject: Path, wanted, backup: bool):
    if backup:
        bak = uproject.with_suffix(".uproject.bak")
        shutil.copyfile(uproject, bak)
        print(f"      백업: {bak.name}")
    try:
        data = json.loads(uproject.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"[ERROR] .uproject JSON 파싱 실패({e}). 파일 손상 여부를 확인하세요 (.uproject.bak 로 복구 가능).")
    plugins = data.setdefault("Plugins", [])
    by_name = {p.get("Name"): p for p in plugins}
    for name in wanted:
        p = by_name.get(name)
        if p is None:
            plugins.append({"Name": name, "Enabled": True}); print(f"      + {name} (추가)")
        elif p.get("Enabled") is not True:
            p["Enabled"] = True; print(f"      ~ {name} (Enabled=true 보정)")
        else:
            print(f"      = {name} (이미 활성)")
    uproject.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_mcp_json(root: Path, port: int):
    target = root / ".mcp.json"
    data = {}
    if target.exists():
        try: data = json.loads(target.read_text(encoding="utf-8"))
        except Exception: data = {}
    data.setdefault("mcpServers", {})["unreal-mcp"] = {"type": "http", "url": f"http://127.0.0.1:{port}/mcp"}
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[2/3] .mcp.json → http://127.0.0.1:{port}/mcp")


def copy_claude_md(root: Path, force: bool):
    tpl = Path(__file__).resolve().parent.parent / "templates" / "CLAUDE.md"
    dst = root / "CLAUDE.md"
    if not tpl.exists():
        print(f"[3/3] [warn] 템플릿 없음, 건너뜀: {tpl}"); return
    if dst.exists() and not force:
        print("[3/3] = CLAUDE.md 이미 존재 → 건너뜀 (--force 로 덮어쓰기)"); return
    shutil.copyfile(tpl, dst); print("[3/3] + CLAUDE.md 작성")


def do_setup(root, wanted, port, force, backup):
    up = find_uproject(root)
    print(f"[1/3] .uproject: {up.name}")
    ensure_plugins(up, wanted, backup)
    write_mcp_json(root, port)
    copy_claude_md(root, force)
    print("\n=== 남은 단계 ===")
    print(" 1. 에디터를 (재)시작해 플러그인 로드.")
    print("    서버 자동시작: 에디터 실행인자에 -ModelContextProtocolStartServer 추가,")
    print("    또는 Editor Preferences > Model Context Protocol > Auto Start Server 체크.")
    print(f" 2. 확인:  python setup_project.py . --verify")


# ---------- 진단 ----------
def probe_server(port: int) -> str:
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        urllib.request.urlopen(url, timeout=1.5)
        return "up"
    except urllib.error.HTTPError:
        return "up"          # 4xx/5xx 라도 서버는 떠 있음
    except Exception:
        return "down"


# --- (실험) 실제 MCP 핸드셰이크로 툴셋 로드까지 확인. 불확실하면 절대 실패로 안 봄 ---
KNOWN_WORK_TOOLSETS = ["SceneTools", "ActorTools", "ObjectTools", "MaterialTools",
                       "MaterialInstanceTools", "BlueprintTools", "StaticMeshTools",
                       "AssetTools", "PrimitiveTools", "TextureTools", "LogsToolset"]


def _post(url, payload, headers, timeout=4):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers=headers, method="POST")
    return urllib.request.urlopen(req, timeout=timeout)


def _extract_json(body: str):
    objs = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("data:"):
            s = s[5:].strip()
        if s.startswith("{"):
            try: objs.append(json.loads(s))
            except Exception: pass
    if not objs:
        try: objs.append(json.loads(body))
        except Exception: pass
    return objs[-1] if objs else None


def deep_probe(port: int):
    """returns (True|False|None, message). None = 판정 불가(실패로 취급 안 함)."""
    base = f"http://127.0.0.1:{port}/mcp"
    H = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    try:
        init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                           "clientInfo": {"name": "ue-mcp-kit-verify", "version": "1"}}}
        r = _post(base, init, H)
        sid = r.headers.get("Mcp-Session-Id")
        r.read()
        h2 = dict(H)
        if sid:
            h2["Mcp-Session-Id"] = sid
        try:
            _post(base, {"jsonrpc": "2.0", "method": "notifications/initialized"}, h2).read()
        except Exception:
            pass
        call = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "list_toolsets", "arguments": {}}}
        body = _post(base, call, h2).read().decode("utf-8", "replace")
        obj = _extract_json(body)
        text = json.dumps(obj, ensure_ascii=False) if obj else body
        present = [k for k in KNOWN_WORK_TOOLSETS if k in text]
        if present:
            return (True, f"작업 툴셋 로드 확인: {', '.join(present)}")
        if "AgentSkillToolset" in text:
            return (False, "AgentSkillToolset만 감지 → EditorToolset 미로드(.uproject 추가 + 에디터 재시작)")
        return (None, "툴셋 목록 판정 불가 → 에디터에서 직접 list_toolsets 확인")
    except Exception as e:
        return (None, f"딥 프로브 불가({type(e).__name__}) → 에디터에서 직접 확인")


def do_verify(root, port, deep=False):
    print("=== UE 5.8 MCP 진단 ===")
    ok = True
    up = find_uproject(root)
    _, by = load_plugins(up)
    for name in CORE:
        p = by.get(name)
        if p and p.get("Enabled") is True:
            print(OK + f"{name} 활성")
        else:
            ok = False
            print(BAD + f"{name} 비활성/없음 → .uproject 에 추가 후 에디터 재시작 "
                        f"(EditorToolset 없으면 AgentSkillToolset 하나만 뜸)")
    mcp = root / ".mcp.json"
    if mcp.exists() and f":{port}/mcp" in mcp.read_text(encoding="utf-8"):
        print(OK + ".mcp.json 존재/URL 일치")
    else:
        ok = False; print(BAD + f".mcp.json 없음/포트 불일치 → python setup_project.py . --port {port}")
    has_md = (root / "CLAUDE.md").exists()
    print((OK if has_md else WARN) + ("CLAUDE.md 존재" if has_md else "CLAUDE.md 없음(선택) → 재실행 시 생성"))
    if probe_server(port) == "up":
        print(OK + f"MCP 서버 응답 (127.0.0.1:{port})")
        if deep:
            dok, dmsg = deep_probe(port)
            print((OK if dok is True else BAD if dok is False else WARN) + dmsg)
            if dok is False:
                ok = False
    else:
        ok = False
        print(BAD + f"서버 무응답 → 에디터가 켜져 있는지, Auto Start Server(또는 콘솔 "
                    f"ModelContextProtocol.StartServer) 확인")
        print("       (참고: 이 진단은 에디터와 '같은 PC'에서 실행해야 유효. 에이전트가 "
              "샌드박스/원격이면 서버 항목은 무시하고 에디터 쪽에서 직접 확인)")
    print("\n결과:", "모두 통과. Claude Code 에서 list_toolsets 로 툴셋 확인." if ok
          else "실패 항목 있음. 위 안내대로 조치 후 다시 --verify.")
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--niagara", action="store_true")
    ap.add_argument("--umg", action="store_true")
    ap.add_argument("--physics", action="store_true")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--force", action="store_true", help="CLAUDE.md 덮어쓰기")
    ap.add_argument("--no-backup", action="store_true", help=".uproject 백업 생략")
    ap.add_argument("--verify", action="store_true", help="파일 수정 없이 셋업/연결 진단")
    ap.add_argument("--deep", action="store_true",
                    help="(실험) verify 시 실제 list_toolsets 호출로 툴셋 로드까지 확인")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    if a.verify:
        do_verify(root, a.port, a.deep)
    wanted = list(CORE) + [OPTIONAL[k] for k in OPTIONAL if getattr(a, k)]
    do_setup(root, wanted, a.port, a.force, not a.no_backup)


if __name__ == "__main__":
    main()
