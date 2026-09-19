"""Jinja2 LaTeX rendering with custom delimiters to avoid {} collisions."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# Custom delimiters: << >> for variables, <% %> for blocks
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    block_start_string="<%",
    block_end_string="%>",
    variable_start_string="<<",
    variable_end_string=">>",
    comment_start_string="<#",
    comment_end_string="#>",
    autoescape=False,
)

_LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def latex_escape(value) -> str:
    """Escape LaTeX special characters in plain text (parsed titles, bullets, skills)."""
    if value is None:
        return ""
    return "".join(_LATEX_SPECIALS.get(c, c) for c in str(value))


_env.filters["latex"] = latex_escape


def render_resume(
    sections: list[dict],
    header_info: dict | None = None,
    preamble: str | None = None,
    original_header: str | None = None,
) -> str:
    """Render a LaTeX resume from selected entities.

    Args:
        sections: ordered list, each one of
            {kind: "mutable", name, entities: [{title, subtitle, date_range, location, bullets: [str]}]}
            {kind: "raw", name, raw_latex} for sections that don't change
            {kind: "skills", items: [{category, items: [str]}]}
        header_info: optional {name, email, phone, linkedin, github, website}
        preamble: the original resume's preamble (incl. \\documentclass); default used if None
        original_header: the original resume's header block, used when header_info is empty
    """
    template = _env.get_template("resume_template.tex")

    return template.render(
        sections=sections,
        header=header_info or {},
        preamble=preamble,
        original_header=original_header,
    )
