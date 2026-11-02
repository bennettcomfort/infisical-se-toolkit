# Prompt Recipes

Paste a template, fill in the `<>`, and send it. Prefixes match the modes in `SYSTEM_PROMPT.md`. The co-pilot should search `KNOWLEDGE.md` (or call `search_knowledge`) before it states a number.

## 1. New requirement / first pass

```
REQS: <industry>, <hosting: aws/gcp/azure/onprem/airgap>, <k8s|vm>, <#eng/#svcs/#secrets>, <compliance>, <IdP>, <RTO/RPO>, <regions>, <existing tool>. Give full design.
```

Example: `REQS: fintech, aws eks, 600 eng 250 svcs, soc2+pci, okta, rto 30m rpo 5m, us-east+us-west, vault oss today. full design.`

## 2. Add a requirement mid-design

```
ADD: <new req>. What changes? Diff only + updated YAML.
```

## 3. Curveball

```
CURVE: "<new constraint>"
```

Examples: "we can't allow any outbound internet", "security wants keys in our Luna HSM", "EU secrets can't leave EU", "we need 50k reads/min at deploy".

## 4. Postgres failure

```
FAIL: primary Postgres down in <region/AZ>. HA=<mode>. Impact, detection, recovery, RTO/RPO, diagram change.
```

## 5. Other failures

```
FAIL: <redis lost data | AZ outage | region outage | HSM unreachable | ENCRYPTION_KEY lost | bad upgrade>
```

## 6. Kubernetes vs Docker vs VMs

```
CMP: Helm/K8s vs Docker Compose vs Linux package vs standalone container vs ECS for <context>. Ops burden, HA, upgrades, air-gap fit.
```

## 7. Sizing

```
SIZE: <#users>, <#services>, <reads/min peak>, <audit retention>. Map to small/medium/large [K2]: container count, Postgres, Redis, storage. Do not invent prices.
```

## 8. Migration from Vault or Doppler

```
MIGRATE: from <Vault | Doppler> with <KV v2, dynamic DB creds, Kubernetes auth, policies>. Phased plan, what the docs say can move, coexistence, cutover risks.
```

## 9. Summary

```
SUM: recap the design in 6 bullets + risks + a short POC success criteria.
```

## 10. Diagram only

```
DIAG: <describe the design or the changes>
```

Then run `python excalidraw/gen_diagram.py spec.yaml out.excalidraw`, or call the MCP tool `make_diagram`, and open the file at [excalidraw.com](https://excalidraw.com) (Menu > Open).

## 11. Fact check

```
FACT: <claim>? yes/no + KNOWLEDGE section. If it is not in KNOWLEDGE.md, say unverified.
```

## 12. Worked example

```
bank, on-prem, air-gapped, FIPS, Okta SAML, 5k devs, RTO 1h. Search the knowledge, then DIAG.
```
