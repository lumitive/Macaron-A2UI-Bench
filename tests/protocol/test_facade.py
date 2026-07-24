import pytest

from protocol import get_protocol_stack


def test_rejects_unknown_version():
    with pytest.raises(ValueError, match="Unsupported protocol version"):
        get_protocol_stack("1.0")


def test_accepts_0_8_and_0_9_1_keys():
    # Stacks may be incomplete early; keys must resolve without ValueError.
    s08 = get_protocol_stack("0.8")
    s091 = get_protocol_stack("0.9.1")
    assert s08.version == "0.8"
    assert s091.version == "0.9.1"
    assert s091.strip_gt_a2ui is True
    assert s08.strip_gt_a2ui is False
    assert s091.catalog_id == (
        "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"
    )
