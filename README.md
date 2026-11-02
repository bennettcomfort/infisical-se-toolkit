# Infisical Self-Hosting Toolkit

Unofficial community project, not affiliated with or endorsed by Infisical.

A toolkit for solutions engineers and platform engineers designing self-hosted Infisical deployments. It pairs a small knowledge base of self-hosting doc facts with an MCP server (`search_knowledge`, `make_diagram`), Excalidraw diagram generation, a system prompt, and prompt recipes.

## What's in the kit

| Path | Purpose |
|---|---|
| `SYSTEM_PROMPT.md` | Custom instructions for the design co-pilot |
| `KNOWLEDGE.md` | Condensed self-hosting facts, each with a source link |
| `PROMPTS.md` | Prompt recipes (`REQS`, `ADD`, `CURVE`, `FAIL`, `CMP`, `SIZE`, `MIGRATE`, `SUM`, `DIAG`, `FACT`) |
| `excalidraw/*.excalidraw` | Example diagrams: base HA, air-gapped regulated, multi-region EKS |
| `excalidraw/gen_diagram.py` and `excalidraw/specs/` | Turn a YAML component list into an `.excalidraw` file |
| `mcp_server/` | Stdio MCP server with `search_knowledge` and `make_diagram` |

This repo does not include rendered diagram images. Open the `.excalidraw` files on [excalidraw.com](https://excalidraw.com) (drag the file onto the canvas, or Menu > Open).

## Quickstart

```bash
python -m venv .venv
.venv/bin/pip install -r mcp_server/requirements.txt
.venv/bin/python mcp_server/test_client.py
```

`test_client.py` starts the server over stdio, lists the tools, searches the knowledge base, and writes `excalidraw/generated/smoke.excalidraw`.

Draw a diagram from a spec:

```bash
.venv/bin/python excalidraw/gen_diagram.py excalidraw/specs/base_reference.yaml out.excalidraw
```

## Claude Desktop

Add this to `claude_desktop_config.json`. Replace the path with the absolute path to this repo. Point `command` at the same interpreter that has the requirements installed (for example `.venv/bin/python`).

```json
{
  "mcpServers": {
    "infisical-self-hosting": {
      "command": "/ABS/PATH/infisical-se-toolkit/.venv/bin/python",
      "args": ["/ABS/PATH/infisical-se-toolkit/mcp_server/server.py"]
    }
  }
}
```

Cursor uses the same `mcpServers` block.

## Shorthand

Paste `SYSTEM_PROMPT.md` as the system prompt and attach `KNOWLEDGE.md`. Start a message with one of these prefixes. The co-pilot switches mode on the prefix. Full templates are in `PROMPTS.md`.

| Prefix | What you get | Example |
|---|---|---|
| `REQS` | Full design from a first set of requirements | `REQS: fintech, aws eks, 600 eng, soc2, okta, rto 30m rpo 5m, us-east+us-west. full design.` |
| `ADD` | Diff only, plus updated diagram YAML | `ADD: offline license, no outbound internet. What changes?` |
| `CURVE` | Short answer to a new constraint | `CURVE: "EU secrets can't leave EU"` |
| `FAIL` | Impact, detection, recovery, and the diagram change | `FAIL: primary Postgres down in us-east-1a. HA=RDS Multi-AZ.` |
| `CMP` | Comparison table, then a recommendation | `CMP: Helm/K8s vs Docker Compose vs ECS for an air-gapped bank.` |
| `SIZE` | Small / medium / large mapping from [K2]. No prices. | `SIZE: 5k devs, 300 services, audit kept 7 years.` |
| `MIGRATE` | What Vault or Doppler can move, and cutover risks | `MIGRATE: from Vault with KV v2, Kubernetes auth, and policies.` |
| `SUM` | Six-bullet recap, risks, and a short POC | `SUM: recap the design.` |
| `DIAG` | Diagram YAML only | `DIAG: on-prem, air-gapped, FIPS, HSM, Okta SAML, RTO 1h.` |
| `FACT` | Yes/no against `KNOWLEDGE.md`, or unverified | `FACT: Redis noeviction is required?` |

A first pass can also be plain requirements, then a prefix for the next step:

```
bank, on-prem, air-gapped, FIPS, Okta SAML, 5k devs, RTO 1h. Search the knowledge, then DIAG.
```

## Example diagrams

- `excalidraw/base_reference.excalidraw` — single-region HA (from `excalidraw/specs/base_reference.yaml`)
- `excalidraw/airgapped_regulated.excalidraw` — on-prem, FIPS, HSM, no egress (from `excalidraw/specs/airgapped_regulated.yaml`)
- `excalidraw/multiregion_eks.excalidraw` — AWS EKS primary plus secondaries (from `excalidraw/specs/multiregion_eks.yaml`)

## License

MIT. See `LICENSE`. Infisical is a trademark of its owner. This project is not an Infisical product.
