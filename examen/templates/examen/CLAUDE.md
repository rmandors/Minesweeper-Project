# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Minesweeper implemented on the **MARIE.js** simulator. The 16×16 board renders on MARIE's graphical display and all game logic runs in MARIE assembly. There is no build/test toolchain — the workflow is:

1. Run `python/script.py` (or the Colab notebook linked in `README.md`) to generate `buscaminas.mas` with random mines and per-cell neighbor counts already embedded as `DEC` data.
2. Paste the contents of the generated `.mas` file into [marie.js.org](https://marie.js.org) and run it.

There is no package manager, no test runner, no linter. Verification is done by running the assembly in the MARIE.js simulator and observing the display / score output.

## Repository layout (non-obvious bits)

- `python/script.py` — board generator. Outputs a complete MARIE source file by concatenating `marie/logic.mas` with a `BoardData` block. Mine count is its only input.
- `marie/logic.mas` — canonical game logic. The "real" board is appended to this file by the Python generator; do not hand-edit `BoardData` here.
- `examen/templates/` — exam variant of the project. `base.mas` is the same logic but with the hardcoded `BoardData` map removed; instead it calls `JnS BuildPattern` at startup. Each `pattern_*.mas` file defines a different `BuildPattern` routine that seeds mines algorithmically (checker, cross, rectangle, triangles, X). To produce a runnable program, **concatenate `base.mas` + one `pattern_*.mas`** and paste the result into MARIE.js. Pattern parameters live near the bottom of each pattern file (e.g. `PT_Gap`, `PT_OffsetOdd`, `PT_XThickness`).
- `docs/` — LaTeX paper + poster. Not part of the runtime.

## MARIE memory map (used across both `marie/logic.mas` and `examen/templates/base.mas`)

```
0x100 - 0x274   Code
0x275 - 0x2C4   Variables and color constants
0x2C5 - 0x3C6   BoardData (256 cells; -1 = mine, 0..8 = neighbor count)
0xF00 - 0xFFF   Display (16×16)
```

The "visible" board is the display memory itself; cell state is encoded by color (see README's color table). The "real" board lives in `BoardData` and is read-only at runtime.

## Input convention

Each turn reads three sequential `INPUT` values: row (1–16), column (1–16), action (1=reveal, 2=toggle flag). Validation routines (`ValidateRow`, `ValidateCol`, `ValidateAction`) loop back to `GameLoop` on invalid input.

## MARIE assembly — language reference

This project targets the **MARIE.js** simulator (https://marie.js.org/, source: https://github.com/MARIE-js/MARIE.js, wiki: https://github.com/MARIE-js/MARIE.js/wiki).

Syntax: `[Label, ]Operation[ Operand]`. `/` starts a line comment. Operations are case-insensitive. Hex operands need a leading `0` if the first digit is > 9. Labels cannot start with a digit and cannot contain whitespace or commas; a label as an operand resolves to the address of its instruction/directive.

Directives: `DEC X`, `HEX X`, `OCT X`, `ORG X`.

Instruction set:
- `Load X` / `Store X` / `LoadI X` / `LoadImmi X` / `Clear` (= `LoadImmi 0`) / `StoreI X`
- `Add X` / `Subt X` / `AddI X`
- `Input` / `Output` / `Halt`
- `Jump X` / `JumpI X` / `JnS X` (alias `Adr X`) — `JnS` stores the return address at `M[X]` then jumps to `X+1`, so callees start with `Label, HEX 000` (the return slot) and return via `JumpI Label`.
- `SkipCond X` — skip next instruction if: `000` AC<0, `400` AC=0, `800` AC>0, `0C00` AC≠0.

### Hard syntactic rule (easy to forget)

**After `Label,` you must put an instruction or directive on the same line — never leave it blank and never put a comment there.** Write:

```
BuildPattern,    HEX 000
                 Clear
                 Store   TotalMines
```

not:

```
BuildPattern,                / wrong — line is empty after the comma
                 HEX 000
```

## Conventions when editing assembly

- Labels in `base.mas` that the patterns rely on: `BoardStart`, `BoardData`, `TotalMines`, `SafeCellsLeft`, `DisplayWidth`, `One`, `Two`. Pattern files use a `PT_` prefix for their own labels/variables to avoid collisions — keep that prefix when adding new patterns.
- The `BuildPattern` entry point must be a `JnS`-callable routine (`HEX 000` header, `JumpI BuildPattern` to return), because `base.mas` invokes it once at startup with `JnS BuildPattern`.
- New patterns should reuse the shared helpers `PT_ClearBoard` and `PT_SetMineAtRC` from existing pattern files rather than reimplementing board addressing — those helpers handle the (row,col) → linear-address math and the duplicate-mine guard, and they keep `TotalMines` / `SafeCellsLeft` in sync.

### Comment style — match the user's voice

The assembly was written by the user; new code must read like they wrote it. Observed style:

- Spanish, lowercase, terse, no trailing period. Comments describe **intent or the high-level effect**, not the opcode (`/ bajar una fila`, `/ columna correcta en fila 1`, `/ si RowInput <= RowCounter -> listo`). Never write `/ load value into AC`-style narration.
- Inline comments are common, placed after the instruction on the same line and aligned roughly with neighbors using spaces/tabs.
- For `SkipCond`, the comment phrases the condition from the user's perspective (`/ Check for RowInput >= 1, else skip`, `/ salta si ColIdx > 0`), not the raw `400/800/000` semantics.
- Section dividers use a banner block:
  ```
  / ================================================================
  / TITULO DE LA SECCION
  / ================================================================
  ```
- Routines often get a short `/`-prefixed paragraph above them describing purpose and inputs/outputs (see `MoveToCoords`, `PT_SetMineAtRC`, `BuildPattern`).
- Leave existing whitespace/alignment alone — do not retab or reformat surrounding code when making a small edit.

## Working with the code

- To regenerate the playable file: `python python/script.py` (then paste the output `.mas` into MARIE.js).
- To test an exam pattern: concatenate `examen/templates/base.mas` and the chosen `pattern_*.mas` (e.g. `cat base.mas pattern_x.mas > out.mas`) and paste into MARIE.js.
- There is nothing to lint, build, or unit-test locally — correctness is validated by running in the simulator.
