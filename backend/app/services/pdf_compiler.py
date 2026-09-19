"""Tectonic-based LaTeX to PDF compilation with --untrusted sandboxing."""

import subprocess
import tempfile
from pathlib import Path


class CompilationError(Exception):
    pass


async def compile_latex(tex_source: str) -> bytes:
    """Compile LaTeX source to PDF using Tectonic.

    Uses --untrusted flag to disable shell-escape (LaTeX RCE protection).
    Returns raw PDF bytes.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "resume.tex"
        pdf_path = Path(tmpdir) / "resume.pdf"

        tex_path.write_text(tex_source, encoding="utf-8")

        try:
            result = subprocess.run(
                [
                    "tectonic",
                    "--untrusted",
                    "-o", str(tmpdir),
                    str(tex_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=tmpdir,
            )
        except FileNotFoundError:
            raise CompilationError("Tectonic is not installed or not in PATH")
        except subprocess.TimeoutExpired:
            raise CompilationError("LaTeX compilation timed out (60s limit)")

        if result.returncode != 0:
            raise CompilationError(f"Tectonic compilation failed:\n{result.stderr}")

        if not pdf_path.exists():
            raise CompilationError("PDF output not found after compilation")

        return pdf_path.read_bytes()
