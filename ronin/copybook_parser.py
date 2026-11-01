"""Conservative copybook metadata parser; unsupported layouts remain explicit."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class PicInfo:
    raw: str
    category: str
    length: int
    precision: int
    scale: int
    signed: bool
    usage: str | None = None
    supported: bool = True


def parse_pic_string(pic_str: str) -> PicInfo:
    raw = pic_str.strip().upper().rstrip(".")
    usage_match = re.search(r"\b(COMP-3|PACKED-DECIMAL|COMP-5|COMP|BINARY)\b", raw)
    usage = usage_match.group(1) if usage_match else None
    pic_match = re.search(r"\bPIC(?:TURE)?\s+(.+?)(?=\s+(?:USAGE|COMP-3|PACKED-DECIMAL|COMP-5|COMP|BINARY|VALUE|OCCURS|REDEFINES)\b|$)", raw)
    if pic_match:
        body = pic_match.group(1).strip()
    else:
        body = re.sub(r"\s+(?:USAGE\s+IS\s+)?(?:COMP-3|PACKED-DECIMAL|COMP-5|COMP|BINARY)\b.*$", "", raw).strip()
    body = re.sub(r"\s+", "", body)
    signed = body.startswith("S")
    body = body[1:] if signed else body
    if not body or not re.fullmatch(r"[X9AVZ0-9*(),.+\-]+", body):
        raise ValueError(f"unsupported PIC syntax: {pic_str!r}")
    tokens = re.findall(r"([A-Z0-9*])(?:\((\d+)\))?", body)
    if not tokens:
        raise ValueError(f"invalid PIC syntax: {pic_str!r}")
    chars = [(char, int(count) if count else 1) for char, count in tokens]
    length = sum(count for char, count in chars if char in ("X", "A", "9", "Z", "*"))
    scale = 0
    after_v = False
    for char, count in chars:
        if char == "V":
            after_v = True
        elif char == "9" and after_v:
            scale += count
    numeric = any(char == "9" for char, _ in chars)
    alpha = any(char in ("X", "A") for char, _ in chars)
    if numeric and alpha:
        category = "alphanumeric-edited"
    elif alpha:
        category = "alphanumeric" if any(char == "X" for char, _ in chars) else "alphabetic"
    elif numeric:
        category = "numeric"
    else:
        category = "edited"
    precision = sum(count for char, count in chars if char == "9")
    supported = "P" not in body
    return PicInfo(raw=raw, category=category, length=length, precision=precision,
                   scale=scale, signed=signed, usage=usage, supported=supported)


def denormalize_occurs(copybook_lines: list[str]) -> list[dict[str, Any]]:
    """Expand simple fixed OCCURS declarations; do not guess nested layouts."""
    output: list[dict[str, Any]] = []
    declaration = re.compile(
        r"^\s*(\d{1,2})\s+([A-Z0-9_-]+)"
        r"(?:\s+REDEFINES\s+([A-Z0-9_-]+))?"
        r"(?:\s+PIC(?:TURE)?\s+(.+?))?"
        r"(?:\s+OCCURS\s+(\d+)\s+TIMES?)?\s*\.?$",
        re.IGNORECASE,
    )
    for line in copybook_lines:
        clean = line.split("*>", 1)[0].strip()
        if not clean:
            continue
        match = declaration.match(clean)
        if not match:
            continue
        level, name, redefines, pic, occurs = match.groups()
        count = int(occurs or 1)
        supported = not (count > 1 and redefines)
        try:
            info = asdict(parse_pic_string(pic)) if pic else None
        except ValueError:
            info, supported = None, False
        for index in range(1, count + 1):
            output.append({
                "level": int(level),
                "name": name.upper() if count == 1 else f"{name.upper()}-{index}",
                "source_name": name.upper(),
                "occurs_index": index if count > 1 else None,
                "pic": info,
                "redefines": redefines.upper() if redefines else None,
                "supported": supported,
            })
    return output


def handle_redefines(copybook_lines: list[str]) -> list[dict[str, Any]]:
    """Annotate overlays without claiming compiler-specific byte offsets."""
    entries = denormalize_occurs(copybook_lines)
    by_name = {entry["source_name"]: entry for entry in entries
               if entry["occurs_index"] in (None, 1)}
    for entry in entries:
        target = entry["redefines"]
        if target:
            if target not in by_name:
                entry["supported"] = False
                entry["overlay_target_found"] = False
            else:
                entry["overlay_target_found"] = True
                entry["overlay_target"] = target
                entry["offsets_resolved"] = False
    return entries
