from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import Any

from locust import HttpUser, between, task


DEFAULT_PASSWORD = os.getenv("MISSIO_LOAD_PASSWORD", "MissioLoad.2026!")
RUN_ID = os.getenv("MISSIO_LOAD_RUN_ID", "20260529153907")
BUSINESS_COUNT = int(os.getenv("MISSIO_LOAD_BUSINESS_COUNT", "15"))
STAFF_COUNT = int(os.getenv("MISSIO_LOAD_STAFF_COUNT", "12"))
MANAGER_COUNT = int(os.getenv("MISSIO_LOAD_MANAGER_COUNT", "2"))
ROLE_FILTER = os.getenv("MISSIO_LOAD_ROLE", "all").strip().lower()


@dataclass(frozen=True)
class TestAccount:
    business_slug: str
    username: str
    password: str
    role: str


def build_accounts() -> list[TestAccount]:
    accounts: list[TestAccount] = []

    for business_index in range(1, BUSINESS_COUNT + 1):
        business_no = f"{business_index:03d}"
        business_slug = f"load-test-{RUN_ID}-{business_no}"

        if ROLE_FILTER in {"all", "boss", "patron"}:
            accounts.append(
                TestAccount(
                    business_slug=business_slug,
                    username=f"boss{business_no}",
                    password=DEFAULT_PASSWORD,
                    role="boss",
                )
            )

        if ROLE_FILTER in {"all", "manager", "yonetici", "yönetici"}:
            for manager_index in range(1, MANAGER_COUNT + 1):
                accounts.append(
                    TestAccount(
                        business_slug=business_slug,
                        username=f"manager{business_no}{manager_index:02d}",
                        password=DEFAULT_PASSWORD,
                        role="manager",
                    )
                )

        if ROLE_FILTER in {"all", "staff", "personel"}:
            for staff_index in range(1, STAFF_COUNT + 1):
                accounts.append(
                    TestAccount(
                        business_slug=business_slug,
                        username=f"staff{business_no}{staff_index:02d}",
                        password=DEFAULT_PASSWORD,
                        role="staff",
                    )
                )

    if not accounts:
        raise RuntimeError(
            "Test kullanıcı listesi boş. MISSIO_LOAD_ROLE değerini kontrol et. "
            "Geçerli değerler: all, boss, manager, staff"
        )

    return accounts


ACCOUNTS = build_accounts()


class MissioReadOnlyUser(HttpUser):
    wait_time = between(0.5, 2.0)

    access_token: str | None = None
    account: TestAccount | None = None

    def on_start(self) -> None:
        self.account = random.choice(ACCOUNTS)
        self.login()

    def auth_headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    def login(self) -> None:
        assert self.account is not None

        payload = {
            "business_slug": self.account.business_slug,
            "username": self.account.username,
            "password": self.account.password,
        }

        with self.client.post(
            "/api/v1/auth/login",
            json=payload,
            name="POST /api/v1/auth/login",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Login failed for {self.account.username} / "
                    f"{self.account.business_slug}: HTTP {response.status_code} {response.text[:300]}"
                )
                self.access_token = None
                return

            try:
                data: dict[str, Any] = response.json()
            except Exception as exc:
                response.failure(f"Login JSON parse failed: {exc}")
                self.access_token = None
                return

            token = data.get("access_token")
            if not token:
                response.failure(f"Login response has no access_token: {data}")
                self.access_token = None
                return

            self.access_token = str(token)
            response.success()

    def ensure_logged_in(self) -> bool:
        if self.access_token:
            return True

        self.login()
        return self.access_token is not None

    @task(4)
    def read_my_today_tasks(self) -> None:
        if not self.ensure_logged_in():
            return

        self.client.get(
            "/api/v1/tasks/my-today",
            headers=self.auth_headers(),
            name="GET /api/v1/tasks/my-today",
        )

    @task(3)
    def read_tasks_list(self) -> None:
        if not self.ensure_logged_in():
            return

        self.client.get(
            "/api/v1/tasks",
            params={"limit": 100},
            headers=self.auth_headers(),
            name="GET /api/v1/tasks?limit=100",
        )

    @task(2)
    def read_me(self) -> None:
        if not self.ensure_logged_in():
            return

        self.client.get(
            "/api/v1/auth/me",
            headers=self.auth_headers(),
            name="GET /api/v1/auth/me",
        )


    @task(1)
    def read_pending_location_checks(self) -> None:
        if not self.ensure_logged_in():
            return

        self.client.get(
            "/api/v1/location-checks/my-pending",
            headers=self.auth_headers(),
            name="GET /api/v1/location-checks/my-pending",
        )

    @task(1)
    def occasionally_relogin(self) -> None:
        self.login()
