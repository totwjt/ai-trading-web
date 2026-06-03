# mcp-deploy Production Release Automation Tasks

Source requirements:

- `mcp-deploy/docs/production-release-requirements.md`
- `mcp-deploy/docs/development-prompt.md`

Implement these tasks in order unless a later task is required to make an
earlier task testable. Do not change the confirmed requirements without asking
the user.

## T1. Split Release and Runtime Config Scopes

Goal: separate local release-control secrets from production runtime env.

Changes:

- Treat `mcp-deploy/.env` as the local MCP release-control file.
- Treat root `.env.deploy` as the business runtime source file.
- Move SSH and Harbor login configuration into release-control scope.
- Keep runtime database and business API configuration in runtime scope.
- Generate remote `.env.deploy` by filtering runtime-safe keys only.
- Add a managed marker to generated remote env files.

Acceptance:

- Remote env generation never includes `SSH_PASSWORD`, `SSH_KEY_PATH`,
  `HARBOR_USERNAME`, or `HARBOR_PASSWORD`.
- Existing managed remote env files can be overwritten automatically.
- Existing non-managed remote env files require confirmation.

## T2. Add Config Migration Support

Goal: migrate the current mixed `.env.deploy` layout with minimal manual work.

Changes:

- Add a read-only migration preview that classifies keys by scope.
- Add a migration tool that writes release-control keys to `mcp-deploy/.env`,
  leaves runtime keys in root `.env.deploy`, and creates backups before changes.
- Preserve explicit existing values.

Acceptance:

- Mixed files containing `SSH_*`, Harbor credentials, database URLs, and API URLs
  are split correctly.
- Migration never prints sensitive values.
- Backup files are created before modifying existing env files.

## T3. Add Runtime Key Discovery

Goal: discover required runtime keys without requiring AI to guess.

Changes:

- Maintain a required runtime key allowlist for known production runtime values.
- Scan production backend code for likely runtime env usage such as
  `os.getenv("...")`.
- Mark scanned keys that are not in the allowlist as `discovered=true`.
- Exclude tests, scripts, and obvious development-only paths from hard gates.

Acceptance:

- Known runtime keys are always checked.
- A newly added `*_API` env usage is surfaced in config status.
- Discovered keys are included in `needs_input` but clearly marked.

## T4. Add Structured needs_input Flow

Goal: let MCP request missing production values through AI in one batch.

Changes:

- Add a structured response shape for `needs_input`.
- Include field key, scope, label, current state, expected format, required flag,
  discovered flag, and redaction policy.
- Add a completion tool that validates user-provided values and writes them to
  the correct local env file.

Acceptance:

- Empty, missing, or placeholder critical values produce `needs_input`.
- AI can submit multiple field values in one tool call.
- After completion, status re-runs and no longer reports those fields missing.

## T5. Generate Release Image Tags

Goal: avoid requiring users to maintain non-critical image tags manually.

Changes:

- Generate timestamp image tags when no explicit tool argument or env value is
  provided.
- Apply the generated tag consistently to build, push, remote pull, and compose
  up.
- Include the selected tag in status and release summary.

Acceptance:

- A release without `IMAGE_TAG` uses a timestamp tag.
- Explicit tool argument overrides env.
- Explicit env value overrides generated value.

## T6. Support Password SSH Behind MCP Tools

Goal: prevent AI from hand-writing `sshpass` terminal commands.

Changes:

- Use SSH key auth when a valid key path is configured.
- Use `sshpass -e` when password auth is configured and no valid key is present.
- Detect missing local `sshpass` and return a blocked status with manual fix
  instructions.
- Keep passwords out of command output, logs, and tool responses.

Acceptance:

- All remote tools use the shared SSH execution path.
- Password auth works when `sshpass` is installed.
- Missing `sshpass` stops cleanly without exposing the password.

## T7. Add Remote Preflight and Bootstrap

Goal: initialize a new production environment safely.

Changes:

- Add remote deploy directory configuration with default `/root`.
- Create the remote deploy directory when missing.
- Upload `docker-compose.prod.yml` and generated remote `.env.deploy`.
- Check Docker and Docker Compose availability.
- Run `docker compose -f ... --env-file ... config`.
- Detect container and port conflicts.

Acceptance:

- New production hosts can be bootstrapped after SSH succeeds.
- Missing Docker or Compose stops with a manual fix list.
- Conflicts stop release and do not auto-clean containers.

## T8. Add Database Validation

Goal: make database misconfiguration a hard release gate.

Changes:

- Validate database URLs required for production runtime.
- Check connection, authentication, and database existence.
- Redact credentials in all output.

Acceptance:

- Invalid credentials block release.
- Unreachable host blocks release.
- Successful validation is reported without leaking connection strings.

## T9. Add deploy__status

Goal: make the normal AI flow state-driven.

Changes:

- Return config status, missing fields, generated defaults, SSH auth mode,
  local dependency status, build platform, remote path, preflight status, and
  recommended next action.
- Return one of `ready`, `needs_input`, `blocked`, or `warning`.

Acceptance:

- AI can decide the next MCP call from `deploy__status` alone.
- Sensitive values are represented as booleans or redacted summaries.

## T10. Add deploy__run_release

Goal: provide one high-level release entrypoint.

Changes:

- Orchestrate status, validation, image build, Harbor login/push, SSH test,
  remote preflight, image pull, compose up, startup checks, and health checks.
- Support `services=all|backend|web`.
- Support explicit tag override and skip flags for build/push/pull.
- Stop only for `needs_input`, blocked dependencies, conflicts, or failed hard
  validation.

Acceptance:

- A complete release can run through MCP tools without AI issuing terminal
  SSH/docker commands.
- Backend-only release does not recreate or pull web unnecessarily.
- Release summary includes tag, services, remote path, and verification result.

## T11. Add Startup and Health Verification

Goal: surface runtime failures immediately after deployment.

Changes:

- Verify target containers are `Up`.
- Tail recent logs for startup-level failure patterns.
- Check backend health and frontend root.
- Treat business workflow checks as manual unless configured.

Acceptance:

- `exec format error` is detected and reported.
- Stopped target containers fail verification.
- Business API availability is not falsely reported as fully verified.

## T12. Add Test Coverage

Goal: protect the release automation behavior.

Changes:

- Add unit tests for config classification, env generation, redaction, tag
  generation, placeholder detection, and needs_input responses.
- Add command construction tests for SSH key and password auth.
- Add mocked release-flow tests for success, missing config, missing sshpass,
  remote conflict, and database validation failure.

Acceptance:

- Tests cover all new critical branches.
- Tests do not require real SSH, Docker, Harbor, or production databases.
