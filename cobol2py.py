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
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ============================================================================
# 1. PREPROCESADO
# ============================================================================

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
            line = raw.split("*>")[0].rstrip()
            if line.strip():
                out.append((i, line))
            continue
        line = raw.rstrip("\n").ljust(80)
        indicator = line[6] if len(line) > 6 else " "
        if indicator in ("*", "/", "D", "d"):
            continue
        code = line[7:72].rstrip()
        code = code.split("*>")[0].rstrip()
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
    r"""VALUE\s+(?:IS\s+)?((?:ALL\s+)?(?:"[^"]*"|'[^']*'|[+-]?\d+(?:\.\d+)?|[A-Za-z][A-Za-z0-9-]*))""",
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
    tokens = text.split()
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
            upper.startswith("PERFORM")
            and not normalized.endswith(".")
            and "TIMES" not in upper
            and "UNTIL" not in upper
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
        if m:
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
            code_line = line.split("*>", 1)[0].rstrip()
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

def normalize_name(name: str) -> str:
    name = name.replace("-", "_").lower()

    # COBOL table subscripts are 1-based; Python lists are 0-based.
    # Translate a simple literal or data-name subscript accordingly.
    def normalize_subscript(match: re.Match[str]) -> str:
        subscript = match.group(1)
        if subscript.isdigit():
            return f"[{int(subscript) - 1}]"
        return f"[{subscript.replace('-', '_').lower()} - 1]"

    return re.sub(r"\(([A-Za-z0-9_-]+)\)", normalize_subscript, name)

def normalize_data_reference(
    name: str,
    variables: Optional[dict[str, CobolVar]] = None,
) -> str:
    """Map a COBOL data-name (including OF/IN qualification) into nested dicts."""
    text = name.strip()
    match = re.fullmatch(
        r"([A-Za-z0-9-]+)(?:\\(([A-Za-z0-9_-]+)\\))?(?:\\s+(?:OF|IN)\\s+([A-Za-z0-9-]+))?",
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


def translate_literal(token: str) -> str:
    t = token.strip()
    if not t:
        return '""'
    all_literal = re.fullmatch(r"""ALL\s+(["'])(.*?)\1""", t, re.IGNORECASE)
    if all_literal:
        return repr(all_literal.group(2))
    if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
        return '"' + t[1:-1] + '"'
    if re.match(r"^[+-]?\d+$", t):
        return t
    if re.match(r"^[+-]?\d+\.\d+$", t):
        return t
    if t.upper() in ("SPACES", "SPACE"):
        return '""'
    if t.upper() in ("ZEROS", "ZERO", "ZEROES", "ZEROES"):
        return "0"
    if t.upper() in ("LOW-VALUE", "LOW-VALUES"):
        return repr("\x00")
    if t.upper() in ("HIGH-VALUE", "HIGH-VALUES"):
        return repr("\xff")
    if t.upper() in ("QUOTE", "QUOTES"):
        return repr('"')
    return normalize_name(t)


def translate_expr(expr: str) -> str:
    # Match COBOL identifiers before arithmetic operators so hyphenated
    # names (WS-NUM) become Python identifiers (ws_num), not subtraction.
    # COBOL arithmetic using '-' should be separated from identifiers by
    # whitespace when the token could otherwise be a hyphenated data-name.
    token_pattern = r"""("[^"]*"|'[^']*'|[A-Za-z][A-Za-z0-9-]*|\d+(?:\.\d+)?|<=|>=|<>|==|!=|[()+*/=<>&-]|\s+|.)"""
    # Normalize simple COBOL table references before tokenizing identifiers.
    # COBOL subscripts are 1-based; normalize_name converts them to Python indexes.
    expr = re.sub(
        r"\b([A-Za-z][A-Za-z0-9-]*)\(([A-Za-z0-9_-]+)\)",
        lambda match: normalize_name(f"{match.group(1)}({match.group(2)})"),
        expr,
    )
    token_pattern = token_pattern.replace("[A-Za-z0-9-]*", "[A-Za-z0-9_-]*")
    tokens = re.findall(token_pattern, expr)
    out = []
    for tok in tokens:
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", tok):
            out.append(normalize_name(tok))
        else:
            out.append(tok)
    return "".join(out).strip()

# Patch 1: normalización de operadores
def translate_condition(cond: str, variables: Optional[dict[str, CobolVar]] = None) -> str:
    c = cond.strip()
    c = re.sub(r"\bAND\b", "and", c, flags=re.IGNORECASE)
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
    c = re.sub(r"(?<![<>=])=(?!=)", "==", c)
    c = c.replace("<>", "!=")

    translated = translate_expr(c)
    if not variables:
        return translated

    # COBOL pads the shorter operand with spaces for alphanumeric comparisons.
    # Match a translated data-name (including a table element) against a literal.
    def pad_literal(match: re.Match[str]) -> str:
        left, operator, quote, literal = match.groups()
        base = re.match(r"[a-z_][a-z0-9_]*", left)
        if base is None:
            return match.group(0)
        variable = next(
            (item for item in variables.values()
             if normalize_name(item.name) == base.group(0)),
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
        r"""([a-z_][a-z0-9_]*(?:\[[^\]]+\])?)\s*(==|!=)\s*(["'])(.*?)\3""",
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
    variable = variables.get(token.upper())
    if variable is not None and variable.pic:
        pic = variable.pic.upper()
        if "9" in pic:
            digits = pic_digit_count(pic)
            scale = pic_digit_count(pic.split("V", 1)[1]) if "V" in pic else 0
            name = normalize_name(token)
            return (
                f'f"{{float({name}):.{scale}f}}".replace(".", "")'
                f".zfill({digits})"
            )
    return f"str({translate_literal(token)})"

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
    value = translate_literal(source)
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


COBOL_TOKEN_RE = re.compile(r'"[^"]*"|\'[^\']*\'|,?\s*|(?:\S+)')


def split_cobol_items(s: str) -> list[str]:
    tokens = []
    for m in COBOL_TOKEN_RE.finditer(s):
        tok = m.group(0).strip().strip(",")
        if tok:
            tokens.append(tok)
    return tokens


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
        return ["return"]
    if upper.startswith("EXIT PROGRAM") or upper == "GOBACK":
        return ["return"]

    m = re.match(r"DISPLAY\s+(.+)", s, re.IGNORECASE)
    if m:
        args = split_cobol_items(m.group(1))
        # COBOL DISPLAY concatenates operands. Numeric DISPLAY items also
        # retain the zero-filled width specified by their PIC clause.
        items = ", ".join(
            translate_display_item(a, variables or {}) for a in args
        )
        return [f'print("".join([{items}]))']

    m = re.match(r"ACCEPT\s+([A-Za-z0-9\-\(\)]+)", s, re.IGNORECASE)
    if m:
        return [f"{normalize_name(m.group(1))} = input()"]

    m = re.match(r"MOVE\s+(.+?)\s+TO\s+([A-Za-z0-9\-\(\)]+)", s, re.IGNORECASE)
    if m:
        target = m.group(2)
        value = translate_move_value(m.group(1), target, variables or {})
        return [f"{normalize_name(target)} = {value}"]

    m = re.match(r"COMPUTE\s+([A-Za-z0-9\-\(\)]+)\s*=\s*(.+)", s, re.IGNORECASE)
    if m:
        return [f"{normalize_name(m.group(1))} = {translate_expr(m.group(2))}"]

    # Patch 4: ADD con múltiples operandos
    m = re.match(r"ADD\s+(.+?)\s+TO\s+([A-Za-z0-9\-\(\)]+)", s, re.IGNORECASE)
    if m:
        operands = split_cobol_items(m.group(1))
        sum_expr = " + ".join(translate_literal(o) for o in operands)
        return [f"{normalize_name(m.group(2))} += {sum_expr}"]

    m = re.match(r"SUBTRACT\s+(.+?)\s+FROM\s+([A-Za-z0-9\-\(\)]+)", s, re.IGNORECASE)
    if m:
        operands = split_cobol_items(m.group(1))
        sum_expr = " + ".join(translate_literal(o) for o in operands)
        return [f"{normalize_name(m.group(2))} -= {sum_expr}"]

    m = re.match(r"MULTIPLY\s+(.+?)\s+BY\s+([A-Za-z0-9\-\(\)]+)", s, re.IGNORECASE)
    if m:
        return [f"{normalize_name(m.group(2))} *= {translate_literal(m.group(1))}"]

    m = re.match(r"DIVIDE\s+(.+?)\s+INTO\s+([A-Za-z0-9\-\(\)]+)", s, re.IGNORECASE)
    if m:
        return [f"{normalize_name(m.group(2))} /= {translate_literal(m.group(1))}"]

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


# ============================================================================
# 5. EMISIÓN
# ============================================================================

def emit_python(prog: Program) -> str:
    lines: list[str] = []
    lines.append("# -*- coding: utf-8 -*-")
    lines.append('"""')
    lines.append("Traducción automática de COBOL a Python.")
    lines.append(f"Programa original: {prog.program_id}")
    lines.append("Generado por cobol2py.py — v0.0.6")
    lines.append('"""')
    lines.append("")
    for warning in prog.unresolved_copybooks:
        lines.append(f"# COPYBOOK RESOLUTION WARNING: {warning}")
    if prog.unresolved_copybooks:
        lines.append("")

    if prog.variables:
        lines.append("# VARIABLES (WORKING-STORAGE)")
        for v in prog.variables:
            if v.is_group:
                lines.append(f"# Grupo nivel {v.level:02d}: {v.name}")
            else:
                t = v.py_type()
                default = v.py_default()
                comment = f"  # COBOL: {v.level:02d} {v.name} PIC {v.pic}"
                if v.occurs:
                    comment += f" OCCURS {v.occurs} TIMES"
                if v.depending_on:
                    comment += f" DEPENDING ON {v.depending_on}"
                if v.value:
                    comment += f" VALUE {v.value}"
                lines.append(f"{normalize_name(v.name)}: {t} = {default}{comment}")
        lines.append("")

    para_names = set(prog.paragraphs.keys())
    variables_by_name = {
        variable.name.upper(): variable
        for variable in prog.variables
        if not variable.is_group
    }
    order = [p for p in prog.paragraph_order if p != "__MAIN__"]
    if "__MAIN__" in prog.paragraphs and prog.paragraphs["__MAIN__"]:
        order = ["__MAIN__"] + order

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
        global_vars = [normalize_name(v.name) for v in prog.variables if not v.is_group]
        if global_vars:
            lines.append("    global " + ", ".join(global_vars))
        body = translate_paragraph(nodes, para_names, variables_by_name)
        lines.extend(body if body else ["    pass"])
        lines.append("")

    lines.append('if __name__ == "__main__":')
    if "__MAIN__" in prog.paragraphs and prog.paragraphs["__MAIN__"]:
        lines.append("    main()")
    elif order:
        lines.append(f"    {normalize_name(order[0])}()")
    else:
        lines.append("    pass")

    return "\n".join(lines)


# ============================================================================
# 6. CLI
# ============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(prog="cobol2py", description="Traductor COBOL → Python v0.0.6")
    ap.add_argument("input", type=Path, help="Archivo .cbl o .cob")
    ap.add_argument("--out", type=Path, default=None, help="Archivo de salida")
    ap.add_argument("--format", dest="source_format", choices=("auto", "fixed", "free"), default="auto", help="Formato fuente COBOL (por defecto: auto)")
    ap.add_argument("--copybook-path", action="append", type=Path, default=[], help="Directorio de copybooks (se puede repetir)")
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
    output = emit_python(prog)

    if args.out:
        args.out.write_text(output, encoding="utf-8")
        print(f"Escrito: {args.out}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
