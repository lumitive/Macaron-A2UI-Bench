from __future__ import annotations

from protocol.types import ProtocolStack, ProtocolVersion


def get_protocol_stack(version: str) -> ProtocolStack:
    if version == "0.8":
        from protocol.v0_8 import build_stack

        return build_stack()
    if version == "0.9.1":
        from protocol.v0_9_1 import build_stack

        return build_stack()
    raise ValueError(f"Unsupported protocol version: {version!r}")


__all__ = ["ProtocolStack", "ProtocolVersion", "get_protocol_stack"]
