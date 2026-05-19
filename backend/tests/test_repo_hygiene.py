from app.commands import check_repo_hygiene


def test_forbidden_patterns_include_local_sensitive_files() -> None:
    patterns = check_repo_hygiene.FORBIDDEN_TRACKED_PATTERNS

    assert ".env" in patterns
    assert "backend/.env" in patterns
    assert "*.db" in patterns
    assert "ADIM_*.py" in patterns
    assert "__pycache__/*" in patterns


def test_required_gitignore_patterns_include_helper_scripts() -> None:
    patterns = check_repo_hygiene.REQUIRED_GITIGNORE_PATTERNS

    assert "/ADIM_*.py" in patterns
    assert "/ADIM_*.ps1" in patterns
    assert ".env" in patterns


def test_forbidden_file_matching() -> None:
    assert check_repo_hygiene.is_forbidden_tracked_file(".env")
    assert check_repo_hygiene.is_forbidden_tracked_file("backend/.env")
    assert check_repo_hygiene.is_forbidden_tracked_file("missio_local.db")
    assert check_repo_hygiene.is_forbidden_tracked_file("ADIM_5A_test.py")
    assert check_repo_hygiene.is_forbidden_tracked_file("backend/logs/app.log")
    assert not check_repo_hygiene.is_forbidden_tracked_file("backend/app/main.py")


def test_required_project_files_contains_security_docs() -> None:
    required_files = check_repo_hygiene.REQUIRED_PROJECT_FILES

    assert "docs/SECURITY_CHECKLIST.md" in required_files
    assert "docs/SECURITY_GATE.md" in required_files
    assert "docs/API_SECURITY.md" in required_files
    assert ".github/workflows/security-gate.yml" in required_files
