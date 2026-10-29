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



def _resolve_native_variable(token: str, variables: dict[str, core.CobolVar]) -> core.CobolVar | None:
    """Resolve a scalar name, optionally qualified by containing COBOL groups."""
    parts = re.split(r"\s+(?:OF|IN)\s+", token.strip(), flags=re.IGNORECASE)
    if not parts or not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", parts[0]):
        return None
    variable = variables.get(parts[0].upper())
    if variable is None:
        return None
    parent_name = variable.parent_name
    for qualifier in parts[1:]:
        current = variables.get(parent_name.upper()) if parent_name else None
        while current and current.name.upper() != qualifier.upper():
            current = variables.get(current.parent_name.upper()) if current.parent_name else None
        if current is None:
            return None
        parent_name = current.parent_name
    return variable


def _native_ident(variable: core.CobolVar, variables: dict[str, core.CobolVar]) -> str:
    names = [variable.name]
    parent_name = variable.parent_name
    seen: set[str] = set()
    while parent_name and parent_name.upper() not in seen:
        seen.add(parent_name.upper())
        parent = variables.get(parent_name.upper())
        if parent is None:
            break
        names.append(parent.name)
        parent_name = parent.parent_name
    return "_".join(core.normalize_name(name) for name in reversed(names))


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
    variable = _resolve_native_variable(text, variables)
    if variable is not None:
        return _native_ident(variable, variables)
    raise UnsupportedConstruct(f"literal/identifier not supported: {text}")


def _display_expr(token: str, variables: dict[str, core.CobolVar], lang: str) -> tuple[str, str]:
    var = _resolve_native_variable(token, variables)
    if var is not None:
        ident = _native_ident(var, variables)
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
    match = re.fullmatch(r"MOVE\s+(.+?)\s+TO\s+([A-Za-z][A-Za-z0-9-]*(?:\s+(?:OF|IN)\s+[A-Za-z][A-Za-z0-9-]*)*)", s, re.I)
    if match:
        source, target = match.groups()
        var = _resolve_native_variable(target, variables)
        if var is None or var.is_group or var.is_array:
            raise UnsupportedConstruct(f"MOVE target outside prototype subset: {target}")
        value = _literal(source, variables, lang)
        ident = _native_ident(var, variables)
        if var.pic and any(c in var.pic.upper() for c in "XA"):
            width = core.pic_character_count(var.pic)
            if lang == "c":
                return [f'snprintf({ident}, sizeof({ident}), "%-{width}.{width}s", {value});']
            return [f'{ident} = format!("{{:<{width}}}", {value});', f'{ident}.truncate({width});']
        return [f"{ident} = {value};" if lang == "c" else f"{ident} = {value};"]
    match = re.fullmatch(r"ADD\s+(.+?)\s+TO\s+([A-Za-z][A-Za-z0-9-]*(?:\s+(?:OF|IN)\s+[A-Za-z][A-Za-z0-9-]*)*)", s, re.I)
    if match:
        source, target = match.groups()
        variable = _resolve_native_variable(target, variables)
        if variable is None or variable.is_group or variable.is_array:
            raise UnsupportedConstruct(f"unknown or unsupported ADD target: {target}")
        return [f"{_native_ident(variable, variables)} += {_literal(source, variables, lang)};"]
    if upper in ("CONTINUE", "EXIT"):
        return [";"] if lang == "c" else ["()"]
    raise UnsupportedConstruct(f"statement not supported by experimental {lang} backend: {s}")



def _native_condition(condition: str, variables: dict[str, core.CobolVar], lang: str) -> str:
    """Translate a conservative subset of scalar COBOL conditions."""
    text = condition.strip().rstrip(".").strip()
    for word, symbol in ((" AND ", " && "), (" OR ", " || ")):
        if word in text.upper():
            parts = re.split(re.escape(word), text, maxsplit=1, flags=re.IGNORECASE)
            return "(" + _native_condition(parts[0], variables, lang) + symbol + _native_condition(parts[1], variables, lang) + ")"
    if text.upper().startswith("NOT "):
        return "!(" + _native_condition(text[4:], variables, lang) + ")"
    match = re.fullmatch(r"(.+?)\s+(?:(?:IS)\s+)?(?:(NOT)\s+)?(EQUAL(?:\s+TO)?|GREATER(?:\s+THAN)?|LESS(?:\s+THAN)?|<>|!=|<=|>=|=|<|>)\s+(.+)", text, re.I)
    if not match:
        raise UnsupportedConstruct("IF condition outside native subset: " + text)
    left_text, negated, op_text, right_text = match.groups()
    left = _literal(left_text, variables, lang)
    right = _literal(right_text, variables, lang)
    op_upper = re.sub(r"\s+", " ", op_text.upper())
    if op_upper.startswith("EQUAL"):
        op = "=="
    elif op_upper.startswith("GREATER"):
        op = ">"
    elif op_upper.startswith("LESS"):
        op = "<"
    else:
        op = {"=": "==", "<>": "!=", "!=": "!=", "<": "<", ">": ">", "<=": "<=", ">=": ">="}[op_text]
    if negated:
        op = {"==": "!=", "!=": "==", "<": ">=", ">": "<=", "<=": ">", ">=": "<"}.get(op, op)
    if lang == "c":
        def is_text(token: str) -> bool:
            name = re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", token.strip())
            if name and name.group(0).upper() in variables:
                pic = (variables[name.group(0).upper()].pic or "").upper()
                return "X" in pic or "A" in pic
            return core.decode_cobol_quoted_literal(token.strip()) is not None or token.strip().upper() in ("SPACE", "SPACES")
        if is_text(left_text) or is_text(right_text):
            return f"(strcmp({left}, {right}) {op} 0)"
    return f"({left} {op} {right})"


def _emit_nodes(nodes: list[core.Node], variables: dict[str, core.CobolVar], lang: str, indent: int = 1) -> list[str]:
    output: list[str] = []
    pad = "    " * indent
    for node in nodes:
        if node.kind == "stmt":
            output.extend(pad + line for line in _translate_statement(node.text, variables, lang))
        elif node.kind == "perform_until_inline":
            match = re.match(
                r"^PERFORM(?:\s+WITH\s+TEST\s+(BEFORE|AFTER))?\s+UNTIL\s+(.+)$",
                node.text,
                re.IGNORECASE,
            )
            if not match:
                raise UnsupportedConstruct("malformed inline PERFORM UNTIL: " + node.text)
            test_mode = match.group(1).upper() if match.group(1) else "BEFORE"
            condition = _native_condition(match.group(2), variables, lang)
            if test_mode == "AFTER":
                output.append(pad + ("while (1) {" if lang == "c" else "loop {"))
                body = _emit_nodes(node.body, variables, lang, indent + 1)
                output.extend(body or ["    " * (indent + 1) + (";" if lang == "c" else "() ;")])
                output.append("    " * (indent + 1) + f"if ({condition}) {{ break; }}" if lang == "c" else "    " * (indent + 1) + f"if {condition} {{ break; }}")
            else:
                output.append(pad + (f"while (!{condition}) {{" if lang == "c" else f"while !{condition} {{"))
                body = _emit_nodes(node.body, variables, lang, indent + 1)
                output.extend(body or ["    " * (indent + 1) + (";" if lang == "c" else "() ;")])
            output.append(pad + "}")
        elif node.kind == "perform_varying_inline":
            match = re.match(
                r"^PERFORM(?:\s+WITH\s+TEST\s+(BEFORE|AFTER))?\s+VARYING\s+([A-Za-z0-9-]+)\s+FROM\s+(.+?)\s+BY\s+(.+?)\s+UNTIL\s+(.+)$",
                node.text,
                re.IGNORECASE,
            )
            if not match:
                raise UnsupportedConstruct("malformed inline PERFORM VARYING: " + node.text)
            test_mode = match.group(1).upper() if match.group(1) else "BEFORE"
            index_token, start_text, step_text, condition_text = match.group(2, 3, 4, 5)
            variable = _resolve_native_variable(index_token, variables)
            if variable is None or variable.is_group or variable.is_array:
                raise UnsupportedConstruct("unsupported PERFORM VARYING index: " + index_token)
            index_expr = _native_ident(variable, variables)
            start_expr = _literal(start_text, variables, lang)
            step_expr = _literal(step_text, variables, lang)
            condition = _native_condition(condition_text, variables, lang)
            output.append(pad + f"{index_expr} = {start_expr};")
            if test_mode == "AFTER":
                output.append(pad + ("while (1) {" if lang == "c" else "loop {"))
                body = _emit_nodes(node.body, variables, lang, indent + 1)
                output.extend(body or ["    " * (indent + 1) + (";" if lang == "c" else "() ;")])
                output.append("    " * (indent + 1) + f"{index_expr} += {step_expr};")
                output.append("    " * (indent + 1) + (f"if ({condition}) {{ break; }}" if lang == "c" else f"if {condition} {{ break; }}"))
            else:
                output.append(pad + (f"while (!({condition})) {{" if lang == "c" else f"while !({condition}) {{"))
                body = _emit_nodes(node.body, variables, lang, indent + 1)
                output.extend(body or ["    " * (indent + 1) + (";" if lang == "c" else "() ;")])
                output.append("    " * (indent + 1) + f"{index_expr} += {step_expr};")
            output.append(pad + "}")
        elif node.kind == "perform_inline":
            output.append(pad + "{")
            body = _emit_nodes(node.body, variables, lang, indent + 1)
            output.extend(body or ["    " * (indent + 1) + (";" if lang == "c" else "() ;")])
            output.append(pad + "}")
        elif node.kind == "perform_times_inline":
            match = re.match(r"^PERFORM\s+(\d+)\s+TIMES$", node.text, re.IGNORECASE)
            count = int(match.group(1)) if match else 0
            loop_name = f"_cobol_perform_{len(output)}"
            if lang == "c":
                output.append(pad + f"for (int {loop_name} = 0; {loop_name} < {count}; ++{loop_name}) {{")
            else:
                output.append(pad + f"for {loop_name} in 0..{count} {{")
            body = _emit_nodes(node.body, variables, lang, indent + 1)
            output.extend(body or ["    " * (indent + 1) + (";" if lang == "c" else "() ;")])
            output.append(pad + "}")
        elif node.kind == "if":
            match = core.RE_IF_OPEN.match(node.text)
            if not match:
                raise UnsupportedConstruct("malformed IF node: " + node.text)
            condition = _native_condition(match.group(1), variables, lang)
            output.append(pad + (f"if ({condition}) {{" if lang == "c" else f"if {condition} {{"))
            body = _emit_nodes(node.then_branch, variables, lang, indent + 1)
            output.extend(body or ["    " * (indent + 1) + (";" if lang == "c" else "() ;")])
            if node.else_branch:
                output.append(pad + "} else {")
                body = _emit_nodes(node.else_branch, variables, lang, indent + 1)
                output.extend(body or ["    " * (indent + 1) + (";" if lang == "c" else "() ;")])
            output.append(pad + "}")
        else:
            raise UnsupportedConstruct(f"control-flow node '{node.kind}' is not yet supported by experimental {lang} backend")
    return output


def emit_native(program: core.Program, lang: str) -> str:
    if lang not in ("c", "rust"):
        raise ValueError("lang must be c or rust")
    variables = {var.name.upper(): var for var in program.variables}
    for var in program.variables:
        if var.is_array or var.redefines:
            raise UnsupportedConstruct(
                f"data layout outside native subset: {var.name} (OCCURS and REDEFINES need shared storage-layout support)"
            )
    statements: list[str] = []
    for paragraph in program.paragraph_order:
        statements.extend(_emit_nodes(program.paragraphs.get(paragraph, []), variables, lang))
    lines: list[str] = [
        f"/* Experimental COBOL -> {lang.upper()} translation for {program.program_id}. */"
    ]
    if lang == "c":
        lines += ["#include <stdio.h>", "#include <stdlib.h>", "#include <string.h>", "", "int main(void) {"]
        for var in program.variables:
            if var.is_group:
                continue
            ident = _native_ident(var, variables)
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
        lines += statements
        if not any(line.strip() == "return 0;" for line in statements):
            lines.append("    return 0;")
        lines += ["}"]
    else:
        lines += ["use std::io::{self, Write};", "", "fn main() {"]
        for var in program.variables:
            if var.is_group:
                continue
            ident = _native_ident(var, variables)
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
        lines += statements
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
