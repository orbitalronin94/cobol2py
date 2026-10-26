#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cobol2py.py — Traductor COBOL → Python (v0.0.4)
Un archivo. Sin dependencias. Solo stdlib.

Cambios v0.0.4 sobre v0.0.3:
    - Patch 1: normalización de `=` a `==` en condiciones.
    - Patch 2: OCCURS DEPENDING ON + default con tamaño fijo.
    - Patch 3: splitter de buffers concatenados por verbos COBOL.
    - Patch 4: ADD con múltiples operandos (A, B TO C → c += a + b).
"""

from __future__ import annotations

import argparse
import ast
import json
import keyword
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ============================================================================
# 1. PREPROCESADO
# ============================================================================

def strip_inline_comment(line: str) -> str:
    """Remove a COBOL *> comment only when it appears outside a quoted literal.

    COBOL escapes a quote inside a literal by doubling it ("" or ''). Keeping
    this scan small avoids treating comment markers inside DISPLAY/MOVE strings
    as comments without introducing a dependency or pretending to parse COBOL.
    """
    quote: Optional[str] = None
    i = 0
    while i < len(line):
        char = line[i]
        if quote is not None:
            if char == quote:
                if i + 1 < len(line) and line[i + 1] == quote:
                    i += 2
                    continue
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif line.startswith("*>", i):
            return line[:i].rstrip()
        i += 1
    return line.rstrip()


def preprocess(source: str, source_format: str = "auto") -> list[tuple[int, str]]:
    if source_format not in ("auto", "fixed", "free"):
        raise ValueError("source_format debe ser 'auto', 'fixed' o 'free'")
    lines = source.splitlines()
    # COBOL fixed format uses columns 1-6 for sequence numbers, column 7
    # for the indicator, and columns 8-72 for source. Do not infer free
    # format merely because a fixed-format line has leading spaces.
    def looks_fixed(line: str) -> bool:
        if len(line) < 8 or not re.fullmatch(r"[ 0-9]{6}", line[:6]):
            return False
        return line[6] in (" ", "*", "/", "D", "d", "-")

    # Blank sequence areas make fixed/free format inherently ambiguous. Allow
    # callers to override the heuristic explicitly when source layout is known.
    fixed_format = source_format == "fixed" or (
        source_format == "auto" and any(looks_fixed(line) for line in lines[:20])
    )
    out: list[tuple[int, str]] = []
    for i, raw in enumerate(lines, 1):
        if not fixed_format:
            line = strip_inline_comment(raw)
            if line.strip():
                out.append((i, line))
            continue
        line = raw.rstrip("\n").ljust(80)
        indicator = line[6] if len(line) > 6 else " "
        if indicator in ("*", "/", "D", "d"):
            continue
        code = line[7:72].rstrip()
        code = strip_inline_comment(code)
        if code.strip():
            out.append((i, code))
    return out

# ============================================================================
# 2. MODELOS
# ============================================================================

@dataclass
class CobolVar:
    level: int
    name: str
    pic: Optional[str] = None
    value: Optional[str] = None
    is_group: bool = False
    is_array: bool = False
    occurs: Optional[int] = None
    depending_on: Optional[str] = None
    parent_name: Optional[str] = None

    def _base_py_type(self) -> str:
        if self.pic is None:
            return "dict"
        p = self.pic.upper()
        if any(c in p for c in ("X", "A")):
            return "str"
        if "V" in p:
            return "float"
        if "9" in p:
            m = re.search(r"9\((\d+)\)", p)
            n = int(m.group(1)) if m else len(re.findall(r"9", p))
            return "int" if n <= 18 else "str"
        return "str"

    def _base_default(self) -> str:
        return {"int": "0", "float": "0.0", "str": '""', "dict": "{}"}.get(
            self._base_py_type(), "None"
        )

    def py_type(self) -> str:
        if self.is_group:
            return "dict"
        if self.is_array:
            return f"list[{self._base_py_type()}]"
        return self._base_py_type()

    def py_default(self) -> str:
        # Preserve simple VALUE literals. Fixed-width alphanumeric storage
        # starts space-filled and MOVE/VALUE text is padded or truncated.
        initial = translate_literal(self.value) if self.value is not None else self._base_default()
        if self.pic and ("X" in self.pic.upper() or "A" in self.pic.upper()):
            width = pic_character_count(self.pic)
            if width:
                if self.value is None:
                    initial = repr(" " * width)
                else:
                    all_literal = re.fullmatch(r"""ALL\s+(["'])(.*?)\1""", self.value, re.IGNORECASE)
                    if all_literal:
                        repeated = (all_literal.group(2) * width)[:width]
                        initial = repr(repeated)
                    elif self.value.upper() in ("LOW-VALUE", "LOW-VALUES"):
                        initial = repr("\x00" * width)
                    elif self.value.upper() in ("HIGH-VALUE", "HIGH-VALUES"):
                        initial = repr("\xff" * width)
                    elif self.value.upper() in ("SPACE", "SPACES"):
                        initial = repr(" " * width)
                    else:
                        initial = f"str({initial})[:{width}].ljust({width})"
        if self.is_array:
            if self.occurs:
                return f"[{initial}] * {self.occurs}"
            return "[]"
        return initial

    def java_type(self) -> str:
        if self.is_array:
            base = self._base_py_type()
            jb = {"int": "Integer", "float": "Double", "str": "String", "dict": "Object"}.get(base, "Object")
            return f"List<{jb}>"
        return {"int": "int", "float": "double", "str": "String", "dict": "Map<String, Object>"}.get(
            self._base_py_type(), "Object"
        )

    def java_default(self) -> str:
        return "new ArrayList<>()" if self.is_array else {
            "int": "0", "float": "0.0", "str": '""', "dict": "new HashMap<>()"
        }.get(self._base_py_type(), "null")


@dataclass
class Node:
    kind: str
    text: str
    line: int
    then_branch: list["Node"] = field(default_factory=list)
    else_branch: list["Node"] = field(default_factory=list)
    body: list["Node"] = field(default_factory=list)


@dataclass
class Program:
    program_id: str = "PROGRAM"
    variables: list[CobolVar] = field(default_factory=list)
    paragraphs: dict[str, list[Node]] = field(default_factory=dict)
    paragraph_order: list[str] = field(default_factory=list)
    raw_lines: list[tuple[int, str]] = field(default_factory=list)
    unresolved_copybooks: list[str] = field(default_factory=list)


# ============================================================================
# 3. PARSEO
# ============================================================================

RE_IDENT = re.compile(r"IDENTIFICATION\s+DIVISION", re.IGNORECASE)
RE_DATA = re.compile(r"DATA\s+DIVISION", re.IGNORECASE)
RE_PROC = re.compile(r"PROCEDURE\s+DIVISION", re.IGNORECASE)
RE_PROGRAM_ID = re.compile(r"PROGRAM-ID\.\s*([A-Za-z0-9\-]+)", re.IGNORECASE)
RE_WORKING_STORAGE = re.compile(r"WORKING-STORAGE\s+SECTION", re.IGNORECASE)
RE_VAR = re.compile(r"^\s*(\d{1,2})\s+([A-Za-z0-9\-]+)\s*(.*?)(?:\.\s*)?$", re.IGNORECASE)
RE_PIC = re.compile(r"PIC(?:TURE)?\s+(?:IS\s+)?([A-Za-z0-9\(\)VSPX]+)", re.IGNORECASE)
RE_VALUE = re.compile(
    r"""VALUE\s+(?:IS\s+)?((?:ALL\s+)?(?:"(?:[^"]|"")*"|'(?:[^']|'')*'|[+-]?\d+(?:\.\d+)?|[A-Za-z][A-Za-z0-9-]*))""",
    re.IGNORECASE,
)
# Patch 2: OCCURS dinámico
RE_OCCURS = re.compile(
    r"OCCURS\s+(?:\d+\s+TO\s+)?(\d+)\s+TIMES"
    r"(?:\s+DEPENDING\s+ON\s+([A-Za-z0-9\-]+))?",
    re.IGNORECASE,
)
RE_PARAGRAPH = re.compile(r"^(?!END-)([A-Za-z][A-Za-z0-9\-]*)\.\s*$")


def parse_variables(lines: list[tuple[int, str]]) -> list[CobolVar]:
    variables: list[CobolVar] = []
    hierarchy: list[CobolVar] = []
    for _, text in lines:
        m = RE_VAR.match(text)
        if not m:
            continue
        level = int(m.group(1))
        if level == 88 or level >= 50:
            continue
        while hierarchy and hierarchy[-1].level >= level:
            hierarchy.pop()
        name = m.group(2).upper()
        rest = m.group(3)
        pic_m = RE_PIC.search(rest)
        val_m = RE_VALUE.search(rest)
        occ_m = RE_OCCURS.search(rest)
        is_group = pic_m is None
        parent = next((item for item in reversed(hierarchy) if item.is_group), None)
        variable = CobolVar(
            level=level,
            name=name,
            pic=pic_m.group(1) if pic_m else None,
            value=val_m.group(1) if val_m else None,
            is_group=is_group,
            is_array=occ_m is not None,
            occurs=int(occ_m.group(1)) if occ_m else None,
            depending_on=occ_m.group(2) if occ_m and occ_m.group(2) else None,
            parent_name=parent.name if parent else None,
        )
        variables.append(variable)
        hierarchy.append(variable)
    return variables

# Patch 3: verbos que abren sentencia. Se usan para partir buffers concatenados.
STATEMENT_VERBS = frozenset({
    "MOVE", "DISPLAY", "ACCEPT", "COMPUTE", "ADD", "SUBTRACT", "MULTIPLY",
    "DIVIDE", "PERFORM", "IF", "ELSE", "END-IF", "END-PERFORM",
    "END-EVALUATE", "EVALUATE", "STOP", "GOBACK", "EXIT",
    "CALL", "OPEN", "CLOSE", "READ", "WRITE", "REWRITE", "DELETE",
    "START", "STRING", "UNSTRING", "INSPECT", "SET", "INITIALIZE",
    "CONTINUE", "RETURN", "SEARCH", "SORT", "MERGE", "GO", "ALTER",
})


def split_concat_statements(text: str) -> list[str]:
    """
    Divide un buffer que contiene varias sentencias COBOL concatenadas.
    Heurística: un nuevo statement empieza donde aparece un verbo COBOL
    que no es el primero del buffer.
    """
    # Keep quoted literals atomic: they may contain spaces, verbs, terminators,
    # or the inline-comment marker, none of which should split a statement.
    tokens = re.findall(r"""'(?:''|[^'])*'|"(?:\"\"|[^"])*"|\S+""", text)
    if not tokens:
        return []
    statements: list[str] = []
    current = [tokens[0]]
    for tok in tokens[1:]:
        clean = tok.upper().strip(".,")
        if clean in STATEMENT_VERBS:
            statements.append(" ".join(current))
            current = [tok]
        else:
            current.append(tok)
    if current:
        statements.append(" ".join(current))
    return statements


def split_paragraph_into_units(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    units: list[tuple[int, str]] = []
    buffer: list[str] = []
    buffer_start = 0

    def flush():
        nonlocal buffer, buffer_start
        if not buffer:
            return
        text = " ".join(buffer)
        for i, stmt in enumerate(split_concat_statements(text)):
            line = buffer_start + i  # aproximación: numera por offset
            units.append((line, stmt))
        buffer = []

    for num, raw in lines:
        text = raw.strip()
        if not text:
            continue
        upper = text.upper().rstrip(".")

        if upper == "ELSE":
            flush()
            units.append((num, "ELSE"))
            continue

        if upper.startswith("WHEN "):
            flush()
            units.append((num, text.strip()))
            continue

        # Scope terminators must be standalone parser units. Otherwise a
        # preceding DISPLAY without a period can absorb END-IF as an operand.
        if upper in ("END-IF", "END-PERFORM", "END-EVALUATE"):
            flush()
            units.append((num, upper))
            continue

        if not buffer:
            buffer_start = num
        buffer.append(text)

        ends_unit = (
            text.endswith(".")
            or upper in ("END-IF", "END-PERFORM", "END-EVALUATE")
            or upper.endswith("THEN")
            or upper.startswith("EVALUATE")
            or upper.startswith("WHEN ")
        )
        if ends_unit:
            flush()

    flush()
    return units


RE_IF_OPEN = re.compile(r"^IF\s+(.+?)(?:\s+THEN)?$", re.IGNORECASE | re.DOTALL)
RE_EVALUATE_OPEN = re.compile(r"^EVALUATE\s+(.+)$", re.IGNORECASE)


def build_tree(units: list[tuple[int, str]]) -> list[Node]:
    """Build nested blocks with one stack, so mixed/nested scopes close correctly."""
    root: list[Node] = []
    current_list = root
    # Each frame stores (block kind, opening node, list to resume after closing).
    stack: list[tuple[str, Node, list[Node]]] = []

    for line, text in units:
        normalized = text.strip().rstrip(".").strip()
        upper = normalized.upper()

        if upper == "ELSE":
            if stack and stack[-1][0] == "if":
                current_list = stack[-1][1].else_branch
            else:
                current_list.append(Node(kind="malformed", text="ELSE without matching IF", line=line))
            continue

        if upper.startswith("WHEN "):
            if stack and stack[-1][0] == "evaluate":
                branch = Node(kind="when", text=normalized[5:].strip(), line=line)
                stack[-1][1].body.append(branch)
                current_list = branch.then_branch
            else:
                current_list.append(Node(kind="malformed", text=f"{normalized} without matching EVALUATE", line=line))
            continue

        if upper in ("END-IF", "END-PERFORM", "END-EVALUATE"):
            expected = {
                "END-IF": "if",
                "END-PERFORM": "perform",
                "END-EVALUATE": "evaluate",
            }[upper]
            if stack and stack[-1][0] == expected:
                _, _, parent_list = stack.pop()
                current_list = parent_list
            else:
                current_list.append(Node(
                    kind="malformed",
                    text=f"{upper} without matching open block",
                    line=line,
                ))
            continue

        m = RE_IF_OPEN.match(normalized)
        if m:
            node = Node(kind="if", text=normalized, line=line)
            current_list.append(node)
            stack.append(("if", node, current_list))
            current_list = node.then_branch
            continue

        inline_times = re.match(r"^PERFORM\s+(\d+)\s+TIMES$", upper)
        if inline_times:
            node = Node(kind="perform_times_inline", text=normalized, line=line)
            current_list.append(node)
            stack.append(("perform", node, current_list))
            current_list = node.body
            continue

        if (
            upper == "PERFORM"
        ):
            node = Node(kind="perform_inline", text=normalized, line=line)
            current_list.append(node)
            stack.append(("perform", node, current_list))
            current_list = node.body
            continue

        m = RE_EVALUATE_OPEN.match(normalized)
        if m:
            node = Node(kind="evaluate", text=normalized, line=line)
            current_list.append(node)
            stack.append(("evaluate", node, current_list))
            current_list = node.body
            continue

        current_list.append(Node(kind="stmt", text=normalized, line=line))

    # Preserve malformed/unclosed scopes visibly instead of silently resetting
    # the parser to the root list. Comments remain valid Python output.
    for kind, node, _ in reversed(stack):
        current_list.append(Node(
            kind="malformed",
            text=f"Unclosed {kind.upper()} opened at source line {node.line}",
            line=node.line,
        ))
    return root

def parse_procedure(lines: list[tuple[int, str]]) -> tuple[dict[str, list[Node]], list[str]]:
    paragraph_lines: dict[str, list[tuple[int, str]]] = {}
    order: list[str] = []
    current = "__MAIN__"
    paragraph_lines[current] = []
    order.append(current)

    for num, text in lines:
        stripped = text.strip()
        m = RE_PARAGRAPH.match(stripped)
        if m and m.group(1).upper() not in {"GOBACK", "CONTINUE", "EXIT"}:
            current = m.group(1).upper()
            if current not in paragraph_lines:
                paragraph_lines[current] = []
                order.append(current)
            continue
        paragraph_lines[current].append((num, text))

    paragraphs: dict[str, list[Node]] = {}
    for name, plines in paragraph_lines.items():
        units = split_paragraph_into_units(plines)
        paragraphs[name] = build_tree(units)
    return paragraphs, order


def resolve_copybooks(
    source: str,
    copybook_paths: Optional[list[str | Path]] = None,
    source_path: Optional[str | Path] = None,
) -> tuple[str, list[str]]:
    """Expand simple COPY directives, recording missing files and cycles.

    Search order is the source file's directory, each explicit --copybook-path
    directory, then the current working directory. COPY ... REPLACING and
    library-qualified COPY forms are intentionally reported as unresolved.
    """
    roots: list[Path] = []
    if source_path is not None:
        roots.append(Path(source_path).resolve().parent)
    roots.extend(Path(path).resolve() for path in (copybook_paths or []))
    roots.append(Path.cwd().resolve())
    unique_roots: list[Path] = []
    for root in roots:
        if root not in unique_roots:
            unique_roots.append(root)

    unresolved: list[str] = []

    def record(message: str) -> None:
        if message not in unresolved:
            unresolved.append(message)

    def locate(name: str, search_roots: list[Path]) -> Optional[Path]:
        candidates = [name, name.lower(), name.upper()]
        if not Path(name).suffix:
            candidates.extend([
                name + ".cpy", name + ".CPY", name + ".Cpy",
                name + ".cbl", name + ".CBL", name + ".cob", name + ".COB",
            ])
        seen: set[str] = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            for root in search_roots:
                path = root / candidate
                if path.is_file():
                    return path.resolve()
        return None

    def expand(text: str, search_roots: list[Path], stack: list[Path]) -> list[str]:
        output: list[str] = []
        for line in text.splitlines():
            code_line = strip_inline_comment(line)
            # Accept free-format COPY and the common six-column fixed-format
            # sequence prefix. Other COPY syntax is left visible as a warning.
            match = re.match(
                r"^\s*(?:\d{6}[ \t]+)?COPY\s+([A-Za-z0-9_.-]+)(.*?)\s*\.\s*$",
                code_line,
                re.IGNORECASE,
            )
            if not match:
                output.append(line)
                continue
            name, suffix = match.groups()
            if suffix.strip():
                record(f"COPYBOOK UNSUPPORTED CLAUSE: {line.strip()}")
                output.append(f"*> COBOL2PY UNRESOLVED COPYBOOK: {line.strip()}")
                continue
            resolved = locate(name, search_roots)
            if resolved is None:
                record(f"COPYBOOK NOT FOUND: {name} (searched: {', '.join(str(p) for p in search_roots)})")
                output.append(f"*> COBOL2PY UNRESOLVED COPYBOOK: {name}")
                continue
            if resolved in stack:
                chain = " -> ".join(path.name for path in stack + [resolved])
                record(f"COPYBOOK CYCLE: {chain}")
                output.append(f"*> COBOL2PY COPYBOOK CYCLE: {chain}")
                continue
            try:
                nested_source = resolved.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                record(f"COPYBOOK READ ERROR: {resolved}: {exc}")
                output.append(f"*> COBOL2PY UNRESOLVED COPYBOOK: {name}")
                continue
            nested_roots = [resolved.parent] + [root for root in search_roots if root != resolved.parent]
            output.extend(expand(nested_source, nested_roots, stack + [resolved]))
        return output

    return "\n".join(expand(source, unique_roots, [])), unresolved


def parse_cobol(
    source: str,
    source_format: str = "auto",
    copybook_paths: Optional[list[str | Path]] = None,
    source_path: Optional[str | Path] = None,
) -> Program:
    source, unresolved_copybooks = resolve_copybooks(
        source, copybook_paths=copybook_paths, source_path=source_path
    )
    lines = preprocess(source, source_format=source_format)
    prog = Program()
    prog.unresolved_copybooks = unresolved_copybooks
    prog.raw_lines = lines

    idx_ident = idx_data = idx_proc = -1
    for i, (_, t) in enumerate(lines):
        if idx_ident < 0 and RE_IDENT.search(t):
            idx_ident = i
        elif idx_data < 0 and RE_DATA.search(t):
            idx_data = i
        elif idx_proc < 0 and RE_PROC.search(t):
            idx_proc = i

    for _, t in lines:
        m = RE_PROGRAM_ID.search(t)
        if m:
            prog.program_id = m.group(1).upper()
            break

    if idx_data >= 0:
        end_data = idx_proc if idx_proc > 0 else len(lines)
        ws_start = None
        for i in range(idx_data, end_data):
            if RE_WORKING_STORAGE.search(lines[i][1]):
                ws_start = i + 1
                break
        if ws_start is not None:
            prog.variables = parse_variables(lines[ws_start:end_data])

    if idx_proc >= 0:
        proc_lines = lines[idx_proc + 1:]
        prog.paragraphs, prog.paragraph_order = parse_procedure(proc_lines)

    return prog


# ============================================================================
# 4. TRADUCCIÓN
# ============================================================================

JAVA_RESERVED_WORDS = frozenset({
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while", "true", "false", "null",
    "_", "record", "sealed", "permits", "var", "yield",
})


def normalize_identifier(name: str) -> str:
    normalized = name.replace("-", "_").lower()
    if keyword.iskeyword(normalized) or normalized in JAVA_RESERVED_WORDS:
        return "cobol_" + normalized
    return normalized


def normalize_name(name: str) -> str:
    # Normalize identifiers consistently for both target languages and avoid
    # Python/Java reserved words. This also applies to identifiers in subscripts.
    normalized = re.sub(
        r"[A-Za-z][A-Za-z0-9-]*",
        lambda match: normalize_identifier(match.group(0)),
        name,
    )

    # COBOL table subscripts are 1-based; Python lists are 0-based.
    def normalize_subscript(match: re.Match[str]) -> str:
        subscript = match.group(1)
        if subscript.isdigit():
            return f"[{int(subscript) - 1}]"
        return f"[{normalize_identifier(subscript)} - 1]"

    return re.sub(r"\(([A-Za-z0-9_-]+)\)", normalize_subscript, normalized)

def normalize_data_reference(
    name: str,
    variables: Optional[dict[str, CobolVar]] = None,
) -> str:
    """Map a COBOL data-name (including OF/IN qualification) into nested dicts."""
    text = name.strip()
    match = re.fullmatch(
        r"([A-Za-z0-9-]+)(?:\(([A-Za-z0-9_-]+)\))?(?:\s+(?:OF|IN)\s+([A-Za-z0-9-]+))?",
        text,
        re.IGNORECASE,
    )
    if not match:
        return normalize_name(text)
    field_name, subscript, qualifier = match.groups()
    variable_map = variables or {}
    if qualifier:
        parent_expr = normalize_data_reference(qualifier, variable_map)
        expr = f"{parent_expr}[{normalize_name(field_name)!r}]"
    else:
        variable = variable_map.get(field_name.upper())
        if variable is not None and variable.parent_name:
            parent_expr = normalize_data_reference(variable.parent_name, variable_map)
            expr = f"{parent_expr}[{normalize_name(field_name)!r}]"
        else:
            expr = normalize_name(field_name)
    if subscript:
        if subscript.isdigit():
            expr += f"[{int(subscript) - 1}]"
        else:
            expr += f"[{normalize_name(subscript)} - 1]"
    return expr


def decode_cobol_quoted_literal(token: str) -> Optional[str]:
    """Decode a complete COBOL quoted literal, including doubled quote escapes."""
    text = token.strip()
    if len(text) < 2 or text[0] not in ("'", '"') or text[-1] != text[0]:
        return None
    quote = text[0]
    inner = text[1:-1]
    # A matching quote inside a COBOL literal is represented by two copies.
    return inner.replace(quote + quote, quote)


def translate_literal(
    token: str,
    variables: Optional[dict[str, CobolVar]] = None,
) -> str:
    t = token.strip()
    if not t:
        return '""'
    all_literal = re.fullmatch(r"""ALL\s+(["'])(.*?)\1""", t, re.IGNORECASE)
    if all_literal:
        return repr(all_literal.group(2))
    quoted = decode_cobol_quoted_literal(t)
    if quoted is not None:
        return json.dumps(quoted, ensure_ascii=False)
    if re.match(r"^[+-]?\d+$", t):
        return t
    if re.match(r"^[+-]?\d+\.\d+$", t):
        return t
    if t.upper() in ("SPACES", "SPACE"):
        return json.dumps(" ")
    if t.upper() in ("ZEROS", "ZERO", "ZEROES", "ZEROES"):
        return "0"
    if t.upper() in ("LOW-VALUE", "LOW-VALUES"):
        return repr("\x00")
    if t.upper() in ("HIGH-VALUE", "HIGH-VALUES"):
        return repr("\xff")
    if t.upper() == "TRUE":
        return "True"
    if t.upper() == "FALSE":
        return "False"
    if t.upper() in ("QUOTE", "QUOTES"):
        return repr('"')
    return normalize_data_reference(t, variables)


def translate_expr(
    expr: str,
    variables: Optional[dict[str, CobolVar]] = None,
) -> str:
    # Rewrite qualified data-names first; unqualified child names are resolved
    # through the parsed hierarchy when they are unambiguous in the model.
    expr = re.sub(
        r"\b[A-Za-z][A-Za-z0-9-]*(?:\([A-Za-z0-9_-]+\))?\s+(?:OF|IN)\s+[A-Za-z][A-Za-z0-9-]*",
        lambda match: normalize_data_reference(match.group(0), variables),
        expr,
        flags=re.IGNORECASE,
    )
    expr = re.sub(
        r"\b([A-Za-z][A-Za-z0-9-]*)\(([A-Za-z0-9_-]+)\)",
        lambda match: normalize_data_reference(match.group(0), variables),
        expr,
    )
    token_pattern = r"""("(?:[^"]|"")*"|'(?:[^']|'')*'|[A-Za-z][A-Za-z0-9-]*|\d+(?:\.\d+)?|<=|>=|<>|==|!=|[()+*/=<>&\[\]-]|\s+|.)"""
    tokens = re.findall(token_pattern, expr)
    out = []
    for tok in tokens:
        if tok.startswith(('"', "'")):
            out.append(translate_literal(tok, variables))
        elif tok.lower() in ("and", "or", "not"):
            out.append(tok.lower())
        elif tok.upper() in ("TRUE", "FALSE"):
            out.append("True" if tok.upper() == "TRUE" else "False")
        elif re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", tok):
            out.append(normalize_data_reference(tok, variables))
        else:
            out.append(tok)
    return "".join(out).strip()


# Patch 1: normalización de operadores
def rewrite_outside_literals(text: str, transform) -> str:
    """Rewrite COBOL operators without modifying quoted literal contents."""
    protected: list[str] = []
    literals: list[tuple[str, str]] = []
    i = 0
    while i < len(text):
        if text[i] not in ("'", '"'):
            protected.append(text[i])
            i += 1
            continue
        quote = text[i]
        start = i
        i += 1
        while i < len(text):
            if text[i] == quote:
                if i + 1 < len(text) and text[i + 1] == quote:
                    i += 2
                    continue
                i += 1
                break
            i += 1
        marker = f"COBOL_LITERAL_TOKEN_{len(literals)}"
        literals.append((marker, text[start:i]))
        protected.append(marker)
    rewritten = transform("".join(protected))
    for marker, literal in literals:
        rewritten = rewritten.replace(marker, literal)
    return rewritten


def translate_condition(cond: str, variables: Optional[dict[str, CobolVar]] = None) -> str:
    def rewrite(chunk: str) -> str:
        c = re.sub(r"\bAND\b", "and", chunk, flags=re.IGNORECASE)
        c = re.sub(r"\bOR\b", "or", c, flags=re.IGNORECASE)
        c = re.sub(r"\bNOT\b", "not", c, flags=re.IGNORECASE)
        c = re.sub(r"\bIS\s+NOT\s+EQUAL\s+TO\b", "!=", c, flags=re.IGNORECASE)
        c = re.sub(r"\bNOT\s+EQUAL\s+TO\b", "!=", c, flags=re.IGNORECASE)
        c = re.sub(r"\bIS\s+EQUAL\s+TO\b", "==", c, flags=re.IGNORECASE)
        c = re.sub(r"\bEQUAL\s+TO\b", "==", c, flags=re.IGNORECASE)
        c = re.sub(r"\bIS\s+GREATER\s+THAN\b", ">", c, flags=re.IGNORECASE)
        c = re.sub(r"\bGREATER\s+THAN\b", ">", c, flags=re.IGNORECASE)
        c = re.sub(r"\bIS\s+LESS\s+THAN\b", "<", c, flags=re.IGNORECASE)
        c = re.sub(r"\bLESS\s+THAN\b", "<", c, flags=re.IGNORECASE)
        c = re.sub(r"\bIS\b", "==", c, flags=re.IGNORECASE)
        c = re.sub(r"(?<![!<>=])=(?!=)", "==", c)
        return c.replace("<>", "!=")

    c = rewrite_outside_literals(cond.strip(), rewrite)
    translated = translate_expr(c, variables)
    if not variables:
        return translated

    # COBOL pads the shorter operand with spaces for alphanumeric comparisons.
    # Match a translated data-name (including a table element) against a literal.
    def pad_literal(match: re.Match[str]) -> str:
        left, operator, literal_token = match.groups()
        try:
            literal = ast.literal_eval(literal_token)
        except (SyntaxError, ValueError):
            return match.group(0)
        if not isinstance(literal, str):
            return match.group(0)
        base = re.match(r"[a-z_][a-z0-9_]*", left)
        if base is None:
            return match.group(0)
        field_keys = re.findall(r"\['([a-z_][a-z0-9_]*)'\]", left)
        lookup_name = field_keys[-1] if field_keys else base.group(0)
        variable = next(
            (item for item in variables.values()
             if normalize_name(item.name) == lookup_name),
            None,
        )
        if variable is None or not variable.pic:
            return match.group(0)
        pic = variable.pic.upper()
        if not any(char in pic for char in ("X", "A")):
            return match.group(0)
        width = pic_character_count(pic)
        if not width:
            return match.group(0)
        compare_width = max(width, len(literal))
        padded = literal.ljust(compare_width)
        return f"{left}.ljust({compare_width}) {operator} {padded!r}"

    return re.sub(
        r"""([a-z_][a-z0-9_]*(?:\[[^\]]+\])*)\s*(==|!=)\s*("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')""",
        pad_literal,
        translated,
    )

def pic_digit_count(pic: str) -> int:
    """Count storage digits in a simple numeric PIC, including repetitions."""
    return sum(
        int(match.group(1)) if match.group(1) else 1
        for match in re.finditer(r"9(?:\((\d+)\))?", pic.upper())
    )


def translate_display_item(token: str, variables: dict[str, CobolVar]) -> str:
    """Emit a string expression matching basic COBOL DISPLAY formatting."""
    base_match = re.match(r"[A-Za-z0-9-]+", token)
    variable = variables.get(base_match.group(0).upper()) if base_match else None
    if variable is not None and variable.pic:
        pic = variable.pic.upper()
        if "9" in pic:
            digits = pic_digit_count(pic)
            scale = pic_digit_count(pic.split("V", 1)[1]) if "V" in pic else 0
            name = normalize_data_reference(token, variables)
            if scale:
                # V is an implied decimal point in COBOL storage; DISPLAY emits
                # the digit positions, not a visible decimal separator.
                return f"format(float({name}), '.{scale}f').replace('.', '').zfill({digits})"
            return f"str(int(float({name}))).zfill({digits})"
    return f"str({translate_literal(token, variables)})"

def pic_character_count(pic: str) -> int:
    """Count positions in a simple alphanumeric PIC such as X(10) or XX."""
    return sum(
        int(match.group(1)) if match.group(1) else 1
        for match in re.finditer(r"[XA](?:\((\d+)\))?", pic.upper())
    )


def translate_move_value(source: str, target: str, variables: dict[str, CobolVar]) -> str:
    """Translate MOVE with basic receiving-field size semantics.

    For alphanumeric PICs, COBOL right-pads short values with spaces and
    truncates values that exceed the receiving field. Other PIC categories
    retain the existing simple assignment behavior.
    """
    value = translate_literal(source, variables)
    target_base = re.match(r"([A-Za-z0-9-]+)", target)
    variable = variables.get(target_base.group(1).upper()) if target_base else None
    if variable is not None and variable.pic:
        pic = variable.pic.upper()
        if "X" in pic or "A" in pic:
            width = pic_character_count(pic)
            if width:
                all_literal = re.fullmatch(r"""ALL\s+(["'])(.*?)\1""", source.strip(), re.IGNORECASE)
                if all_literal:
                    return repr((all_literal.group(2) * width)[:width])
                if source.strip().upper() in ("SPACE", "SPACES"):
                    return repr(" " * width)
                if source.strip().upper() in ("LOW-VALUE", "LOW-VALUES"):
                    return repr("\x00" * width)
                if source.strip().upper() in ("HIGH-VALUE", "HIGH-VALUES"):
                    return repr("\xff" * width)
                return f"str({value})[:{width}].ljust({width})"
        # Numeric MOVE keeps the low-order receiving digits. For implied
        # decimal pictures, scale first, truncate excess fractional digits,
        # then retain the receiving picture's total digit capacity.
        if "9" in pic and "P" not in pic:
            digits = pic_digit_count(pic)
            if "V" in pic:
                scale = pic_digit_count(pic.split("V", 1)[1])
                if digits:
                    factor = 10 ** scale
                    magnitude = f"int(abs(float({value})) * {factor}) % (10 ** {digits})"
                    sign = f"(-1 if float({value}) < 0 else 1)"
                    return f"{sign} * ({magnitude} / {factor})"
            elif digits:
                if "S" in pic:
                    return f"(-1 if int({value}) < 0 else 1) * (abs(int({value})) % (10 ** {digits}))"
                return f"int({value}) % (10 ** {digits})"
    return value


COBOL_TOKEN_RE = re.compile(
    r'"(?:[^"]|"")*"|\'(?:[^\']|\'\')*\'|[A-Za-z][A-Za-z0-9-]*(?:\([A-Za-z0-9_-]+\))?(?:\s+(?:OF|IN)\s+[A-Za-z][A-Za-z0-9-]*)?|,?\s*|(?:\S+)',
    re.IGNORECASE,
)


def split_cobol_items(s: str) -> list[str]:
    tokens = []
    for m in COBOL_TOKEN_RE.finditer(s):
        tok = m.group(0).strip().strip(",")
        if tok:
            tokens.append(tok)
    return tokens


DATA_REF_PATTERN = r"[A-Za-z0-9-]+(?:\([A-Za-z0-9_-]+\))?(?:\s+(?:OF|IN)\s+[A-Za-z0-9-]+)?"


def translate_statement(
    stmt: str,
    paragraphs: set[str],
    variables: Optional[dict[str, CobolVar]] = None,
) -> Optional[list[str]]:
    s = stmt.strip().rstrip(".").strip()
    if not s:
        return None
    upper = s.upper()

    if upper in ("STOP RUN", "STOP RUN."):
        return ["raise _CobolStopRun"]
    if upper.startswith("EXIT PROGRAM") or upper == "GOBACK":
        return ["return"]
    if upper in ("CONTINUE", "EXIT"):
        return ["pass"]

    m = re.match(r"DISPLAY\s+(.+)", s, re.IGNORECASE)
    if m:
        args = split_cobol_items(m.group(1))
        # COBOL DISPLAY concatenates operands. Numeric DISPLAY items also
        # retain the zero-filled width specified by their PIC clause.
        items = ", ".join(
            translate_display_item(a, variables or {}) for a in args
        )
        return [f'print("".join([{items}]))']

    m = re.match(rf"ACCEPT\s+({DATA_REF_PATTERN})$", s, re.IGNORECASE)
    if m:
        return [f"{normalize_data_reference(m.group(1), variables)} = input()"]

    m = re.match(rf"MOVE\s+(.+?)\s+TO\s+({DATA_REF_PATTERN})$", s, re.IGNORECASE)
    if m:
        target = m.group(2)
        value = translate_move_value(m.group(1), target, variables or {})
        return [f"{normalize_data_reference(target, variables)} = {value}"]

    m = re.match(rf"COMPUTE\s+({DATA_REF_PATTERN})\s*=\s*(.+)", s, re.IGNORECASE)
    if m:
        return [f"{normalize_data_reference(m.group(1), variables)} = {translate_expr(m.group(2), variables)}"]

    # Patch 4: ADD con múltiples operandos
    m = re.match(rf"ADD\s+(.+?)\s+TO\s+({DATA_REF_PATTERN})$", s, re.IGNORECASE)
    if m:
        operands = split_cobol_items(m.group(1))
        sum_expr = " + ".join(translate_literal(o, variables) for o in operands)
        return [f"{normalize_data_reference(m.group(2), variables)} += {sum_expr}"]

    m = re.match(rf"SUBTRACT\s+(.+?)\s+FROM\s+({DATA_REF_PATTERN})$", s, re.IGNORECASE)
    if m:
        operands = split_cobol_items(m.group(1))
        sum_expr = " + ".join(translate_literal(o, variables) for o in operands)
        return [f"{normalize_data_reference(m.group(2), variables)} -= {sum_expr}"]

    m = re.match(rf"MULTIPLY\s+(.+?)\s+BY\s+({DATA_REF_PATTERN})$", s, re.IGNORECASE)
    if m:
        return [f"{normalize_data_reference(m.group(2), variables)} *= {translate_literal(m.group(1), variables)}"]

    m = re.match(rf"DIVIDE\s+(.+?)\s+INTO\s+({DATA_REF_PATTERN})$", s, re.IGNORECASE)
    if m:
        return [f"{normalize_data_reference(m.group(2), variables)} /= {translate_literal(m.group(1), variables)}"]

    m = re.match(r"PERFORM\s+([A-Za-z0-9\-]+)\s+(\d+)\s+TIMES", s, re.IGNORECASE)
    if m and m.group(1).upper() in paragraphs:
        return [f"for _ in range({m.group(2)}):", f"{normalize_name(m.group(1))}()"]

    m = re.match(r"PERFORM\s+([A-Za-z0-9\-]+)\s+UNTIL\s+(.+)", s, re.IGNORECASE)
    if m and m.group(1).upper() in paragraphs:
        return [
            f"while not ({translate_condition(m.group(2), variables or {})}):",
            f"{normalize_name(m.group(1))}()",
        ]

    m = re.match(r"PERFORM\s+([A-Za-z0-9\-]+)", s, re.IGNORECASE)
    if m and m.group(1).upper() in paragraphs:
        return [f"{normalize_name(m.group(1))}()"]

    if upper.startswith("PERFORM"):
        return [f"# PERFORM no traducido: {s}"]

    return [f"# COBOL no traducido: {s}"]


def translate_nodes(
    nodes: list[Node],
    paragraphs: set[str],
    indent: int,
    variables: Optional[dict[str, CobolVar]] = None,
) -> list[str]:
    out: list[str] = []
    for node in nodes:
        if node.kind == "stmt":
            lines = translate_statement(node.text, paragraphs, variables)
            if lines:
                opens_block = lines[0].rstrip().endswith(":")
                for i, line in enumerate(lines):
                    line_indent = indent + 1 if opens_block and i > 0 else indent
                    out.append("    " * line_indent + line.strip())

        elif node.kind == "if":
            m = RE_IF_OPEN.match(node.text)
            if not m:
                out.append("    " * indent + f"# IF malformado: {node.text}")
                continue
            cond = translate_condition(m.group(1), variables)
            out.append("    " * indent + f"if {cond}:")
            then_body = translate_nodes(node.then_branch, paragraphs, indent + 1, variables)
            if not then_body:
                then_body = ["    " * (indent + 1) + "pass"]
            elif all(not line.strip() or line.strip().startswith("#") for line in then_body):
                then_body.append("    " * (indent + 1) + "pass")
            out.extend(then_body)
            if node.else_branch:
                out.append("    " * indent + "else:")
                else_body = translate_nodes(node.else_branch, paragraphs, indent + 1, variables)
                if not else_body:
                    else_body = ["    " * (indent + 1) + "pass"]
                elif all(not line.strip() or line.strip().startswith("#") for line in else_body):
                    else_body.append("    " * (indent + 1) + "pass")
                out.extend(else_body)

        elif node.kind == "perform_inline":
            out.append("    " * indent + f"# PERFORM inline: {node.text}")
            body = translate_nodes(node.body, paragraphs, indent + 1, variables)
            if not body:
                body = ["    " * (indent + 1) + "pass"]
            elif all(not line.strip() or line.strip().startswith("#") for line in body):
                body.append("    " * (indent + 1) + "pass")
            out.extend(body)

        elif node.kind == "perform_times_inline":
            match = re.match(r"^PERFORM\s+(\d+)\s+TIMES$", node.text, re.IGNORECASE)
            count = match.group(1) if match else "0"
            out.append("    " * indent + f"for _ in range({count}):")
            body = translate_nodes(node.body, paragraphs, indent + 1, variables)
            if not body or all(not line.strip() or line.strip().startswith("#") for line in body):
                body = ["    " * (indent + 1) + "pass"]
            out.extend(body)

        elif node.kind == "evaluate":
            subject = node.text[len("EVALUATE"):].strip()
            is_boolean = subject.upper() in ("TRUE", "FALSE")
            temp_name = f"_cobol_evaluate_{node.line}"
            if not is_boolean:
                out.append("    " * indent + f"{temp_name} = {translate_expr(subject)}")
            emitted = 0
            for branch in node.body:
                if branch.kind != "when":
                    out.append("    " * indent + f"# COBOL no traducido dentro de EVALUATE: {branch.text}")
                    continue
                choice = branch.text.strip()
                if choice.upper() == "OTHER":
                    condition = "True" if emitted == 0 else None
                    prefix = "if True:" if condition else "else:"
                else:
                    if is_boolean:
                        condition = translate_condition(choice, variables)
                        if subject.upper() == "FALSE":
                            condition = f"not ({condition})"
                    elif re.search(r"\s+(?:THRU|THROUGH)\s+", choice, re.IGNORECASE):
                        low, high = re.split(r"\s+(?:THRU|THROUGH)\s+", choice, maxsplit=1, flags=re.IGNORECASE)
                        condition = f"{temp_name} >= {translate_literal(low)} and {temp_name} <= {translate_literal(high)}"
                    else:
                        condition = f"{temp_name} == {translate_literal(choice)}"
                    prefix = ("if " if emitted == 0 else "elif ") + condition + ":"
                out.append("    " * indent + prefix)
                branch_body = translate_nodes(branch.then_branch, paragraphs, indent + 1, variables)
                if not branch_body:
                    branch_body = ["    " * (indent + 1) + "pass"]
                elif all(not line.strip() or line.strip().startswith("#") for line in branch_body):
                    branch_body.append("    " * (indent + 1) + "pass")
                out.extend(branch_body)
                emitted += 1
            if emitted == 0:
                out.append("    " * indent + f"# EVALUATE sin WHEN: {node.text}")

        elif node.kind == "malformed":
            out.append("    " * indent + f"# COBOL estructura malformada: {node.text}")

    return out


def translate_paragraph(
    nodes: list[Node],
    paragraphs: set[str],
    variables: Optional[dict[str, CobolVar]] = None,
) -> list[str]:
    return translate_nodes(nodes, paragraphs, indent=1, variables=variables)


def java_group_class_name(variable: CobolVar, variables: dict[str, CobolVar]) -> str:
    names = [variable.name]
    parent_name = variable.parent_name
    while parent_name and parent_name in variables:
        parent = variables[parent_name]
        names.append(parent.name)
        parent_name = parent.parent_name
    suffix = "".join(
        part[:1].upper() + part[1:].lower()
        for name in reversed(names)
        for part in re.split(r"[-_]+", name)
        if part
    )
    return "CobolGroup" + suffix


def java_data_reference(name: str, variables: dict[str, CobolVar]) -> str:
    text = name.strip()
    match = re.fullmatch(
        r"([A-Za-z0-9-]+)(?:\(([A-Za-z0-9_-]+)\))?(?:\s+(?:OF|IN)\s+([A-Za-z0-9-]+))?",
        text,
        re.IGNORECASE,
    )
    if not match:
        return normalize_name(text)
    field_name, subscript, qualifier = match.groups()
    if qualifier:
        expr = java_data_reference(qualifier, variables) + "." + normalize_name(field_name)
    else:
        variable = variables.get(field_name.upper())
        if variable is not None and variable.parent_name:
            expr = java_data_reference(variable.parent_name, variables) + "." + normalize_name(field_name)
        else:
            expr = normalize_name(field_name)
    if subscript:
        index = str(int(subscript) - 1) if subscript.isdigit() else f"{normalize_name(subscript)} - 1"
        expr += f".get({index})"
    return expr


def java_string_literal(value: str) -> str:
    # Java processes Unicode escapes before tokenization; use an octal escape for NUL.
    return json.dumps(value, ensure_ascii=False).replace(r"\u0000", r"\000")


def translate_java_literal(token: str, variables: dict[str, CobolVar]) -> str:
    t = token.strip()
    if not t:
        return '""'
    all_literal = re.fullmatch(r"""ALL\s+(["'])(.*?)\1""", t, re.IGNORECASE)
    if all_literal:
        return java_string_literal(all_literal.group(2))
    quoted = decode_cobol_quoted_literal(t)
    if quoted is not None:
        return java_string_literal(quoted)
    if re.match(r"^[+-]?\d+(?:\.\d+)?$", t):
        return t
    if t.upper() in ("SPACE", "SPACES"):
        return java_string_literal(" ")
    if t.upper() in ("ZERO", "ZEROS", "ZEROES"):
        return "0"
    if t.upper() in ("LOW-VALUE", "LOW-VALUES"):
        return java_string_literal("\x00")
    if t.upper() in ("HIGH-VALUE", "HIGH-VALUES"):
        return java_string_literal("\xff")
    if t.upper() in ("QUOTE", "QUOTES"):
        return '"\\\""'
    if t.upper() == "TRUE":
        return "true"
    if t.upper() == "FALSE":
        return "false"
    return java_data_reference(t, variables)


def translate_java_expr(expr: str, variables: dict[str, CobolVar]) -> str:
    expr = re.sub(
        r"\b[A-Za-z][A-Za-z0-9-]*(?:\([A-Za-z0-9_-]+\))?\s+(?:OF|IN)\s+[A-Za-z][A-Za-z0-9-]*",
        lambda match: java_data_reference(match.group(0), variables),
        expr,
        flags=re.IGNORECASE,
    )
    expr = re.sub(
        r"\b([A-Za-z][A-Za-z0-9-]*)\(([A-Za-z0-9_-]+)\)",
        lambda match: java_data_reference(match.group(0), variables),
        expr,
    )
    token_pattern = r"""("(?:[^"]|"")*"|'(?:[^']|'')*'|[A-Za-z][A-Za-z0-9-]*|\d+(?:\.\d+)?|<=|>=|<>|==|!=|[()+*/=<>&\[\]-]|\s+|.)"""
    out: list[str] = []
    for token in re.findall(token_pattern, expr):
        if token.startswith(('"', "'")):
            out.append(translate_java_literal(token, variables))
        elif re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", token):
            out.append(translate_java_literal(token, variables))
        else:
            out.append(token)
    return "".join(out).strip()


def translate_java_condition(condition: str, variables: dict[str, CobolVar]) -> str:
    text = condition.strip()
    string_comparison = re.fullmatch(
        r"""(.+?)\s*(IS\s+NOT\s+EQUAL\s+TO|NOT\s+EQUAL\s+TO|IS\s+EQUAL\s+TO|EQUAL\s+TO|==|=|!=|<>)\s*("(?:[^"]|"")*"|'(?:[^']|'')*')""",
        text,
        re.IGNORECASE,
    )
    if string_comparison:
        left, operator, literal_token = string_comparison.groups()
        literal = decode_cobol_quoted_literal(literal_token)
        if literal is None:
            literal = literal_token[1:-1]
        base = re.match(r"[A-Za-z0-9-]+", left.strip())
        variable = variables.get(base.group(0).upper()) if base else None
        if variable is not None and variable.pic and any(char in variable.pic.upper() for char in ("X", "A")):
            width = pic_character_count(variable.pic)
            padded = literal.ljust(max(width, len(literal)))
            equality = f"Objects.equals({java_data_reference(left, variables)}, {java_string_literal(padded)})"
            positive = operator in ("=", "==") or operator.upper().split() in (
                ["EQUAL", "TO"], ["IS", "EQUAL", "TO"]
            )
            return equality if positive else "!(" + equality + ")"
    def rewrite(chunk: str) -> str:
        text = re.sub(r"\bIS\s+NOT\s+EQUAL\s+TO\b|\bNOT\s+EQUAL\s+TO\b", "!=", chunk, flags=re.IGNORECASE)
        text = re.sub(r"\bIS\s+EQUAL\s+TO\b|\bEQUAL\s+TO\b", "==", text, flags=re.IGNORECASE)
        text = re.sub(
            r"\bNOT\s+(.+?)(?=\s+\bAND\b|\s+\bOR\b|$)",
            r"!(\1)",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"\bIS\s+GREATER\s+THAN\b|\bGREATER\s+THAN\b", ">", text, flags=re.IGNORECASE)
        text = re.sub(r"\bIS\s+LESS\s+THAN\b|\bLESS\s+THAN\b", "<", text, flags=re.IGNORECASE)
        text = re.sub(r"\bAND\b", "&&", text, flags=re.IGNORECASE)
        text = re.sub(r"\bOR\b", "||", text, flags=re.IGNORECASE)
        text = re.sub(r"\bNOT\b", "!", text, flags=re.IGNORECASE)
        text = re.sub(r"(?<![!<>=])=(?!=)", "==", text).replace("<>", "!=")
        return text

    text = rewrite_outside_literals(text, rewrite)
    return translate_java_expr(text, variables)


def java_type(variable: CobolVar, variables: dict[str, CobolVar]) -> str:
    if variable.is_group:
        base = java_group_class_name(variable, variables)
    elif variable.pic and "V" in variable.pic.upper():
        base = "double"
    elif variable.pic and any(char in variable.pic.upper() for char in ("X", "A")):
        base = "String"
    elif variable.pic and "9" in variable.pic.upper():
        base = "int"
    else:
        base = "Object"
    return f"List<{base}>" if variable.is_array else base


def java_field_default(variable: CobolVar, variables: dict[str, CobolVar]) -> str:
    if variable.is_array:
        count = variable.occurs or 0
        if count <= 0:
            return "new ArrayList<>()"
        element = CobolVar(
            level=variable.level,
            name=variable.name,
            pic=variable.pic,
            value=variable.value,
            is_group=variable.is_group,
        )
        item = java_field_default(element, variables)
        return "new ArrayList<>(Arrays.asList(" + ", ".join(item for _ in range(count)) + "))"
    if variable.is_group:
        return f"new {java_group_class_name(variable, variables)}()"
    pic = (variable.pic or "").upper()
    if any(char in pic for char in ("X", "A")):
        width = pic_character_count(pic)
        if variable.value is None:
            value = '""'
        else:
            all_literal = re.fullmatch(r"""ALL\s+(["'])(.*?)\1""", variable.value, re.IGNORECASE)
            if all_literal:
                value = java_string_literal((all_literal.group(2) * width)[:width])
            elif variable.value.upper() in ("SPACE", "SPACES"):
                value = java_string_literal(" " * width)
            elif variable.value.upper() in ("LOW-VALUE", "LOW-VALUES"):
                value = java_string_literal("\x00" * width)
            elif variable.value.upper() in ("HIGH-VALUE", "HIGH-VALUES"):
                value = java_string_literal("\xff" * width)
            else:
                value = translate_java_literal(variable.value, variables)
        return f"fit({value}, {width})" if width else value
    if variable.value is not None:
        return translate_java_literal(variable.value, variables)
    return "0.0" if "V" in pic else "0"


def java_assignment_statement(
    target: str,
    operator: str,
    value: str,
    variables: dict[str, CobolVar],
) -> str:
    """Emit assignment to a scalar field or a 1-based COBOL table element."""
    match = re.fullmatch(
        r"([A-Za-z0-9-]+)\(([A-Za-z0-9_-]+)\)(?:\s+(?:OF|IN)\s+([A-Za-z0-9-]+))?",
        target.strip(),
        re.IGNORECASE,
    )
    if not match:
        return f"{java_data_reference(target, variables)} {operator} {value};"
    field_name, subscript, qualifier = match.groups()
    collection_name = field_name + (f" OF {qualifier}" if qualifier else "")
    collection = java_data_reference(collection_name, variables)
    index = str(int(subscript) - 1) if subscript.isdigit() else f"{normalize_name(subscript)} - 1"
    if operator == "=":
        result = value
    else:
        symbol = {"+=": "+", "-=": "-", "*=": "*", "/=": "/"}.get(operator, "+")
        result = f"{collection}.get({index}) {symbol} ({value})"
    return f"{collection}.set({index}, {result});"


def translate_java_display_item(token: str, variables: dict[str, CobolVar]) -> str:
    base_match = re.match(r"[A-Za-z0-9-]+", token)
    variable = variables.get(base_match.group(0).upper()) if base_match else None
    value = translate_java_literal(token, variables)
    if variable is not None and variable.pic and "9" in variable.pic.upper():
        pic = variable.pic.upper()
        digits = pic_digit_count(pic)
        scale = pic_digit_count(pic.split("V", 1)[1]) if "V" in pic else 0
        return f"formatNumeric((double)({value}), {digits}, {scale})"
    return f"String.valueOf({value})"


def translate_java_statement(
    stmt: str,
    paragraphs: set[str],
    variables: dict[str, CobolVar],
) -> list[str]:
    text = stmt.strip().rstrip(".").strip()
    upper = text.upper()
    if not text:
        return []
    if upper == "STOP RUN":
        return ["System.exit(0);"]
    if upper in ("GOBACK", "EXIT PROGRAM"):
        return ["return;"]
    if upper in ("CONTINUE", "EXIT"):
        return [";"]
    if upper.startswith("DISPLAY "):
        args = split_cobol_items(text[len("DISPLAY "):])
        values = ", ".join(translate_java_display_item(arg, variables) for arg in args)
        return [f'System.out.println(String.join("", Arrays.asList({values})));']
    if upper.startswith("ACCEPT "):
        match = re.match(rf"ACCEPT\s+({DATA_REF_PATTERN})$", text, re.IGNORECASE)
        if match:
            target = match.group(1)
            variable = variables.get(re.match(r"[A-Za-z0-9-]+", target).group(0).upper())
            if variable and variable.pic and "9" in variable.pic.upper():
                parser = "Double.parseDouble" if "V" in variable.pic.upper() else "Integer.parseInt"
                return [java_assignment_statement(target, "=", f"{parser}(SCANNER.nextLine())", variables)]
            return [java_assignment_statement(target, "=", "SCANNER.nextLine()", variables)]
    move = re.match(rf"MOVE\s+(.+?)\s+TO\s+({DATA_REF_PATTERN})$", text, re.IGNORECASE)
    if move:
        source, target = move.groups()
        value = translate_java_literal(source, variables)
        base = re.match(r"[A-Za-z0-9-]+", target)
        variable = variables.get(base.group(0).upper()) if base else None
        target_expr = java_data_reference(target, variables)
        if variable and variable.pic and any(char in variable.pic.upper() for char in ("X", "A")):
            width = pic_character_count(variable.pic)
            all_literal = re.fullmatch(r"""ALL\s+(["'])(.*?)\1""", source.strip(), re.IGNORECASE)
            if all_literal:
                value = java_string_literal((all_literal.group(2) * width)[:width])
            return [java_assignment_statement(target, "=", f"fit(String.valueOf({value}), {width})", variables)]
        if variable and variable.pic and "9" in variable.pic.upper():
            digits = pic_digit_count(variable.pic)
            scale = pic_digit_count(variable.pic.upper().split("V", 1)[1]) if "V" in variable.pic.upper() else 0
            moved = f"moveNumeric((double)({value}), {digits}, {scale})"
            if "V" not in variable.pic.upper():
                moved = f"(int){moved}"
            return [java_assignment_statement(target, "=", moved, variables)]
        return [java_assignment_statement(target, "=", value, variables)]
    compute = re.match(rf"COMPUTE\s+({DATA_REF_PATTERN})\s*=\s*(.+)", text, re.IGNORECASE)
    if compute:
        return [java_assignment_statement(compute.group(1), "=", translate_java_expr(compute.group(2), variables), variables)]
    for verb, delim, op in (("ADD", "TO", "+="), ("SUBTRACT", "FROM", "-=")):
        match = re.match(rf"{verb}\s+(.+?)\s+{delim}\s+({DATA_REF_PATTERN})$", text, re.IGNORECASE)
        if match:
            operands = split_cobol_items(match.group(1))
            value = " + ".join(translate_java_literal(item, variables) for item in operands)
            return [java_assignment_statement(match.group(2), op, value, variables)]
    match = re.match(rf"MULTIPLY\s+(.+?)\s+BY\s+({DATA_REF_PATTERN})$", text, re.IGNORECASE)
    if match:
        return [java_assignment_statement(match.group(2), "*=", translate_java_literal(match.group(1), variables), variables)]
    match = re.match(rf"DIVIDE\s+(.+?)\s+INTO\s+({DATA_REF_PATTERN})$", text, re.IGNORECASE)
    if match:
        return [java_assignment_statement(match.group(2), "/=", translate_java_literal(match.group(1), variables), variables)]
    match = re.match(r"PERFORM\s+([A-Za-z0-9-]+)\s+(\d+)\s+TIMES", text, re.IGNORECASE)
    if match and match.group(1).upper() in paragraphs:
        return [f"for (int _i = 0; _i < {match.group(2)}; _i++) {{ {normalize_name(match.group(1))}(); }}"]
    match = re.match(r"PERFORM\s+([A-Za-z0-9-]+)\s+UNTIL\s+(.+)", text, re.IGNORECASE)
    if match and match.group(1).upper() in paragraphs:
        return [f"while (!({translate_java_condition(match.group(2), variables)})) {{ {normalize_name(match.group(1))}(); }}"]
    match = re.match(r"PERFORM\s+([A-Za-z0-9-]+)", text, re.IGNORECASE)
    if match and match.group(1).upper() in paragraphs:
        return [f"{normalize_name(match.group(1))}();"]
    return [f"// COBOL no traducido: {text}"]


def translate_java_nodes(
    nodes: list[Node],
    paragraphs: set[str],
    variables: dict[str, CobolVar],
    indent: int = 0,
) -> list[str]:
    out: list[str] = []
    pad = "    " * indent
    for node in nodes:
        if node.kind == "stmt":
            out.extend(pad + line for line in translate_java_statement(node.text, paragraphs, variables))
        elif node.kind == "if":
            match = RE_IF_OPEN.match(node.text)
            if not match:
                out.append(pad + "// IF malformado: " + node.text)
                continue
            out.append(pad + f"if ({translate_java_condition(match.group(1), variables)}) {{")
            body = translate_java_nodes(node.then_branch, paragraphs, variables, indent + 1)
            out.extend(body if any(line.strip() and not line.strip().startswith("//") for line in body) else body + ["    " * (indent + 1) + ";"])
            if node.else_branch:
                out.append(pad + "} else {")
                body = translate_java_nodes(node.else_branch, paragraphs, variables, indent + 1)
                out.extend(body if any(line.strip() and not line.strip().startswith("//") for line in body) else body + ["    " * (indent + 1) + ";"])
            out.append(pad + "}")
        elif node.kind in ("perform_inline", "perform_times_inline"):
            if node.kind == "perform_times_inline":
                match = re.match(r"PERFORM\s+(\d+)\s+TIMES", node.text, re.IGNORECASE)
                count = match.group(1) if match else "0"
                out.append(pad + f"for (int _i_{node.line} = 0; _i_{node.line} < {count}; _i_{node.line}++) {{")
            else:
                out.append(pad + "// PERFORM inline body")
                out.append(pad + "{")
            body = translate_java_nodes(node.body, paragraphs, variables, indent + 1)
            out.extend(body if any(line.strip() and not line.strip().startswith("//") for line in body) else body + ["    " * (indent + 1) + ";"])
            out.append(pad + "}")
        elif node.kind == "evaluate":
            subject = node.text[len("EVALUATE"):].strip()
            boolean_subject = subject.upper() in ("TRUE", "FALSE")
            temp = f"_cobolEvaluate{node.line}"
            if not boolean_subject:
                out.append(pad + f"Object {temp} = {translate_java_expr(subject, variables)};")
            emitted = 0
            for branch in node.body:
                if branch.kind != "when":
                    out.append(pad + "// Unsupported EVALUATE branch: " + branch.text)
                    continue
                choice = branch.text.strip()
                if choice.upper() == "OTHER":
                    prefix = "if (true) {" if emitted == 0 else "} else {"
                else:
                    if boolean_subject:
                        condition = translate_java_condition(choice, variables)
                        if subject.upper() == "FALSE":
                            condition = "!(" + condition + ")"
                        test = condition
                    elif re.search(r"\s+(?:THRU|THROUGH)\s+", choice, re.IGNORECASE):
                        low, high = re.split(r"\s+(?:THRU|THROUGH)\s+", choice, maxsplit=1, flags=re.IGNORECASE)
                        test = f"evalCompare({temp}, {translate_java_literal(low, variables)}) >= 0 && evalCompare({temp}, {translate_java_literal(high, variables)}) <= 0"
                    else:
                        test = f"evalEquals({temp}, {translate_java_literal(choice, variables)})"
                    prefix = ("if (" if emitted == 0 else "} else if (") + test + ") {"
                out.append(pad + prefix)
                body = translate_java_nodes(branch.then_branch, paragraphs, variables, indent + 1)
                out.extend(body if any(line.strip() and not line.strip().startswith("//") for line in body) else body + ["    " * (indent + 1) + ";"])
                emitted += 1
            if emitted:
                out.append(pad + "}")
            else:
                out.append(pad + "// EVALUATE without WHEN: " + node.text)
        elif node.kind == "malformed":
            out.append(pad + "// COBOL structure malformed: " + node.text)
    return out


def emit_java(prog: Program) -> str:
    variables = {variable.name.upper(): variable for variable in prog.variables}
    children_by_parent: dict[str, list[CobolVar]] = {}
    for variable in prog.variables:
        if variable.parent_name:
            children_by_parent.setdefault(variable.parent_name.upper(), []).append(variable)

    lines = [
        "import java.util.*;",
        "",
        "class Cobol2PyProgram {",
        "    private static final Scanner SCANNER = new Scanner(System.in);",
        *[f"    // COPYBOOK RESOLUTION WARNING: {warning}" for warning in prog.unresolved_copybooks],
    ]
    groups = [variable for variable in prog.variables if variable.is_group]
    for group in groups:
        lines.append(f"    private static class {java_group_class_name(group, variables)} {{")
        children = children_by_parent.get(group.name.upper(), [])
        if not children:
            lines.append("        // Empty COBOL group")
        for child in children:
            lines.append(
                f"        {java_type(child, variables)} {normalize_name(child.name)} = "
                f"{java_field_default(child, variables)};"
            )
        lines.append("    }")
    if groups:
        lines.append("")
    for variable in prog.variables:
        if variable.parent_name:
            continue
        lines.append(
            f"    private static {java_type(variable, variables)} {normalize_name(variable.name)} = "
            f"{java_field_default(variable, variables)};"
        )
    lines.extend([
        "",
        "    private static String fit(String value, int width) {",
        '        String text = value == null ? "" : value;',
        "        if (text.length() > width) return text.substring(0, width);",
        '        return String.format(Locale.ROOT, "%-" + width + "s", text);',
        "    }",
        "",
        "    private static String formatNumeric(double value, int digits, int scale) {",
        '        String text = String.format(Locale.ROOT, "%." + scale + "f", value).replace(".", "");',
        '        return text.length() < digits ? "0".repeat(digits - text.length()) + text : text;',
        "    }",
        "",
        "    private static double moveNumeric(double value, int digits, int scale) {",
        "        double factor = Math.pow(10, scale);",
        "        long magnitude = (long) (Math.abs(value) * factor);",
        "        long modulus = (long) Math.pow(10, digits);",
        "        double result = (magnitude % modulus) / factor;",
        "        return value < 0 ? -result : result;",
        "    }",
        "",
        "    private static boolean evalEquals(Object left, Object right) {",
        "        if (left instanceof Number && right instanceof Number) return ((Number) left).doubleValue() == ((Number) right).doubleValue();",
        "        return Objects.equals(left, right);",
        "    }",
        "",
        "    private static int evalCompare(Object left, Object right) {",
        "        if (left instanceof Number && right instanceof Number) return Double.compare(((Number) left).doubleValue(), ((Number) right).doubleValue());",
        "        return String.valueOf(left).compareTo(String.valueOf(right));",
        "    }",
        "",
    ])
    paragraph_names = set(prog.paragraphs)
    order = [name for name in prog.paragraph_order if name != "__MAIN__"]
    if "__MAIN__" in prog.paragraphs and prog.paragraphs["__MAIN__"]:
        order = ["__MAIN__"] + order
    for paragraph in order:
        method_name = "mainParagraph" if paragraph == "__MAIN__" else normalize_name(paragraph)
        lines.append(f"    private static void {method_name}() {{")
        body = translate_java_nodes(prog.paragraphs.get(paragraph, []), paragraph_names, variables, indent=2)
        if not body:
            body = ["        ;"]
        elif all(not line.strip() or line.strip().startswith("//") for line in body):
            body.append("        ;")
        lines.extend(body)
        lines.append("    }")
        lines.append("")
    lines.append("    public static void main(String[] args) {")
    if "__MAIN__" in prog.paragraphs and prog.paragraphs["__MAIN__"]:
        lines.append("        mainParagraph();")
    elif order:
        first = "mainParagraph" if order[0] == "__MAIN__" else normalize_name(order[0])
        lines.append(f"        {first}();")
    lines.append("    }")
    lines.append("}")
    return "\n".join(lines)


# ============================================================================
# 5. EMISIÓN
# ============================================================================

def emit_python(prog: Program) -> str:
    lines: list[str] = []
    lines.append("# -*- coding: utf-8 -*-")
    lines.append('"""')
    lines.append("Traducción automática de COBOL a Python.")
    lines.append(f"Programa original: {prog.program_id}")
    lines.append("Generado por cobol2py.py — v0.0.8")
    lines.append('"""')
    lines.append("")
    lines.append("class _CobolStopRun(Exception):")
    lines.append('    """Internal signal for COBOL STOP RUN; caught by the entry paragraph."""')
    lines.append("    pass")
    lines.append("")
    for warning in prog.unresolved_copybooks:
        lines.append(f"# COPYBOOK RESOLUTION WARNING: {warning}")
    if prog.unresolved_copybooks:
        lines.append("")

    if prog.variables:
        lines.append("# VARIABLES (WORKING-STORAGE)")
        children_by_parent: dict[str, list[CobolVar]] = {}
        for variable in prog.variables:
            if variable.parent_name:
                children_by_parent.setdefault(variable.parent_name.upper(), []).append(variable)

        def nested_default(variable: CobolVar) -> str:
            if not variable.is_group:
                return variable.py_default()
            children = children_by_parent.get(variable.name.upper(), [])
            if not children:
                return "{}"
            fields = ", ".join(
                f"{normalize_name(child.name)!r}: {nested_default(child)}"
                for child in children
            )
            return "{" + fields + "}"

        root_variables = [variable for variable in prog.variables if not variable.parent_name]
        for variable in root_variables:
            default = nested_default(variable)
            if variable.is_group:
                lines.append(
                    f"{normalize_name(variable.name)}: dict = {default}  "
                    f"# COBOL group: {variable.level:02d} {variable.name}"
                )
                continue
            comment = f"  # COBOL: {variable.level:02d} {variable.name} PIC {variable.pic}"
            if variable.occurs:
                comment += f" OCCURS {variable.occurs} TIMES"
            if variable.depending_on:
                comment += f" DEPENDING ON {variable.depending_on}"
            if variable.value:
                comment += f" VALUE {variable.value}"
            lines.append(f"{normalize_name(variable.name)}: {variable.py_type()} = {default}{comment}")
        lines.append("")

    para_names = set(prog.paragraphs.keys())
    variables_by_name = {variable.name.upper(): variable for variable in prog.variables}
    order = [p for p in prog.paragraph_order if p != "__MAIN__"]
    if "__MAIN__" in prog.paragraphs and prog.paragraphs["__MAIN__"]:
        order = ["__MAIN__"] + order
    entrypoint = (
        "__MAIN__"
        if "__MAIN__" in prog.paragraphs and prog.paragraphs["__MAIN__"]
        else (order[0] if order else None)
    )

    for para_name in order:
        nodes = prog.paragraphs.get(para_name, [])
        if not nodes:
            continue
        lines.append(f"# PÁRRAFO: {para_name}")
        if para_name == "__MAIN__":
            lines.append("def main():")
        else:
            lines.append(f"def {normalize_name(para_name)}():")
        # Working-Storage variables live outside paragraph functions in the
        # generated module. Declare them global so statements mutate shared
        # COBOL storage instead of creating Python locals.
        global_vars = [normalize_name(v.name) for v in prog.variables if not v.parent_name]
        if global_vars:
            lines.append("    global " + ", ".join(global_vars))
        body = translate_paragraph(nodes, para_names, variables_by_name)
        body = body if body else ["    pass"]
        if para_name == entrypoint:
            lines.append("    try:")
            lines.extend("    " + line if line else line for line in body)
            lines.append("    except _CobolStopRun:")
            lines.append("        return")
        else:
            lines.extend(body)
        lines.append("")

    lines.append('if __name__ == "__main__":')
    if "__MAIN__" in prog.paragraphs and prog.paragraphs["__MAIN__"]:
        lines.append("    main()")
    elif order:
        lines.append(f"    {normalize_name(order[0])}()")
    else:
        lines.append("    pass")

    return "\n".join(lines)


def collect_diagnostics(prog: Program) -> list[dict[str, object]]:
    """Return structured diagnostics for unsupported or malformed source constructs."""
    diagnostics: list[dict[str, object]] = []

    for message in prog.unresolved_copybooks:
        diagnostics.append({
            "code": "COPYBOOK_RESOLUTION",
            "severity": "warning",
            "line": None,
            "message": message,
        })

    for line_number, source_line in prog.raw_lines:
        if re.match(r"^\s*66\s+[A-Za-z0-9-]+\s+.*\bRENAMES\b", source_line, re.IGNORECASE):
            diagnostics.append({
                "code": "UNSUPPORTED_RENAMES",
                "severity": "warning",
                "line": line_number,
                "message": source_line.strip(),
            })
        if re.match(r"^\s*88\s+[A-Za-z0-9-]+\b", source_line, re.IGNORECASE):
            diagnostics.append({
                "code": "UNSUPPORTED_CONDITION_NAME_88",
                "severity": "warning",
                "line": line_number,
                "message": source_line.strip(),
            })
        if re.match(
            r"^\s*\d{1,2}\s+[A-Za-z0-9-]+\s+.*\bREDEFINES\b",
            source_line,
            re.IGNORECASE,
        ):
            diagnostics.append({
                "code": "UNSUPPORTED_STORAGE_OVERLAY",
                "severity": "warning",
                "line": line_number,
                "message": source_line.strip(),
            })

    for variable in prog.variables:
        if variable.is_group and variable.is_array:
            diagnostics.append({
                "code": "OCCURS_GROUP_UNSUPPORTED",
                "severity": "warning",
                "line": next(
                    (
                        line_number for line_number, source_line in prog.raw_lines
                        if re.search(rf"^\s*0*{variable.level}\s+{re.escape(variable.name)}\b", source_line, re.IGNORECASE)
                    ),
                    None,
                ),
                "message": (
                    f"{variable.name} is a group with OCCURS; repeated nested group storage "
                    "is not represented as a list of records"
                ),
            })
        if variable.depending_on:
            diagnostics.append({
                "code": "OCCURS_DEPENDING_ON_UNSUPPORTED",
                "severity": "warning",
                "line": next(
                    (
                        line_number for line_number, source_line in prog.raw_lines
                        if re.search(rf"^\s*0*{variable.level}\s+{re.escape(variable.name)}\b", source_line, re.IGNORECASE)
                    ),
                    None,
                ),
                "message": (
                    f"{variable.name} OCCURS DEPENDING ON {variable.depending_on}: "
                    "dynamic active length is not implemented; storage uses the maximum occurrence count"
                ),
            })
        if variable.pic and any(code in variable.pic.upper() for code in ("S", "V", "P")):
            declaration_line = next(
                (
                    line_number for line_number, source_line in prog.raw_lines
                    if re.search(rf"\b{re.escape(variable.name)}\b", source_line, re.IGNORECASE)
                ),
                None,
            )
            diagnostics.append({
                "code": "PARTIAL_NUMERIC_PIC_SEMANTICS",
                "severity": "warning",
                "line": declaration_line,
                "message": f"{variable.name} PIC {variable.pic}: sign, scale, or scaling semantics are not generally guaranteed",
            })

    def visit(nodes: list[Node], paragraph: str) -> None:
        for node in nodes:
            if node.kind == "malformed":
                diagnostics.append({
                    "code": "MALFORMED_CONTROL_FLOW",
                    "severity": "error",
                    "line": node.line,
                    "message": node.text,
                    "paragraph": paragraph,
                })
            elif node.kind == "stmt":
                if re.match(
                    r"^(?:ADD|SUBTRACT|MULTIPLY|DIVIDE|COMPUTE)\b",
                    node.text.strip(),
                    re.IGNORECASE,
                ):
                    diagnostics.append({
                        "code": "ARITHMETIC_SIZE_ERROR_UNSUPPORTED",
                        "severity": "warning",
                        "line": node.line,
                        "message": (
                            f"{node.text}: receiving PIC overflow and ON SIZE ERROR "
                            "semantics are not fully implemented"
                        ),
                        "paragraph": paragraph,
                    })
                translated = translate_statement(
                    node.text,
                    set(prog.paragraphs),
                    {v.name.upper(): v for v in prog.variables},
                ) or []
                if any(
                    line.lstrip().startswith(("# COBOL no traducido:", "# PERFORM no traducido:"))
                    for line in translated
                ):
                    diagnostics.append({
                        "code": "UNSUPPORTED_STATEMENT",
                        "severity": "warning",
                        "line": node.line,
                        "message": node.text,
                        "paragraph": paragraph,
                    })
            elif node.kind == "if":
                match = RE_IF_OPEN.match(node.text)
                condition = match.group(1) if match else ""
                comparison = re.search(
                    r"""([A-Za-z][A-Za-z0-9-]*(?:\([A-Za-z0-9_-]+\))?)\s*(?:<=|>=|<|>)\s*["']""",
                    condition,
                    re.IGNORECASE,
                )
                if comparison:
                    base = re.match(r"[A-Za-z][A-Za-z0-9-]*", comparison.group(1))
                    variable = (
                        next(
                            (item for item in prog.variables if item.name.upper() == base.group(0).upper()),
                            None,
                        )
                        if base else None
                    )
                    if variable and variable.pic and any(char in variable.pic.upper() for char in ("X", "A")):
                        diagnostics.append({
                            "code": "ALPHANUMERIC_ORDER_COMPARISON_UNSUPPORTED",
                            "severity": "warning",
                            "line": node.line,
                            "message": node.text,
                            "paragraph": paragraph,
                        })
                field_comparison = re.search(
                    r"\b([A-Za-z][A-Za-z0-9-]*)\b\s*(?:=|==|!=|<>|<=|>=|<|>)\s*([A-Za-z][A-Za-z0-9-]*)\b",
                    condition,
                    re.IGNORECASE,
                )
                if field_comparison:
                    left_var = next(
                        (item for item in prog.variables if item.name.upper() == field_comparison.group(1).upper()),
                        None,
                    )
                    right_var = next(
                        (item for item in prog.variables if item.name.upper() == field_comparison.group(2).upper()),
                        None,
                    )
                    if (
                        left_var and right_var
                        and left_var.pic and right_var.pic
                        and any(char in left_var.pic.upper() for char in ("X", "A"))
                        and any(char in right_var.pic.upper() for char in ("X", "A"))
                    ):
                        diagnostics.append({
                            "code": "ALPHANUMERIC_FIELD_COMPARISON_UNSUPPORTED",
                            "severity": "warning",
                            "line": node.line,
                            "message": node.text,
                            "paragraph": paragraph,
                        })
            elif node.kind == "evaluate":
                if not any(child.kind == "when" for child in node.body):
                    diagnostics.append({
                        "code": "EVALUATE_WITHOUT_WHEN",
                        "severity": "warning",
                        "line": node.line,
                        "message": node.text,
                        "paragraph": paragraph,
                    })
                subject = node.text[len("EVALUATE"):].strip()
                also_branch = next(
                    (
                        child.text for child in node.body
                        if child.kind == "when" and re.search(r"\bALSO\b", child.text, re.IGNORECASE)
                    ),
                    None,
                )
                if re.search(r"\bALSO\b", subject, re.IGNORECASE) or also_branch:
                    diagnostics.append({
                        "code": "UNSUPPORTED_EVALUATE_ALSO",
                        "severity": "warning",
                        "line": node.line,
                        "message": also_branch or node.text,
                        "paragraph": paragraph,
                    })

            visit(node.then_branch, paragraph)
            visit(node.else_branch, paragraph)
            visit(node.body, paragraph)

    for paragraph, nodes in prog.paragraphs.items():
        visit(nodes, paragraph)
    return diagnostics


# ============================================================================
# 6. CLI
# ============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(prog="cobol2py", description="Traductor COBOL → Python/Java v0.1.0")
    ap.add_argument("input", type=Path, help="Archivo .cbl o .cob")
    ap.add_argument("--out", type=Path, default=None, help="Archivo de salida")
    ap.add_argument("--format", dest="source_format", choices=("auto", "fixed", "free"), default="auto", help="Formato fuente COBOL (por defecto: auto)")
    ap.add_argument("--copybook-path", action="append", type=Path, default=[], help="Directorio de copybooks (se puede repetir)")
    ap.add_argument("--lang", choices=("python", "java"), default="python", help="Lenguaje de salida (por defecto: python)")
    ap.add_argument(
        "--strict", action="store_true",
        help="Falla si hay construcciones no soportadas, copybooks sin resolver o semántica de datos/aritmética parcialmente cubierta",
    )
    ap.add_argument(
        "--diagnostics-json", action="store_true",
        help="Emite diagnósticos estructurados JSON por stderr",
    )
    args = ap.parse_args()

    if not args.input.exists():
        print(f"No existe: {args.input}", file=sys.stderr)
        return 1

    source = args.input.read_text(encoding="utf-8", errors="replace")
    prog = parse_cobol(
        source,
        source_format=args.source_format,
        copybook_paths=args.copybook_path,
        source_path=args.input,
    )
    diagnostics = collect_diagnostics(prog)
    if args.diagnostics_json:
        print(json.dumps(diagnostics, ensure_ascii=False), file=sys.stderr)
    elif diagnostics and args.strict:
        for diagnostic in diagnostics:
            print(
                f"{diagnostic['severity'].upper()} {diagnostic['code']}"
                f" line={diagnostic['line']}: {diagnostic['message']}",
                file=sys.stderr,
            )
    if args.strict and diagnostics:
        return 2

    output = emit_java(prog) if args.lang == "java" else emit_python(prog)

    if args.out:
        args.out.write_text(output, encoding="utf-8")
        print(f"Escrito: {args.out}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
