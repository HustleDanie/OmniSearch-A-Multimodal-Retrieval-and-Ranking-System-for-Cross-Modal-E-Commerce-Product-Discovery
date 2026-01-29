# GitHub Actions CI/CD - Quick Start Guide

## For Developers

### Before Committing

```bash
# 1. Run linting locally
black api/ services/ scripts/
isort api/ services/ scripts/
flake8 api/ services/ scripts/

# 2. Run tests locally
pytest tests/ -v

# 3. Type check (optional)
mypy api/ services/

# 4. Commit and push
git add .
git commit -m "feat: Add my feature"
git push origin my-branch
```

### Creating a Pull Request

1. Push to your feature branch
2. Create Pull Request on GitHub
3. GitHub Actions automatically:
   - Runs linting checks
   - Runs unit tests
   - Builds Docker images
   - Runs integration tests
4. Review results in "Checks" tab
5. Merge when all checks pass

### Understanding Workflow Status

- ✅ **Green checkmark**: All checks passed, safe to merge
- ❌ **Red X**: Some checks failed, review logs to fix
- ⏳ **Yellow circle**: Checks still running

---

## For DevOps/Infrastructure

### Deploying to Staging

```bash
# Automatic on develop branch push
git push origin develop

# Or manual trigger
GitHub Actions → deploy → Run workflow → Select staging
```

### Deploying to Production

```bash
# Create and push a version tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Or manual trigger
GitHub Actions → deploy → Run workflow → Select production
```

### Monitoring Deployments

```bash
# View deployment history
GitHub → Deployments

# View recent workflow runs
GitHub Actions → View all workflows

# Check deployment status
gh deployment list
```

---

## Common Commands

### View Workflow Status

```bash
# List all workflows
gh workflow list

# View recent runs
gh run list --workflow=ci-cd.yml

# View specific run logs
gh run view <run-id> --log

# View pull request checks
gh pr checks <pr-number>
```

### Retry Failed Workflows

```bash
# Retry specific failed job
gh run rerun <run-id>

# Retry with logs
gh run rerun <run-id> --failed
```

### View Test Results

```bash
# Download test artifacts
gh run download <run-id>

# View coverage report
cat coverage.xml
```

---

## Troubleshooting

### Linting Failures

**Issue**: Flake8 or Black failed

**Solution**:
```bash
# Fix formatting
black api/ services/ scripts/

# Fix import order
isort api/ services/ scripts/

# Check what needs fixing
flake8 api/ services/ scripts/

# Commit fixes
git add .
git commit -m "style: Fix linting issues"
git push
```

### Test Failures

**Issue**: pytest tests failed

**Solution**:
```bash
# Run tests locally
pytest tests/ -v --tb=short

# Run specific test
pytest tests/test_ab_testing.py::test_something -v

# Run with coverage
pytest tests/ --cov=api --cov=services

# Check GitHub Actions logs for full error
```

### Docker Build Failure

**Issue**: Docker image build failed

**Solution**:
```bash
# Test build locally
docker build -f Dockerfile --no-cache .

# Check for issues
docker build -f Dockerfile --progress=plain .

# View build logs in GitHub Actions
# GitHub Actions → ci-cd → build
```

### Deployment Failure

**Issue**: Deployment to staging/production failed

**Solution**:
```bash
# Check deployment logs
gh run view <run-id> --log

# Verify Docker images were built
docker images | grep omnisearch

# Check service status
curl https://staging.omnisearch.example.com/health
```

---

## Setting Up Your Development Environment

### 1. Install Required Tools

```bash
# Python and dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Dev tools for local checks
pip install black isort flake8 pylint mypy bandit

# Test runner
pip install pytest pytest-cov
```

### 2. Configure Git Hooks (Optional)

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
black --check api/ services/ scripts/ || exit 1
isort --check-only api/ services/ scripts/ || exit 1
flake8 api/ services/ scripts/ || exit 1
pytest tests/ -q || exit 1
EOF

chmod +x .git/hooks/pre-commit
```

### 3. Configure IDE

**VS Code** (settings.json):
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python"
  }
}
```

**PyCharm**:
- Settings → Tools → Python Integrated Tools → Default Test Runner → pytest
- Settings → Editor → Code Style → Line length: 120

---

## Workflow Execution Times

Typical workflow durations:

- **Linting**: ~2 minutes
- **Tests**: ~5 minutes (includes service startup)
- **Docker Build**: ~10 minutes (first time), ~2 minutes (cached)
- **Integration Tests**: ~3 minutes
- **Total CI/CD**: ~15-20 minutes

---

## Cost Optimization

GitHub Actions free tier includes:

- 2,000 minutes/month (public repos: unlimited)
- 500 MB storage
- Per-job timeout: 6 hours

**Tips**:
- Use caching to speed up builds
- Disable workflows on draft PRs
- Use conditional steps to skip unnecessary jobs
- Clean up old artifacts

---

## Security Best Practices

### 1. Secrets Management

```bash
# Add secrets in GitHub Settings
GitHub → Settings → Secrets and variables → Actions

# Use in workflows
env:
  SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 2. Token Permissions

```yaml
permissions:
  contents: read        # Don't modify repo
  packages: write       # Push Docker images
  checks: write         # Create check runs
```

### 3. Branch Protection

```
GitHub → Settings → Branches → Add rule

- Require status checks
- Require code review
- Dismiss stale reviews
- Require branches up to date
```

---

## Useful Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Actions Marketplace](https://github.com/marketplace?type=actions)
- [gh CLI Reference](https://cli.github.com/manual/)

---

## Quick Reference

```bash
# Development workflow
git checkout -b feature/my-feature      # Create feature branch
# ... make changes ...
black api/ services/ scripts/           # Format code
isort api/ services/ scripts/           # Fix imports
pytest tests/ -v                        # Run tests
git add .                               # Stage changes
git commit -m "feat: ..."               # Commit
git push origin feature/my-feature      # Push

# On GitHub: Create PR, wait for checks, merge

# Release workflow
git tag -a v1.0.0 -m "Release v1.0.0"  # Create tag
git push origin v1.0.0                  # Trigger deployment

# Check status
gh run list --workflow=ci-cd.yml        # View recent runs
gh deployment list                      # View deployments
```

---

**Status**: Ready to Use ✅
**Questions?** Check `.github/workflows/README.md` for detailed documentation
