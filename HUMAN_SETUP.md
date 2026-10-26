# Human Setup and Approval Checklist

Antigravity should automate local code and tests wherever possible. These actions may require the user to sign in, approve, or provide access.

## Potential human actions
- Create/select the GitHub repository and approve pushes if required.
- Sign in to the chosen hosting platform.
- Authorize the hosting platform to read the repository.
- Choose the deployment repository, branch, and entry-point file.
- Confirm that the selected dataset/license is acceptable if using a non-synthetic public dataset.
- Provide any database credentials only through the approved secret manager if PostgreSQL is enabled.
- Review the final public URL and approve any resume wording.

## Defaults that avoid blockers
- Use deterministic synthetic sample data for the MVP.
- Do not require API keys or external AI services.
- Do not require a database service for the MVP if provisioning would threaten the deadline.
- Use public repository visibility only if the user agrees and no sensitive content is present.
- Do not perform purchases, create supplier orders, or send external communications.

## Record in release report
For each manual step, record the exact action needed, current status, and whether it blocks deployment. Never state that an account was connected or deployment completed unless verified.
