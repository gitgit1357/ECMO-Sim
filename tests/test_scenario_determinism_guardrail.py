from pathlib import Path


def test_no_uncontrolled_random_imports_in_src():
    src = Path(__file__).resolve().parents[1] / "src"
    offenders = []
    for path in src.rglob("*.py"):
        if path.as_posix().endswith("neoscenarios/rng.py"):
            continue
        text = path.read_text(encoding="utf-8")
        if "import random" in text or "from random" in text or "numpy.random" in text or "np.random" in text:
            offenders.append(str(path.relative_to(src)))
    assert offenders == []
