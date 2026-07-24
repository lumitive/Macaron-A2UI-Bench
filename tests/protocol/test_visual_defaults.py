"""Defaults and stack render_check selection for visual eval (0.8 / 0.9.1)."""

from __future__ import annotations

from protocol import get_protocol_stack
from visual_eval import default_render_url_for_protocol, select_targets_with_stack_render_check


def test_urls():
    assert default_render_url_for_protocol("0.8").endswith(":5173/")
    assert default_render_url_for_protocol("0.9.1").endswith(":5174/")


def test_v091_fixture_not_filtered_by_v08_rules():
    # Minimal createSurface + updateComponents with id=root must pass stack.render_check
    stack = get_protocol_stack("0.9.1")
    messages = [
        {
            "version": "v0.9.1",
            "createSurface": {
                "surfaceId": "main",
                "catalogId": "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json",
            },
        },
        {
            "version": "v0.9.1",
            "updateComponents": {
                "surfaceId": "main",
                "components": [
                    {"id": "root", "component": "Text", "text": "Hello"},
                ],
            },
        },
    ]
    ok, issues = stack.render_check(messages)
    assert ok, issues
    # Shared helper must use the same stack render_check (not root 0.8 rules).
    helper_ok, helper_issues = select_targets_with_stack_render_check(
        messages, protocol_version="0.9.1"
    )
    assert helper_ok, helper_issues
