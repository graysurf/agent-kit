# Fixture: Preamble too long

This is line 1 of the preamble.
This is line 2 of the preamble.
This is line 3 of the preamble (should fail).

## Contract

Prereqs:

- `bash`

Inputs:

- `--file <path>`

Outputs:

- Validation output on stdout/stderr

Exit codes:

- `0`: success
- `1`: failure

Failure modes:

- Preamble too long
