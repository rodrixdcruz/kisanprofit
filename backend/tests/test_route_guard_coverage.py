"""Fail-closed coverage check for the demo read-only guard.

`require_writable_user` is applied per route, so a newly added mutating route
that forgets the dependency would silently reopen the demo to writes. This
walks the real app and refuses to let that happen quietly: every non-GET route
must either carry the guard or be listed below with a reason.

Deliberately two-way — a stale allowlist entry (a route that was renamed or
deleted) also fails, so the list cannot rot into a rubber stamp.
"""
import pytest

from app.main import app

MUTATING = {"POST", "PUT", "PATCH", "DELETE"}
GUARD = "require_writable_user"

# Mutating routes a demo visitor may still hit, because they either touch only
# that visitor's own ephemeral state or persist nothing at all:
#   auth/*            — logging in, registering, switching UI language
#   ai/chat           — writes a conversation row; the walkthrough asks Kisan AI
#   notifications/*   — marking *your own* alerts read
#   ocr/receipt       — returns a prefill for the user to confirm, saves nothing
#   analytics/simulator, location/geocode — pure computation / lookup
#   admin/reseed-demo — cron-only, token-guarded, no user context
DEMO_ALLOWED = {
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/register"),
    ("POST", "/api/auth/demo-login"),  # read-only demo session; throttled
    ("PUT", "/api/auth/language"),
    ("POST", "/api/ai/chat"),
    ("POST", "/api/notifications/{notification_id}/read"),
    ("POST", "/api/notifications/read-all"),
    ("POST", "/api/ocr/receipt"),
    ("POST", "/api/analytics/simulator/{crop_id}"),
    ("POST", "/api/location/geocode"),
    ("POST", "/api/admin/reseed-demo"),
}


def _dependant_tree(route):
    """Every dependency attached to a route, however deeply nested."""
    dep = getattr(route, "dependant", None)
    stack = list(dep.dependencies) if dep else []
    while stack:
        node = stack.pop()
        yield node
        stack.extend(node.dependencies)


def _mutating_routes():
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if not methods:
            continue
        for method in sorted(set(methods) & MUTATING):
            yield method, getattr(route, "path", ""), route


def _is_guarded(route) -> bool:
    return any(getattr(d.call, "__name__", "") == GUARD for d in _dependant_tree(route))


def test_every_mutating_route_is_guarded_or_explicitly_allowed():
    unguarded = [
        (method, path)
        for method, path, route in _mutating_routes()
        if not _is_guarded(route) and (method, path) not in DEMO_ALLOWED
    ]
    assert not unguarded, (
        "These mutating routes are neither guarded nor allowlisted — the demo "
        f"account could write through them: {unguarded}"
    )


def test_allowlist_has_no_stale_entries():
    live = {(method, path) for method, path, _ in _mutating_routes()}
    stale = DEMO_ALLOWED - live
    assert not stale, f"DEMO_ALLOWED lists routes that no longer exist: {stale}"


@pytest.mark.parametrize("method,path", sorted(
    {("POST", "/api/farms"), ("PUT", "/api/farms/{farm_id}"),
     ("DELETE", "/api/farms/{farm_id}"), ("POST", "/api/farms/{farm_id}/crops"),
     ("DELETE", "/api/farms/{farm_id}/crops/{crop_id}"), ("POST", "/api/expenses"),
     ("PUT", "/api/expenses/{expense_id}"), ("DELETE", "/api/expenses/{expense_id}"),
     ("POST", "/api/crops/{crop_id}/production"), ("POST", "/api/crops/{crop_id}/sales")}
))
def test_farm_data_writes_are_guarded(method, path):
    """The routes that could actually corrupt the demo farm."""
    found = {(m, p): r for m, p, r in _mutating_routes()}
    route = found.get((method, path))
    assert route is not None, f"{method} {path} is missing from the app"
    assert _is_guarded(route), f"{method} {path} lost its {GUARD} dependency"
