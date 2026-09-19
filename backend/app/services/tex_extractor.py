"""Extract plain text from LaTeX source using detex with pandoc fallback."""

import subprocess
import tempfile
from pathlib import Path


async def extract_plain_text(raw_tex: str) -> str:
    """Try detex first, fall back to pandoc if it fails."""
    text = _try_detex(raw_tex)
    if text and len(text.strip()) > 50:
        return _clean(text)

    text = _try_pandoc(raw_tex)
    if text and len(text.strip()) > 50:
        return _clean(text)

    # Last resort: naive strip of common LaTeX commands
    return _clean(_naive_strip(raw_tex))


def _try_detex(raw_tex: str) -> str | None:
    try:
        result = subprocess.run(
            ["detex", "-l"],
            input=raw_tex,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _try_pandoc(raw_tex: str) -> str | None:
    try:
        with tempfile.NamedTemporaryFile(suffix=".tex", mode="w", delete=False) as f:
            f.write(raw_tex)
            f.flush()
            result = subprocess.run(
                ["pandoc", f.name, "-f", "latex", "-t", "plain", "--wrap=none"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            Path(f.name).unlink(missing_ok=True)
            if result.returncode == 0:
                return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _naive_strip(raw_tex: str) -> str:
    """Rough removal of LaTeX commands for when tools aren't available."""
    import re
    text = raw_tex
    # Remove comments
    text = re.sub(r"%.*$", "", text, flags=re.MULTILINE)
    # Remove common environments
    text = re.sub(r"\\begin\{.*?\}", "", text)
    text = re.sub(r"\\end\{.*?\}", "", text)
    # Remove commands but keep arguments
    text = re.sub(r"\\[a-zA-Z]+\*?\s*", " ", text)
    # Remove braces
    text = re.sub(r"[{}]", "", text)
    # Clean whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _clean(text: str) -> str:
    """Clean up extracted text."""
    import re
    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
