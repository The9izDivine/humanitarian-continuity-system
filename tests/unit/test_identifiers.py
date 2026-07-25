import pytest

from src.identifiers import IdentifierError, IdentifierGenerator


def test_identifiers_are_deterministic() -> None:
    generator = IdentifierGenerator()

    assert generator.next("incident") == "INC-000001"
    assert generator.next("incident") == "INC-000002"
    assert generator.next("volunteer") == "VOL-000001"


def test_peek_does_not_increment() -> None:
    generator = IdentifierGenerator()

    assert generator.peek("resource") == "RES-000001"
    assert generator.peek("resource") == "RES-000001"
    assert generator.next("resource") == "RES-000001"


def test_reset_one_counter() -> None:
    generator = IdentifierGenerator()

    generator.next("decision")
    generator.reset("decision")

    assert generator.next("decision") == "DEC-000001"


def test_unknown_object_type_fails_closed() -> None:
    generator = IdentifierGenerator()

    with pytest.raises(IdentifierError):
        generator.next("unsupported")