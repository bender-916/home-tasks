# Security Policy

## ⚠️ Dependency Blacklist

### CRITICAL: `litellm` BANNED
**Status:** PERMANENTLY BLACKLISTED
**Reason:** Security vulnerability (CVE pending)
**Reference:** https://github.com/BerriAI/litellm/issues/24512

**DO NOT USE** `litellm` in any project. This library has a serious security vulnerability and must be avoided.

### Detection Script

Add this to CI/CD pipelines to detect banned dependencies:

```bash
#!/bin/bash
# check-banned-deps.sh

BANNED_DEPS=(
    "litellm"
    # Add future banned deps here
)

for dep in "${BANNED_DEPS[@]}"; do
    if grep -r "$dep" requirements*.txt pyproject.toml Pipfile 2>/dev/null; then
        echo "ERROR: Banned dependency '$dep' found!"
        echo "See SECURITY.md for details."
        exit 1
    fi
done

echo "No banned dependencies found."
```

### Repository Scan Results

| Repository | litellm Found | Status |
|------------|---------------|--------|
| home-tasks | ❌ NO | ✅ Safe |
| periodico-parodia | N/A (private) | ⚠️ Check manually |
| tf-diagram | N/A (Go) | ✅ Safe |

## Reporting Security Issues

If you discover banned dependencies or security vulnerabilities:
1. Do NOT use them
2. Report immediately
3. Check all projects for usage
