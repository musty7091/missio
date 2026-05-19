from __future__ import annotations

import fnmatch
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

FORBIDDEN_TRACKED_PATTERNS = [
    ".env",
    "backend/.env",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.db-wal",
    "*.db-shm",
    "*.log",
    "ADIM_*.py",
    "ADIM_*.ps1",
    "__pycache__/*",
    "*.pyc",
    "uploads/*",
    "temp/*",
    "tmp/*",
    "logs/*",
    "backend/uploads/*",
    "backend/temp/*",
    "backend/tmp/*",
    "backend/logs/*",
]

REQUIRED_GITIGNORE_PATTERNS = [
    ".env",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.db-wal",
    "*.db-shm",
    "__pycache__/",
    "*.pyc",
    "/ADIM_*.py",
    "/ADIM_*.ps1",
    "uploads/",
    "temp/",
    "tmp/",
    "logs/",
]

REQUIRED_PROJECT_FILES = [
    "README.md",
    ".gitignore",
    ".github/workflows/security-gate.yml",
    "docs/SECURITY_CHECKLIST.md",
    "docs/SECURITY_GATE.md",
    "docs/API_SECURITY.md",
    "docs/CI_SECURITY_GATE.md",
    "docs/DEPENDENCY_SECURITY.md",
    "backend/requirements.txt",
    "backend/alembic.ini",
    "backend/app/main.py",
    "backend/app/commands/check_security_gate.py",
]


@dataclass(frozen=True)
class RepoHygieneResult:
    """Single repository hygiene check result."""

    name: str
    status: str
    message: str


def run_git_command(args: list[str]) -> list[str]:
    """Run git command from project root and return output lines."""

    completed_process = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if completed_process.returncode != 0:
        raise RuntimeError(
            "Git komutu çalıştırılamadı: "
            + " ".join(["git", *args])
            + "\n"
            + completed_process.stderr.strip()
        )

    return [
        line.strip().replace("\\", "/")
        for line in completed_process.stdout.splitlines()
        if line.strip()
    ]


def get_tracked_files() -> list[str]:
    """Return git tracked files."""

    return run_git_command(["ls-files"])


def is_forbidden_tracked_file(path: str) -> bool:
    """Return whether tracked file path matches forbidden patterns."""

    normalized_path = path.strip().replace("\\", "/")

    for pattern in FORBIDDEN_TRACKED_PATTERNS:
        if fnmatch.fnmatch(normalized_path, pattern):
            return True

        if pattern.endswith("/*"):
            folder_prefix = pattern[:-1]
            if normalized_path.startswith(folder_prefix):
                return True

    return False


def check_forbidden_tracked_files() -> RepoHygieneResult:
    """Ensure secrets, local DBs and generated files are not tracked."""

    tracked_files = get_tracked_files()
    forbidden_files = sorted(
        path for path in tracked_files if is_forbidden_tracked_file(path)
    )

    if forbidden_files:
        return RepoHygieneResult(
            name="forbidden_tracked_files",
            status="FAIL",
            message="Takip edilen yasaklı dosyalar: " + ", ".join(forbidden_files),
        )

    return RepoHygieneResult(
        name="forbidden_tracked_files",
        status="OK",
        message="Git tarafından takip edilen yasaklı dosya bulunmadı.",
    )


def check_gitignore_patterns() -> RepoHygieneResult:
    """Ensure .gitignore contains required protection patterns."""

    gitignore_path = PROJECT_ROOT / ".gitignore"

    if not gitignore_path.exists():
        return RepoHygieneResult(
            name="gitignore",
            status="FAIL",
            message=".gitignore dosyası bulunamadı.",
        )

    content = gitignore_path.read_text(encoding="utf-8")
    missing_patterns = [
        pattern
        for pattern in REQUIRED_GITIGNORE_PATTERNS
        if pattern not in content
    ]

    if missing_patterns:
        return RepoHygieneResult(
            name="gitignore",
            status="FAIL",
            message="Eksik .gitignore kuralları: " + ", ".join(missing_patterns),
        )

    return RepoHygieneResult(
        name="gitignore",
        status="OK",
        message=".gitignore temel koruma kuralları mevcut.",
    )


def check_required_project_files() -> RepoHygieneResult:
    """Ensure important project files exist."""

    missing_files = [
        relative_path
        for relative_path in REQUIRED_PROJECT_FILES
        if not (PROJECT_ROOT / relative_path).exists()
    ]

    if missing_files:
        return RepoHygieneResult(
            name="required_project_files",
            status="FAIL",
            message="Eksik proje dosyaları: " + ", ".join(missing_files),
        )

    return RepoHygieneResult(
        name="required_project_files",
        status="OK",
        message="Zorunlu proje, güvenlik ve CI dosyaları mevcut.",
    )


def check_requirements_file() -> RepoHygieneResult:
    """Ensure requirements file does not contain removed dependency."""

    requirements_path = PROJECT_ROOT / "backend" / "requirements.txt"

    if not requirements_path.exists():
        return RepoHygieneResult(
            name="requirements",
            status="FAIL",
            message="backend/requirements.txt bulunamadı.",
        )

    content = requirements_path.read_text(encoding="utf-8").lower()

    if "passlib" in content:
        return RepoHygieneResult(
            name="requirements",
            status="FAIL",
            message="requirements.txt içinde passlib kalmış.",
        )

    if "bcrypt==" not in content:
        return RepoHygieneResult(
            name="requirements",
            status="FAIL",
            message="requirements.txt içinde sabitlenmiş bcrypt paketi bulunamadı.",
        )

    return RepoHygieneResult(
        name="requirements",
        status="OK",
        message="requirements.txt dependency hijyen kontrolü başarılı.",
    )


def check_workflow_file() -> RepoHygieneResult:
    """Ensure GitHub Actions security gate workflow is present and meaningful."""

    workflow_path = PROJECT_ROOT / ".github" / "workflows" / "security-gate.yml"

    if not workflow_path.exists():
        return RepoHygieneResult(
            name="github_actions",
            status="FAIL",
            message="security-gate.yml workflow dosyası bulunamadı.",
        )

    content = workflow_path.read_text(encoding="utf-8")

    required_fragments = [
        "python -m alembic upgrade head",
        "python -m app.commands.seed_database",
        "python -m app.commands.check_security_gate",
    ]
    missing_fragments = [
        fragment
        for fragment in required_fragments
        if fragment not in content
    ]

    if missing_fragments:
        return RepoHygieneResult(
            name="github_actions",
            status="FAIL",
            message="Workflow içinde eksik komutlar: " + ", ".join(missing_fragments),
        )

    return RepoHygieneResult(
        name="github_actions",
        status="OK",
        message="GitHub Actions security gate workflow kontrolü başarılı.",
    )


def run_repo_hygiene_checks() -> list[RepoHygieneResult]:
    """Run all repository hygiene checks."""

    return [
        check_forbidden_tracked_files(),
        check_gitignore_patterns(),
        check_required_project_files(),
        check_requirements_file(),
        check_workflow_file(),
    ]


def main() -> None:
    """Run repository hygiene and secret leak checks."""

    print("Missio repository hijyen kontrolü başlıyor.")
    print(f"Proje kökü: {PROJECT_ROOT}")

    results = run_repo_hygiene_checks()

    print("")

    for result in results:
        print(f"[{result.status}] {result.name}: {result.message}")

    print("")

    if any(result.status == "FAIL" for result in results):
        print("Repository hijyen kontrolü başarısız.")
        sys.exit(1)

    print("Repository hijyen kontrolü başarılı.")


if __name__ == "__main__":
    main()
