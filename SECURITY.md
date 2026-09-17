# Security policy

## Reporting a vulnerability

Please report security issues through GitHub's private vulnerability
reporting ("Report a vulnerability" on the repository's Security tab):

https://github.com/Huntsman1756/bankcall-es/security/advisories/new

Do not open a public issue for a vulnerability.

## Scope

`bankcall` is an offline CLI: it parses local XBRL files into local Parquet
tables and queries them with DuckDB. The most relevant risks are:

- XML parser attacks (XXE, entity expansion) via crafted `.xbrl` files —
  ingest parses with external entity resolution and network access disabled.
- Accidental publication of secrets or personal data in `evidence/`,
  `g0_acquisition/` or local tooling configuration.

## Secrets in this repository

No credentials may be committed. The acquisition probe writes sanitized
captures only (`g0_acquisition/curl.txt` is gitignored). If you find a
secret in the repository, report it privately as above.
