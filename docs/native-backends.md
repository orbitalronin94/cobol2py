# Experimental C and Rust backends

`cobol2native.py` adds the first C and Rust output paths while reusing the existing `cobol2py.py` parser and data model. This is an intentionally small prototype, not a claim of COBOL equivalence.

## Try it

```bash
python cobol2native.py hello.cbl --lang c --out hello.c
cc -std=c11 -Wall -Wextra hello.c -o hello
./hello

python cobol2native.py hello.cbl --lang rust --out hello.rs
rustc hello.rs -o hello-rust
./hello-rust
```

## Supported subset (initial)

- Elementary, top-level `PIC X/A` and simple integer `PIC 9` storage.
- Basic `DISPLAY`, literal/identifier `MOVE`, simple `ADD ... TO`, and termination statements.
- The parser is shared; C and Rust generation is separate.

## Explicit limitations

- Groups, `OCCURS`, `REDEFINES`, decimals/sign/scaling, `ACCEPT`, and complex expressions are not implemented.
- Structured control flow and paragraph calls are rejected rather than silently approximated.
- This prototype has no external-corpus score yet. It must be benchmarked separately against GnuCOBOL before comparing it with Python.
- Rust output requires `rustc`; C output requires a C compiler. Neither compiler is a runtime dependency of the translator itself.

## Next architecture steps

1. Extract a language-neutral semantic IR from the shared parser.
2. Implement storage layouts and control flow once in the IR, then target-specific code generation.
3. Add common conformance fixtures and the same frozen primary/holdout corpus to every backend.
4. Only transfer C/Rust successes into Python after verifying the generated program against GnuCOBOL.
