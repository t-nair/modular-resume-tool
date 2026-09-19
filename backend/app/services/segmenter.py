"""Regex-based structural segmentation of LaTeX resume source."""

import re
from dataclasses import dataclass, field


@dataclass
class SegmentedSection:
    name: str
    raw_latex: str
    entries: list["SegmentedEntry"] = field(default_factory=list)


@dataclass
class SegmentedEntry:
    header_latex: str
    bullets: list[str] = field(default_factory=list)
    raw_latex: str = ""


# Patterns for common LaTeX resume section commands
SECTION_PATTERNS = [
    re.compile(r"\\section\*?\{(.+?)\}", re.DOTALL),
    re.compile(r"\\cvsection\*?\{(.+?)\}", re.DOTALL),
    re.compile(r"\\resumesection\*?\{(.+?)\}", re.DOTALL),
]

# Patterns for entry/entity headers
ENTRY_PATTERNS = [
    re.compile(r"\\(resumeSubHeading|cventry|resumeItem)\s*\{", re.DOTALL),
    re.compile(r"\\textbf\{(.+?)\}", re.DOTALL),
]

# Bullet items
ITEM_PATTERN = re.compile(r"\\(?:resumeItem|item)\s*\{?(.*?)\}?\s*$", re.MULTILINE)


def segment_latex(raw_tex: str) -> list[SegmentedSection]:
    """Split raw LaTeX into sections, then entries and bullets within each."""
    sections = _split_into_sections(raw_tex)
    for section in sections:
        section.entries = _split_into_entries(section.raw_latex)
    return sections


def _split_into_sections(raw_tex: str) -> list[SegmentedSection]:
    """Find section boundaries and split."""
    # Find all section commands and their positions
    matches = []
    for pattern in SECTION_PATTERNS:
        for m in pattern.finditer(raw_tex):
            matches.append((m.start(), m.end(), m.group(1).strip()))

    if not matches:
        # Fallback: treat entire document as one section
        return [SegmentedSection(name="General", raw_latex=raw_tex)]

    matches.sort(key=lambda x: x[0])
    sections = []

    for i, (start, end, name) in enumerate(matches):
        # Section content goes from after this header to the next section (or EOF)
        next_start = matches[i + 1][0] if i + 1 < len(matches) else len(raw_tex)
        content = raw_tex[end:next_start]
        sections.append(SegmentedSection(name=name, raw_latex=content))

    return sections


def _split_into_entries(section_latex: str) -> list[SegmentedEntry]:
    """Split a section's content into entries (entities with bullets)."""
    entries = []

    # Try to find entry blocks by looking for common resume entry commands
    # Strategy: find entry header commands, then collect bullets until next entry
    entry_starts = []
    for pattern in ENTRY_PATTERNS:
        for m in pattern.finditer(section_latex):
            entry_starts.append(m.start())

    if not entry_starts:
        # No structured entries found - extract any bullets as a single entry
        bullets = _extract_bullets(section_latex)
        if bullets:
            entries.append(SegmentedEntry(
                header_latex="",
                bullets=bullets,
                raw_latex=section_latex,
            ))
        return entries

    entry_starts.sort()
    entry_starts = list(dict.fromkeys(entry_starts))  # deduplicate, preserve order

    for i, start in enumerate(entry_starts):
        end = entry_starts[i + 1] if i + 1 < len(entry_starts) else len(section_latex)
        block = section_latex[start:end]

        # First line(s) are the header, rest are bullets
        lines = block.strip().split("\n")
        header = lines[0] if lines else ""
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""
        bullets = _extract_bullets(body)

        entries.append(SegmentedEntry(
            header_latex=header,
            bullets=bullets,
            raw_latex=block,
        ))

    return entries


def _extract_bullets(text: str) -> list[str]:
    """Extract bullet point text from LaTeX item commands."""
    bullets = []

    # Match \item or \resumeItem style bullets
    for m in ITEM_PATTERN.finditer(text):
        bullet_text = m.group(1).strip()
        if bullet_text:
            # Clean up remaining LaTeX artifacts
            bullet_text = re.sub(r"\\[a-zA-Z]+\{(.*?)\}", r"\1", bullet_text)
            bullet_text = re.sub(r"[{}]", "", bullet_text)
            bullet_text = bullet_text.strip()
            if len(bullet_text) > 5:
                bullets.append(bullet_text)

    # Also try matching lines that start with bullet markers in plain text
    if not bullets:
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith(("- ", "* ", "• ")):
                clean = line.lstrip("-*• ").strip()
                if len(clean) > 5:
                    bullets.append(clean)

    return bullets
