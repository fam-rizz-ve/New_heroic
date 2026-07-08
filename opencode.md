=========================================================
VERSION CONTROL & CI/CD
=========================================================

The project must use Git and GitHub from the very beginning.

After every completed feature or milestone:

1. Update all related documentation.
2. Run all local tests.
3. Run linting.
4. Run formatting checks.
5. Run type checking.
6. Verify the application builds successfully.
7. Create a meaningful git commit following Conventional Commits.
8. Push the changes to GitHub automatically.

After every push:

1. Monitor all GitHub Actions workflows.
2. Wait until every workflow has completed.
3. Analyze every failed workflow.
4. Read the logs.
5. Determine the root cause.
6. Fix the problem automatically.
7. Commit the fix.
8. Push again.
9. Repeat until every GitHub Action passes successfully.

=========================================================
CONTINUOUS IMPROVEMENT
=========================================================

Continuously improve the CI/CD pipeline.

When new functionality is added:

- add new unit tests
- add new integration tests
- add regression tests
- add performance tests when useful
- improve existing GitHub Actions workflows
- remove duplicated workflow steps
- optimize build times
- improve caching
- improve security checks

Never leave a new feature without adequate automated tests.

=========================================================
TESTING STRATEGY
=========================================================

Every feature must include:

- Unit tests
- Integration tests
- Regression tests (when applicable)

Every bug that is fixed must first be reproduced by creating a failing test.

After the fix:

- verify that the new test passes
- verify that all previous tests still pass

=========================================================
GITHUB ACTIONS
=========================================================

Design a professional CI/CD pipeline.

Automatically create and maintain workflows for:

- Build
- Test
- Lint
- Type checking
- Security scanning
- Dependency auditing
- Packaging
- Release validation

Continuously improve these workflows during the project.

If additional automated checks would improve software quality, implement them without being asked.

=========================================================
QUALITY GATE
=========================================================

A feature is considered COMPLETE only if:

✓ Code is implemented.
✓ Documentation is updated.
✓ Local tests pass.
✓ GitHub Actions pass.
✓ Packaging succeeds.
✓ No lint errors remain.
✓ No type errors remain.
✓ No security issues are introduced.
✓ Code review passes.
✓ The project is pushed to GitHub.

Only then proceed to the next feature.
