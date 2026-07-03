#!/usr/bin/env python3
"""오프라인 기능 테스트 — 라이브 에디터 없이 setup_project.py 동작을 검증.
CI(validate.yml)와 로컬 양쪽에서 실행 가능:  python3 tests/test_setup.py
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "plugins/unreal-mcp-kit/skills/setup-ue58-mcp/scripts/setup_project.py"
SAMPLE = Path(__file__).resolve().parent / "sample.uproject"


def run(*args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          cwd=str(cwd), capture_output=True, text=True)


def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    tmp = Path(tempfile.mkdtemp())
    try:
        shutil.copy(SAMPLE, tmp / "Sample.uproject")

        # 1) 셋업
        r = run(".", "--niagara", cwd=tmp)
        assert r.returncode == 0, f"setup failed: {r.stderr}\n{r.stdout}"
        up = load(tmp / "Sample.uproject")
        names = [p["Name"] for p in up["Plugins"]]
        assert "EnhancedInput" in names, "기존 플러그인 보존 실패"
        for n in ("ModelContextProtocol", "EditorToolset", "NiagaraToolsets"):
            assert n in names, f"{n} 미추가"
            assert all(p["Enabled"] for p in up["Plugins"] if p["Name"] == n), f"{n} 비활성"
        assert (tmp / "Sample.uproject.bak").exists(), "백업 미생성"
        mcp = load(tmp / ".mcp.json")
        assert mcp["mcpServers"]["unreal-mcp"]["url"] == "http://127.0.0.1:8000/mcp", "mcp url 불일치"
        assert (tmp / "CLAUDE.md").exists(), "CLAUDE.md 미생성"

        # 2) 멱등성 (2회차에 중복 추가 없음)
        r2 = run(".", cwd=tmp)
        assert r2.returncode == 0
        up2 = load(tmp / "Sample.uproject")
        assert [p["Name"] for p in up2["Plugins"]].count("ModelContextProtocol") == 1, "중복 추가됨"

        # 3) verify: 서버 down 이면 실패(exit 1), 크래시 없이
        rv = run(".", "--verify", cwd=tmp)
        assert rv.returncode == 1, "서버 down 인데 verify 통과함"

        # 4) deep: 서버 down 이어도 예외 없이 종료(graceful)
        rd = run(".", "--verify", "--deep", cwd=tmp)
        assert rd.returncode == 1 and "Traceback" not in rd.stderr, "deep 비정상 종료"

        # 5) 손상된 .uproject → 친절 오류(비-크래시, exit!=0)
        bad = tmp / "bad"
        bad.mkdir()
        (bad / "X.uproject").write_text("{ not json", encoding="utf-8")
        rb = run(".", cwd=bad)
        assert rb.returncode != 0 and "Traceback" not in rb.stderr, "손상 파일 처리 실패"

        print("ALL TESTS PASSED")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
