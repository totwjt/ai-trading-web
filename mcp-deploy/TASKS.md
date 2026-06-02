# mcp-deploy Follow-up Tasks

These tasks come from the 2026-06-02 backend production deployment. The current
tooling can guide the flow, but it did not fully match the actual production
environment.

## 1. Make Remote Deploy Path Configurable

- Add `REMOTE_DEPLOY_DIR` to `DeployConfig`, defaulting to `/root`.
- Replace hard-coded `cd /root/ai-trading-web` in SSH deploy tools with `cd {REMOTE_DEPLOY_DIR}`.
- Apply this to pull, compose up, compose down, rollback, verification, and any future remote compose commands.
- Acceptance: production path `/root/docker-compose.prod.yml` and `/root/.env.deploy` works without manual command edits.

## 2. Build Images for the Production Platform

- Add `BUILD_PLATFORM`, defaulting to `linux/amd64`.
- Pass `--platform {BUILD_PLATFORM}` to backend and web `docker build` commands.
- Include the platform value in `deploy__build_status` output.
- Acceptance: images built on an Apple Silicon local machine run on the amd64 production host without `exec format error`.

## 3. Validate Runtime Data Source Variables

- Keep `MARKET_DATA_DATABASE_URL` as a required deploy variable.
- Include it in `DeployConfig.summarize()` only as a boolean or redacted value.
- Extend `deploy__validate_env` to detect placeholder values for this variable.
- Acceptance: deploy validation fails before build/push if `MARKET_DATA_DATABASE_URL` is absent or still placeholder text.

## 4. Support SSH Password Authentication

- `DeployConfig` already reads `SSH_PASSWORD`; `_run_ssh_command` should use it when no key path is configured.
- Prefer `sshpass` only when available; otherwise return an actionable error.
- Keep password out of logs and tool responses.
- Acceptance: deploy tools can connect using `.env.deploy` password credentials, matching the manual release path used today.

## 5. Support Single-Service Pull and Restart

- Make `deploy__ssh_pull_images(services="backend")` run `docker compose ... pull backend`.
- Add a `services` argument to `deploy__ssh_compose_up`; support `backend`, `web`, and `all`.
- Keep the existing confirmation guard for compose up.
- Acceptance: backend-only deployments do not recreate or pull unchanged web images.

## 6. Detect Compose/Env Path Mismatch Early

- Add a read-only preflight that checks:
  - `{REMOTE_DEPLOY_DIR}/docker-compose.prod.yml` exists.
  - `{REMOTE_DEPLOY_DIR}/.env.deploy` exists.
  - `docker compose -f ... --env-file ... config` succeeds.
- Report the actual path used in all deploy summaries.
- Acceptance: the tool reports the wrong `/root/ai-trading-web` assumption before any pull/up command is attempted.

## 7. Add Post-Deploy Startup Sanity Checks

- After compose up, verify the target service is `Up`.
- Fetch a small tail of logs and flag startup-level failures such as `exec format error`.
- Keep business/API validation optional because production functional testing may be done manually.
- Acceptance: architecture/startup failures are surfaced immediately after deployment.
