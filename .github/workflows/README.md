# GitHub Actions Workflows Guide

## Overview

This directory contains comprehensive CI/CD workflows for the omnisearch project:

### Workflows

1. **`ci-cd.yml`** - Main CI/CD pipeline (testing, linting, building)
2. **`security.yml`** - Security and code quality scanning
3. **`deploy.yml`** - Staging and production deployments

---

## 1. CI/CD Pipeline (`ci-cd.yml`)

Runs on every push to `main`/`develop` branches and all pull requests.

### Jobs

#### **Lint Job**
- **Tools**: Black, isort, Flake8, Pylint, Bandit
- **Runs**: Python 3.11
- **Checks**:
  - Code formatting (Black)
  - Import sorting (isort)
  - Style violations (Flake8)
  - Code quality (Pylint)
  - Security issues (Bandit)

```bash
# Manually run linting locally
black --check api/ services/ scripts/
isort --check-only api/ services/ scripts/
flake8 api/ services/ scripts/
pylint api/ services/ scripts/
bandit -r api/ services/ scripts/
```

#### **Test Job**
- **Services**: MongoDB 7.0, Weaviate 1.24.1
- **Framework**: pytest
- **Coverage**: Generated via pytest-cov
- **Uploads**: Coverage reports to Codecov

```bash
# Manually run tests locally
pytest tests/ -v --cov=api --cov=services
```

#### **Build Job**
- **Images**: Builds FastAPI and Embedding service containers
- **Registry**: GitHub Container Registry (ghcr.io)
- **Caching**: Enabled for faster builds
- **Pushes**: Only on main branch (not on PRs)

#### **Integration Job**
- **Services**: MongoDB, Weaviate
- **Tests**: Marks tests with `@pytest.mark.integration`
- **Runs**: After build completes

#### **Status Job**
- **Summarizes**: All job statuses
- **Generates**: Status report

### Triggers

```yaml
on:
  push:
    branches:
      - main
      - develop
      - feature/**
  pull_request:
    branches:
      - main
      - develop
  workflow_dispatch:  # Manual trigger
```

### Environment Variables

```env
REGISTRY: ghcr.io
IMAGE_NAME: ${{ github.repository }}
MONGODB_URL: mongodb://admin:password@localhost:27017
WEAVIATE_URL: http://localhost:8080
```

---

## 2. Security Workflows (`security.yml`)

Runs daily at 2 AM UTC, plus on every push to `main`/`develop`.

### Jobs

#### **Dependencies Job**
- **Tool**: pip-audit
- **Checks**: Vulnerabilities in dependencies
- **Lists**: Outdated packages

```bash
# Manually check
pip-audit --desc
pip list --outdated
```

#### **Security Scan (SAST) Job**
- **Tools**: Bandit, Semgrep
- **Checks**: Security vulnerabilities
- **Output**: JSON reports

```bash
# Manually scan
bandit -r api/ services/ scripts/ -f json
semgrep --config=p/security-audit api/ services/ scripts/
```

#### **Code Quality Job**
- **Tool**: Radon
- **Checks**:
  - Cyclomatic complexity (CC)
  - Maintainability index (MI)
  - Raw metrics (LOC, comments, etc.)

```bash
# Manually check
radon cc api/ services/ scripts/ -s
radon mi api/ services/ scripts/ -s
radon raw api/ services/ scripts/
```

#### **Container Security Scan Job**
- **Tool**: Trivy
- **Scans**: Docker images for vulnerabilities
- **Output**: SARIF format (integrates with GitHub Security tab)

#### **Type Checking Job**
- **Tool**: mypy
- **Checks**: Static type errors

```bash
# Manually check
mypy api/ services/ scripts/ --ignore-missing-imports
```

---

## 3. Deployment Workflows (`deploy.yml`)

Runs on tags (`v*`) or manual workflow dispatch.

### Jobs

#### **Build Job**
- **Builds**: Both FastAPI and Embedding images
- **Pushes**: To GitHub Container Registry
- **Outputs**: Image names/tags for downstream jobs

#### **Deploy to Staging Job**
- **Trigger**: On develop branch or manual staging input
- **Environment**: Staging
- **Tasks**:
  - Deploy images
  - Run health checks
  - Notify on success

#### **Deploy to Production Job**
- **Trigger**: On tags (e.g., `v1.0.0`)
- **Environment**: Production (requires approval)
- **Tasks**:
  - Create GitHub deployment
  - Deploy images
  - Update deployment status
  - Notify on success/failure

#### **Smoke Tests Job**
- **Runs after**: Staging deployment
- **Tests**: `tests/smoke/` directory
- **Checks**: Basic API functionality

#### **Notifications Job**
- **Sends**: Slack notifications
- **Status**: Success or failure message
- **Requires**: `SLACK_WEBHOOK_URL` secret

---

## Setup Instructions

### Prerequisites

1. **GitHub Repository**
   - Create `.github/workflows/` directory
   - Place workflow files in this directory

2. **GitHub Secrets** (Settings → Secrets and variables → Actions)
   ```
   SLACK_WEBHOOK_URL     (optional, for notifications)
   ```

3. **GitHub Environments** (Settings → Environments)
   - Create `staging` environment
   - Create `production` environment (add approval requirements)

### Configuration

#### 1. Update Container Registry

Edit workflows to use your registry:

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
```

#### 2. Configure Deployment Targets

Update deployment steps to match your infrastructure:

```yaml
# For Kubernetes
kubectl set image deployment/fastapi fastapi=${{ needs.build.outputs.fastapi-image }} -n staging

# For Docker Compose
docker-compose -f docker-compose.staging.yml up -d

# For other platforms
# Add your deployment commands here
```

#### 3. Add Slack Notifications (Optional)

1. Create Slack incoming webhook: https://api.slack.com/messaging/webhooks
2. Add to GitHub secrets as `SLACK_WEBHOOK_URL`
3. Workflows will automatically send notifications

#### 4. Configure Branch Protections

GitHub Settings → Branches → Add branch protection rule:

- Require status checks to pass before merging
- Require code reviews
- Require branches to be up to date
- Require deployments to succeed

---

## Usage

### Automatic Triggers

```yaml
# On every push to main/develop
- Lint check
- Unit tests
- Docker build
- Integration tests

# Daily at 2 AM UTC (security.yml)
- Dependency scan
- Security scan
- Code quality check
- Container scan
- Type checking

# On tag push (v*)
- Build images
- Deploy to production
- Run smoke tests
- Send notifications
```

### Manual Triggers

```bash
# Trigger CI/CD pipeline manually
GitHub Actions tab → ci-cd → Run workflow → Select branch

# Trigger deployment manually
GitHub Actions tab → deploy → Run workflow → Select environment
```

### Monitoring

1. **GitHub Actions Tab**: View workflow runs and logs
2. **Pull Requests**: See check status and logs
3. **Commits**: See build status badge on commits

---

## Troubleshooting

### Common Issues

#### 1. Tests Failing

Check test logs in GitHub Actions:

```bash
# View recent workflow run
gh workflow view ci-cd.yml --log

# Run tests locally
pytest tests/ -v --tb=short
```

#### 2. Docker Build Failing

```bash
# Check Dockerfile syntax locally
docker build -f Dockerfile --no-cache .

# View build logs in GitHub Actions
# GitHub Actions → ci-cd → build job → "Build and push FastAPI image"
```

#### 3. Deployment Failing

```bash
# Check deployment status
gh deployment list

# View deployment logs
gh run list --workflow=deploy.yml

# Check environment secrets
GitHub Settings → Environments → [environment] → Repository secrets
```

#### 4. Security Scan Issues

- Bandit: Review findings and add `# nosec` for false positives
- Semgrep: Configure rules in `.semgrep.yml`
- Trivy: Add `TRIVY_IGNORE` file for accepted vulnerabilities

### Debug Mode

Add `debug: true` to any step:

```yaml
- name: Debug step
  run: echo "Debug info"
  env:
    DEBUG: true
```

---

## Best Practices

### 1. Linting

```bash
# Before committing, run locally
black api/ services/ scripts/
isort api/ services/ scripts/
```

### 2. Testing

```bash
# Write tests in tests/ directory
# Use pytest markers for categorization
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.smoke
```

### 3. Commits

Follow conventional commits:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
test: Add tests
perf: Improve performance
```

### 4. Pull Requests

- Enable auto-merge after checks pass
- Request reviews from team
- Add labels (bug, feature, docs, etc.)

### 5. Versioning

Use semantic versioning for tags:

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

---

## Performance Optimization

### 1. Cache Strategy

Workflows use multiple caching strategies:

```yaml
cache: 'pip'  # Cache pip packages
cache-from: type=registry,ref=${{ ... }}  # Docker layer cache
```

### 2. Parallel Execution

Jobs run in parallel when possible:

- `lint` and `test` run simultaneously
- `build` waits for `lint` and `test`
- `integration` waits for `build`

### 3. Conditional Steps

Only run expensive steps when needed:

```yaml
if: github.event_name != 'pull_request'  # Only on push
continue-on-error: true  # Don't fail workflow on optional steps
```

---

## Integration with Other Tools

### 1. Codecov Coverage

Coverage reports automatically uploaded:

```
https://codecov.io/gh/[owner]/[repo]
```

### 2. GitHub Security

SARIF reports from Trivy integrated into:

```
GitHub → Security → Code scanning alerts
```

### 3. Slack Notifications

Deployment notifications sent to Slack channel

### 4. GitHub Deployments

Track deployments in GitHub:

```
GitHub → Deployments → View all deployments
```

---

## Workflow Files Checklist

- ✅ `.github/workflows/ci-cd.yml` - Main CI/CD pipeline
- ✅ `.github/workflows/security.yml` - Security and quality scanning
- ✅ `.github/workflows/deploy.yml` - Deployment workflows

---

## Example: Running a Complete Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# ... edit files ...

# 3. Commit with message
git add .
git commit -m "feat: Add my feature"

# 4. Push to GitHub
git push origin feature/my-feature

# GitHub Actions automatically:
# → Lints code
# → Runs tests
# → Builds Docker images
# → Runs integration tests
# → Posts results on PR

# 5. Review results on GitHub → Pull requests → [PR] → Checks tab

# 6. Merge when all checks pass
git merge feature/my-feature

# GitHub Actions automatically:
# → Builds final images
# → Pushes to registry
# → Deploys to staging

# 7. Create release tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# GitHub Actions automatically:
# → Builds images
# → Deploys to production
# → Sends Slack notification
```

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Available Actions](https://github.com/marketplace?type=actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://github.com/psf/black)
- [Flake8 Linter](https://flake8.pycqa.org/)
- [Bandit Security](https://bandit.readthedocs.io/)

---

## Support

For issues or questions:

1. Check GitHub Actions logs
2. Review workflow file syntax
3. Test commands locally
4. Check GitHub documentation

---

**Last Updated**: January 28, 2026
**Status**: Production Ready ✅
