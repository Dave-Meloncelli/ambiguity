# Security Policy

## Scope

This project performs deterministic prompt analysis with zero external calls.
The analysis code itself (regex + dict + arithmetic) has no network access and
no runtime dependencies.

## Reporting

If you discover a security issue in the ambiguity-analyzer tool, please open an
issue at the GitHub repository. Do not disclose via public channels.

## UDL Bridge

The optional Federation bridge (`src/ambiguity/bridges.py`) performs a
try/import from C:\Federation. If you do not use Federation, no bridging code
activates. The bridge is read-only — it does not transmit data externally.
