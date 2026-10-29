#!/usr/bin/env python3
"""Experimental COBOL -> C/Rust backend prototypes.

This deliberately supports a small, explicit subset. Unsupported constructs
fail closed rather than emitting code that appears semantically equivalent.
The parser and COBOL data model are shared with cobol2py.py.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import cobol2py as core


class UnsupportedConstruct(ValueError):
    """Raised when a source program exceeds this prototype's supported subset."""


def _literal(token: str, variables: dict[str, core.CobolVar], lang: str) -> str:
    text = token.strip()
    quoted = core.decode_cobol_quoted_literal(text)
    if quoted is not None:
        if lang == "c":
            escaped = quoted.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            return '"' + escaped + '"'
        return json.dumps(quoted, ensure_ascii=False)
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text):
        return text
    if text.upper() in ("ZERO", "ZEROS", "ZEROES"):
        return "0"
    if text.upper() in ("SPACE", "SPACES"):
        return '" "' if lang == "c" else '" "'
    name = re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", text)
    if name and name.group(0).upper() in variables:
        return core.normalize_name(name.group(0))
    raise UnsupportedConstruct(f"literal/identifier not supported: {text}")


def _display_expr(token: str, variables: dict[str, core.CobolVar], lang: str) -> tuple[str, str]:
    name_match = re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", token.strip())
    if name_match and name_match.group(0).upper() in variables:
        var = variables[name_match.group(0).upper()]
        ident = core.normalize_name(var.name)
        if var.pic and any(c in var.pic.upper() for c in "XA"):
            return ("{}", ident) if lang == "rust" else ("%s", ident)
        width = core.pic_digit_count(var.pic or "")
        return (f"{{:0{width}}}", ident) if lang == "rust" else (f"%0{width}lld", ident)
    literal = _literal(token, variables, lang)
    if lang == "rust":
        return ("{}", literal)
    if literal.startswith('"'):
        return ("%s", literal)
    if re.fullmatch(r"[+-]?\d+", token.strip()):
        return ("%lld", f"(long long)({literal})")
    return ("%g", f"(double)({literal})")


def _translate_statement(statement: str, variables: dict[str, core.CobolVar], lang: str) -> list[str]:
    s = statement.strip().rstrip(".").strip()
    upper = s.upper()
    if upper in ("STOP RUN", "GOBACK", "EXIT PROGRAM"):
        return ["return 0;" if lang == "c" else "return;"]
    match = re.fullmatch(r"DISPLAY\s+(.+?)(?:\s+WITH\s+NO\s+ADVANCING)?", s, re.I)
    if match:
        no_newline = bool(re.search(r"\s+WITH\s+NO\s+ADVANCING\s*$", s, re.I))
        operands = core.split_cobol_items(re.sub(r"\s+WITH\s+NO\s+ADVANCING\s*$", "", match.group(1), flags=re.I))
        if not operands:
            return []
        rendered = [_display_expr(item, variables, lang) for item in operands]
        if lang == "c":
            fmt = "".join(item[0] for item in rendered) + ("" if no_newline else "\\n")
            args = ", ".join(item[1] for item in rendered)
            return [f'printf("{fmt}", {args});']
        fmt = "".join(item[0] for item in rendered) + ("" if no_newline else "\\n")
        args = ", ".join(item[1] for item in rendered)
        return [f'print!("{fmt}", {args});']
    match = re.fullmatch(r"MOVE\s+(.+?)\s+TO\s+([A-Za-z][A-Za-z0-9-]*)", s, re.I)
    if match:
        source, target = match.groups()
        var = variables.get(target.upper())
        if var is None or var.is_group or var.is_array:
            raise UnsupportedConstruct(f"MOVE target outside prototype subset: {target}")
        value = _literal(source, variables, lang)
        ident = core.normalize_name(target)
        if var.pic and any(c in var.pic.upper() for c in "XA"):
            width = core.pic_character_count(var.pic)
            if lang == "c":
                return [f'snprintf({ident}, sizeof({ident}), "%-{width}.{width}s", {value});']
            return [f'{ident} = format!("{{:<{width}}}", {value});', f'{ident}.truncate({width});']
        return [f"{ident} = {value};" if lang == "c" else f"{ident} = {value};"]
    match = re.fullmatch(r"ADD\s+(.+?)\s+TO\s+([A-Za-z][A-Za-z0-9-]*)", s, re.I)
    if match:
        source, target = match.groups()
        if target.upper() not in variables:
            raise UnsupportedConstruct(f"unknown ADD target: {target}")
        return [f"{core.normalize_name(target)} += {_literal(source, variables, lang)};"]
    if upper in ("CONTINUE", "EXIT"):
        return [";"] if lang == "c" else ["()"]
    raise UnsupportedConstruct(f"statement not supported by experimental {lang} backend: {s}")


def emit_native(program: core.Program, lang: str) -> str:
    if lang not in ("c", "rust"):
        raise ValueError("lang must be c or rust")
    variables = {var.name.upper(): var for var in program.variables}
    for var in program.variables:
        if var.parent_name or var.is_group or var.is_array or var.redefines:
            raise UnsupportedConstruct(
                f"data layout outside prototype subset: {var.name} (groups, OCCURS and REDEFINES need the shared storage-layout backend)"
            )
    statements: list[str] = []
    for paragraph in program.paragraph_order:
        for node in program.paragraphs.get(paragraph, []):
            if node.kind != "stmt":
                raise UnsupportedConstruct(f"control-flow node '{node.kind}' is not yet supported by the experimental {lang} backend")
            statements.extend(_translate_statement(node.text, variables, lang))
    lines: list[str] = [
        f"/* Experimental COBOL -> {lang.upper()} translation for {program.program_id}. */"
    ]
    if lang == "c":
        lines += ["#include <stdio.h>", "#include <stdlib.h>", "#include <string.h>", "", "int main(void) {"]
        for var in program.variables:
            ident = core.normalize_name(var.name)
            pic = (var.pic or "").upper()
            if any(c in pic for c in "XA"):
                width = max(1, core.pic_character_count(pic))
                initial = core.decode_cobol_quoted_literal(var.value or "") or ""
                initial = initial[:width].ljust(width)
                escaped = initial.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'    char {ident}[{width + 1}] = "{escaped}";')
            elif "9" in pic:
                initial = int(var.value) if var.value and re.fullmatch(r"[+-]?\d+", var.value.strip()) else 0
                lines.append(f"    long long {ident} = {initial};")
            else:
                raise UnsupportedConstruct(f"unsupported PIC for {var.name}: {var.pic}")
        lines += ["    " + line for line in statements]
        if not any(line.strip() == "return 0;" for line in statements):
            lines.append("    return 0;")
        lines += ["}"]
    else:
        lines += ["use std::io::{self, Write};", "", "fn main() {"]
        for var in program.variables:
            ident = core.normalize_name(var.name)
            pic = (var.pic or "").upper()
            if any(c in pic for c in "XA"):
                width = max(1, core.pic_character_count(pic))
                initial = core.decode_cobol_quoted_literal(var.value or "") or ""
                initial = initial[:width].ljust(width)
                lines.append(f"    let mut {ident}: String = {json.dumps(initial, ensure_ascii=False)}.to_string();")
            elif "9" in pic:
                initial = int(var.value) if var.value and re.fullmatch(r"[+-]?\d+", var.value.strip()) else 0
                lines.append(f"    let mut {ident}: i64 = {initial};")
            else:
                raise UnsupportedConstruct(f"unsupported PIC for {var.name}: {var.pic}")
        lines += ["    " + line for line in statements]
        lines += ["    let _ = io::stdout().flush();", "}"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--lang", choices=("c", "rust"), required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--source-format", choices=("auto", "fixed", "free"), default="auto")
    args = parser.parse_args(argv)
    try:
        source = args.source.read_text(encoding="utf-8", errors="replace")
        program = core.parse_cobol(source, source_format=args.source_format)
        output = emit_native(program, args.lang)
    except (OSError, ValueError, UnsupportedConstruct) as error:
        print(f"cobol2native: {error}", file=sys.stderr)
        return 2
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
