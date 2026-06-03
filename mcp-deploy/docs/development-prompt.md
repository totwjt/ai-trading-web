# Development Prompt for mcp-deploy Production Release Automation

Use this prompt for the development AI that will implement the production
release automation work.

```text
You are working in the AI-trading-web repository. Your task is to implement the
mcp-deploy production release automation defined by these documents:

1. mcp-deploy/docs/production-release-requirements.md
2. mcp-deploy/tasks/production-release-automation.md

Do not redesign the product requirements. Treat those documents as the source of
truth. If implementation details are ambiguous, inspect the current mcp-deploy
code first, then ask only about decisions that cannot be derived from the docs
or repository.

Primary goal:
The user should be able to fill production-specific environment values, then ask
AI to publish production through local MCP tools. AI should not need to hand-write
sshpass, ssh, docker, or docker compose terminal commands, and should not trigger
repeated terminal privilege prompts during the normal release flow.

Important confirmed requirements:
- Split release-control config and runtime config.
- Use mcp-deploy/.env for local MCP release-control values such as SSH details,
  SSH password/key path, Harbor login credentials, remote deploy path, and other
  local-only release controls.
- Use root .env.deploy as the business runtime source config.
- Never upload SSH_PASSWORD, SSH_KEY_PATH, HARBOR_USERNAME, or HARBOR_PASSWORD
  to production.
- Generate the remote production .env.deploy from runtime-safe values only, and
  include a managed marker.
- IMAGE_TAG should default to a timestamp-generated tag when no tool argument or
  env value is provided.
- Missing, empty, or placeholder critical values must return structured
  needs_input instead of being guessed.
- AI will collect needs_input values from the user and call an MCP completion
  tool to write them back.
- Database URLs are hard-gated by connection, authentication, and database
  existence validation.
- Business API URLs are required and cannot be empty or placeholders, but MCP
  does not claim full business verification unless explicit health metadata is
  configured.
- Runtime key discovery must use both a maintained required-key list and code
  scanning for likely new env keys.
- New discovered runtime keys should be surfaced in needs_input with a discovered
  marker.
- MCP may create the remote deploy directory and upload docker-compose.prod.yml
  plus the generated remote .env.deploy.
- MCP must not install local or remote system dependencies automatically.
- Missing local sshpass, missing remote Docker/Compose, port/container conflicts,
  and non-managed remote env overwrite all require stopping with actionable
  status or explicit confirmation.
- Provide a high-level deploy__run_release tool that orchestrates the normal
  release flow.

Implementation guidance:
- Keep the current safety posture: no automatic destructive remote cleanup.
- Keep sensitive values out of stdout, stderr, logs, exceptions, and MCP tool
  responses.
- Prefer structured return payloads over prose-only strings for status,
  needs_input, blocked, warning, and release summaries.
- Preserve existing lower-level tools where possible, but make deploy__status and
  deploy__run_release the normal AI-facing entrypoints.
- Add tests with mocked SSH, Docker, Harbor, and database behavior. Do not require
  real production infrastructure in tests.

Suggested implementation order:
1. Config classification and redaction helpers.
2. Runtime env generation with managed marker.
3. Config migration preview/apply tools.
4. Runtime key discovery and needs_input response shape.
5. Timestamp tag generation.
6. SSH password execution via sshpass -e.
7. Remote preflight/bootstrap.
8. Database validation.
9. deploy__status.
10. deploy__run_release.
11. Startup/health verification.
12. Test coverage and documentation updates.

Before finishing:
- Run the relevant unit tests.
- Verify no tool response can leak SSH password, Harbor password, or database
  credentials.
- Summarize which tasks from mcp-deploy/tasks/production-release-automation.md
  are complete and which remain.
```
