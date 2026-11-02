# Infisical Self-Hosting Knowledge Base

Condensed facts for designing self-hosted Infisical deployments. Each fact below was checked against the self-hosting docs (or, for migrations, the migration guide linked in that section). Docs index: https://infisical.com/docs/self-hosting/overview

## 1. Deployment options

Source: https://infisical.com/docs/self-hosting/overview

- Docker (single container), Docker Compose (Infisical + PostgreSQL + Redis), Kubernetes (official Helm chart with bundled PostgreSQL and Redis), Linux package (no containers), AWS (ECS Fargate + RDS + ElastiCache + ALB), GCP (GKE + Cloud SQL + Memorystore).
- Reasons to self-host: compliance (SOC 2, HIPAA, FIPS 140-3), data stays under the customer's governance, and topology flexibility (air-gapped bare metal, Kubernetes, cloud VMs).
- Configure guides linked from the overview: environment variables, custom certificates, HSM integration, programmatic provisioning, CDN caching.
- Operate guides linked from the overview: server admin console, upgrades, multi-region replication, production hardening, monitoring and telemetry (Grafana/OpenTelemetry), MongoDB-to-PostgreSQL migration, FAQ.
- The overview lists SSO and gateways as examples of Enterprise features. See licensing in section 14.

Helm: https://infisical.com/docs/self-hosting/deployment-options/kubernetes-helm

- Configuration comes from a Kubernetes Secret named `infisical-secrets` in the release namespace (`kubeSecretRef` defaults to that name).
- Bundled PostgreSQL and Redis are not configured for high availability. Use them for testing. Production should use external managed PostgreSQL and Redis.
- The chart bundles an ingress-nginx controller (class `infisical-nginx`) by default. Set `ingress.nginx.enabled: false` and `ingress.ingressClassName` when the cluster already has an ingress controller.
- Charts are published to Cloudsmith: https://infisical.com/docs/self-hosting/helm-charts/overview

Docker Compose: https://infisical.com/docs/self-hosting/deployment-options/docker-compose

- Runs Infisical, PostgreSQL, and Redis on a single Docker host. It is not designed for high-availability production. Use it for a proof of concept, development, or small-scale deployments. The Kubernetes guide is the HA path.

Standalone container: https://infisical.com/docs/self-hosting/deployment-options/standalone-infisical

- Image `infisical/infisical:<version>` contains only the application. You supply PostgreSQL and Redis. A minimal `docker run` sets `ENCRYPTION_KEY`, `AUTH_SECRET`, `DB_CONNECTION_URI`, `SITE_URL`, and `REDIS_URL`.

## 2. Hardware requirements

Source: https://infisical.com/docs/self-hosting/configuration/requirements

- The app is stateless and scales horizontally. Each container typically needs no more than 2–4 cores and 4–8 GB of memory. Allow 1–2 GB of disk for logs and metrics. All persisted data lives in the database.
- Per container: Small is 2 cores and 4 GB RAM, with 2+ containers. Medium is 2–4 cores and 4–8 GB RAM, with 5+ containers. Large is 2–4 cores and 4–8 GB RAM, with 10+ containers. Scale horizontally first.
- PostgreSQL is the only supported database. It is tested on PostgreSQL 16; use 14 or newer. Small: 2 vCPU / 8 GB RAM / 100 GB disk. Medium: 4 vCPU / 16 GB RAM / 200 GB disk. Large: 8 vCPU / 32 GB RAM / 500 GB disk. Storage is high because audit logs live in the database by default.
- Redis is a required persistent datastore: job queue, distributed locks, and scheduled-job coordination. The instance refuses to start without it and runs degraded while it is unreachable. Use Redis 6.x or 7.x (6.2 or newer). Standalone (with or without HA) and Sentinel are supported. Active-passive is recommended; active-active is untested. `noeviction` is required. Turn on AOF or RDB persistence and back Redis up, because pending rotations, syncs, and webhooks live there. A small deployment is 2 vCPU / 4 GB RAM / 30 GB SSD. Give Redis the same availability target as the app.

## 3. Environment variables

Source: https://infisical.com/docs/self-hosting/configuration/envars

- A minimal instance needs `ENCRYPTION_KEY`, `AUTH_SECRET`, `DB_CONNECTION_URI`, and `REDIS_URL`. Redis is required: the instance will not start unless `REDIS_URL`, `REDIS_SENTINEL_HOSTS`, or `REDIS_CLUSTER_HOSTS` is set. `SITE_URL` is also required (absolute URL, including the protocol). The standalone Docker guide lists `SITE_URL` in the minimal set: https://infisical.com/docs/self-hosting/deployment-options/standalone-infisical
- `ENCRYPTION_KEY` is a random 16-byte hex string (`openssl rand -hex 16`). For FIPS-enabled deployments it must instead be a 256-bit base64 key (`openssl rand -base64 32`).
- `AUTH_SECRET` is a random 32-byte base64 string (`openssl rand -base64 32`).
- `DB_READ_REPLICAS` is a JSON list of replica connection objects, for example `[{"DB_CONNECTION_URI":"..."}]`.
- `AUDIT_LOGS_DB_CONNECTION_URI` stores audit logs in a separate PostgreSQL database. When unset, audit logs stay in the main database.
- `DISABLE_POSTGRES_AUDIT_LOG_STORAGE=true` stops writing audit logs to PostgreSQL. Events are still sent to ClickHouse when configured, and to any configured audit log streams.
- SMTP is configured with `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_ADDRESS`, and `SMTP_FROM_NAME`.
- Enterprise license: set `LICENSE_KEY`. https://infisical.com/docs/self-hosting/ee

## 4. Encryption and keys

- Standard encryption uses `ENCRYPTION_KEY` as a software-protected root key that encrypts the KMS keys inside the instance. HSM mode stores the root encryption key on the HSM and uses it to encrypt those KMS keys. https://infisical.com/docs/self-hosting/guides/hsm-integration
- Without `ENCRYPTION_KEY`, a restored database cannot be decrypted. Store the key outside the cluster and apart from database backups. https://infisical.com/docs/self-hosting/deployment-options/kubernetes-helm and https://infisical.com/docs/self-hosting/deployment-options/docker-compose
- If the HSM is lost or destroyed, data in Infisical can no longer be decrypted. https://infisical.com/docs/self-hosting/guides/hsm-integration
- External KMS (AWS KMS, Google Cloud KMS, Azure Key Vault listed as coming soon) can protect each project's workspace key. That workspace key encrypts the secret data (envelope encryption). https://infisical.com/docs/self-hosting/guides/production-hardening
- Rotating `ENCRYPTION_KEY` is documented at https://infisical.com/docs/self-hosting/guides/rotating-the-encryption-key. The new key is shown once. After rotation, losing the new key means losing access to every secret, and a backup taken before the rotation still needs the old key.

## 5. HSM

Source: https://infisical.com/docs/self-hosting/guides/hsm-integration

- Changing the encryption strategy is Enterprise-only, for on-premise instances that have an Enterprise license.
- PKCS#11 2.30 or newer. Documented providers include Thales Luna, AWS CloudHSM, and Fortanix.
- The HSM wraps the root KMS key. Extra latency shows up when instances start or when the encryption strategy changes, not on ordinary requests.

## 6. FIPS 140-3

Source: https://infisical.com/docs/self-hosting/guides/production-hardening

- The self-hosting overview lists FIPS 140-3 as a reason teams self-host: https://infisical.com/docs/self-hosting/overview
- Deploy the `infisical/infisical-fips` image, available to Enterprise customers. The hardening guide says Infisical meets FIPS 140-3 through validated cryptographic modules, and that the attestation letter is in the Infisical Trust Center.
- FIPS deployments must use a 256-bit base64 `ENCRYPTION_KEY` (`openssl rand -base64 32`). https://infisical.com/docs/self-hosting/configuration/envars

## 7. Multi-region replication

Source: https://infisical.com/docs/self-hosting/guides/replication

- Paid feature. On a self-hosted instance it requires an Enterprise license. Architecture is one primary and N secondaries, using PostgreSQL async streaming replication (WAL). Lag is typically under one second.
- All mutations go through the primary, which avoids split-brain. Secondaries set `INFISICAL_PRIMARY_INSTANCE_URL`, serve reads locally, and forward writes to the primary.
- The primary's Redis runs background jobs (secret syncs, scheduled tasks, audit log processing). A secondary Redis keeps a local cache and processes only audit logs.
- Every instance must run the same version. Migrations run on the primary and replicate to secondaries. Upgrade the primary first, then the secondaries.
- A read replica can be promoted for disaster recovery. Promotion requires Infisical configuration changes so the promoted instance becomes primary and the other secondaries are repointed.
- Replication copies the full PostgreSQL dataset to every replica: secrets and version history, users, tokens, project configuration, policies, audit logs, and integration settings.

## 8. HA and scaling

Drawn only from sections 2 and 7 and the pages linked here.

- Run multiple stateless containers and scale out. Small starts at 2 or more containers. https://infisical.com/docs/self-hosting/configuration/requirements
- PostgreSQL: use an external HA service in production. The Helm guide points at managed Multi-AZ (RDS, Cloud SQL) rather than the bundled database. Add `DB_READ_REPLICAS` for read scale-out. https://infisical.com/docs/self-hosting/deployment-options/kubernetes-helm and https://infisical.com/docs/self-hosting/configuration/envars
- A connection pooler such as PgBouncer or RDS Proxy is optional. The env-var guide says it is worth the extra hop only when instance count pushes the deployment near `max_connections`. https://infisical.com/docs/self-hosting/configuration/envars
- Redis: Sentinel or a managed primary plus replica, `noeviction`, and AOF or RDB. https://infisical.com/docs/self-hosting/configuration/requirements
- Audit: a separate audit database, or `DISABLE_POSTGRES_AUDIT_LOG_STORAGE=true` so streams (and ClickHouse, if configured) keep the events. https://infisical.com/docs/self-hosting/configuration/envars
- More regions: replication secondaries, as in section 7.

## 9. AWS ECS reference architecture

Sources: https://infisical.com/docs/self-hosting/reference-architectures/aws-ecs and https://infisical.com/docs/self-hosting/overview

- ECS on Fargate across multiple Availability Zones, with an ALB in the overview's AWS option. RDS for PostgreSQL: a primary in one AZ and a read replica in another. ElastiCache for Redis: primary plus standby across two AZs. SES for email.
- Put Infisical's root credentials (database connection string, encryption key, and similar) in SSM Parameter Store, and restrict them to the Infisical tasks. RDS master credentials go in AWS Secrets Manager via the RDS integration.
- A NAT gateway is for outbound calls to external secret managers and for pulling images from Docker Hub. An air-gapped ECS task can use the public ECR image plus VPC endpoints instead of Docker Hub.

## 10. Gateway

- The overview lists gateways with SSO as Enterprise features. https://infisical.com/docs/self-hosting/overview
- Prefer a gateway over opening internal IP ranges on the Infisical instance. The gateway runs inside the private network and tunnels traffic over mTLS, so the instance does not need an internal-IP allowlist and its SSRF protection stays on. https://infisical.com/docs/self-hosting/guides/production-hardening
- The official chart `infisical-gateway` is outbound-only by default (relay mode, no inbound ports). Set `gateway.listenAddress` for direct listen mode, where Infisical dials the gateway. https://infisical.com/docs/self-hosting/helm-charts/overview and https://infisical.com/docs/self-hosting/helm-charts/gateway

## 11. Identity

- The self-hosting overview names SSO as an Enterprise feature. https://infisical.com/docs/self-hosting/overview
- Session cookies for OAuth SSO, SAML, OIDC, and LDAP login are signed with `COOKIE_SECRET_SIGN_KEY`. When unset, Infisical derives that key from the deployment's KMS root key. https://infisical.com/docs/self-hosting/configuration/envars

## 12. Kubernetes clients

Source: https://infisical.com/docs/self-hosting/helm-charts/overview

- `secrets-operator`: syncs, pushes, and manages secrets between Infisical and the cluster.
- `infisical-agent-injector`: mutating webhook that injects an Infisical Agent sidecar.
- `infisical-csi-provider`: mounts secrets into pods as files through the Secrets Store CSI Driver.
- `infisical-gateway`: private-network gateway (section 10).
- `infisical-pki-issuer`: cert-manager external issuer for Infisical Certificate Management.

## 13. Audit logs

Source: https://infisical.com/docs/self-hosting/configuration/envars

- Audit logs are stored in PostgreSQL by default (section 2). `AUDIT_LOGS_DB_CONNECTION_URI` moves them to another PostgreSQL database. `DISABLE_POSTGRES_AUDIT_LOG_STORAGE=true` skips PostgreSQL and still forwards events to ClickHouse (when configured) and to audit log streams.
- `AUDIT_LOG_STREAMS_ENABLED` (default true) controls external audit log streams. `DISABLE_AUDIT_LOG_GENERATION=true` produces no audit events at all.
- ClickHouse is an optional high-volume audit backend (`CLICKHOUSE_URL` and related variables on the same page).

## 14. Licensing and air-gapped installs

Source: https://infisical.com/docs/self-hosting/ee

- Set `LICENSE_KEY` to the issued key. An online key is checked against the Infisical license server. An offline key is detected from the key format and does not need that call (`LICENSE_KEY_OFFLINE` still works for older configs; the docs recommend `LICENSE_KEY` for both).
- When the license expires, the instance keeps running and Enterprise features turn off until the license is renewed.
- Air-gapped ECS, without general internet egress, is covered on the AWS reference page: use the ECR image and VPC endpoints instead of Docker Hub. https://infisical.com/docs/self-hosting/reference-architectures/aws-ecs

## 15. Upgrades

Source: https://infisical.com/docs/self-hosting/guides/upgrading-infisical

- Releases land about once a week. Back up PostgreSQL before upgrading.
- Schema migrations run automatically at boot. In a multi-instance deployment one instance takes a lock and migrates while the others wait.
- Downgrade by restoring a snapshot taken before the upgrade, then starting the older application version. Do not run a newer schema on an older build.
- With replication, upgrade the primary first (migrations run there), then upgrade the secondaries to the same version. https://infisical.com/docs/self-hosting/guides/replication

## 16. Production hardening

Source: https://infisical.com/docs/self-hosting/guides/production-hardening

- Use TLS on ingress, PostgreSQL (`sslmode`), Redis, and SMTP.
- On a new instance, public self-service signup turns off after the first super-admin account is created. Existing instances keep their previous setting; check Admin Console → Authentication.
- Restrict network access: default deny, allow the API and HTTPS only as needed, and keep PostgreSQL and Redis off the public internet. On Kubernetes, configure network policies and limit who can reach etcd and the Kubernetes API.
- Reach private systems through a gateway instead of allowlisting internal IPs (section 10).

## 17. Migration from Vault or Doppler

These two pages are platform guides, not under `/self-hosting`. They are included because they are the current migration docs.

Sources: https://infisical.com/docs/documentation/platform/external-migrations/overview and https://infisical.com/docs/documentation/platform/external-migrations/vault

- Supported sources are HashiCorp Vault and Doppler. Vault can move KV secrets, Kubernetes auth configuration, dynamic secret configurations, and policies. Doppler moves secrets from projects and configs, including root and branch environments.
- In-platform migration uses an App Connection scoped to a project or to the organization, and can import on demand. It supports Vault and Doppler.
- Bulk one-time import is an organization-wide cutover. It is supported for HashiCorp Vault.
