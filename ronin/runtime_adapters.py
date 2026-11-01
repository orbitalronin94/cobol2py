"""Small, explicit runtime adapters for the COBOL subset.

These helpers are intentionally not wired into the translator's default emission
path yet. Callers must opt in until differential fixtures cover the relevant PICs.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from typing import Mapping


class CobolOverflowError(ArithmeticError):
    """A value cannot be represented by the requested COBOL picture."""


@dataclass(frozen=True)
class CobolDecimal:
    """Fixed-scale decimal value; default conversion truncates toward zero."""

    value: Decimal
    scale: int = 0
    digits: int | None = None
    signed: bool = True

    def __init__(self, value: object, scale: int = 0, digits: int | None = None,
                 signed: bool = True, rounded: bool = False):
        if scale < 0:
            raise ValueError("scale must be non-negative")
        if digits is not None and digits < 1:
            raise ValueError("digits must be positive")
        raw = value if isinstance(value, Decimal) else Decimal(str(value))
        quantum = Decimal(1).scaleb(-scale)
        mode = ROUND_HALF_UP if rounded else ROUND_DOWN
        fixed = raw.quantize(quantum, rounding=mode)
        if not signed and fixed < 0:
            raise CobolOverflowError("negative value for unsigned PIC")
        if digits is not None:
            integer_capacity = digits - scale
            if integer_capacity < 0 or abs(fixed) >= Decimal(10) ** integer_capacity:
                raise CobolOverflowError(f"{fixed} does not fit PIC with {digits} digits and scale {scale}")
        object.__setattr__(self, "value", fixed)
        object.__setattr__(self, "scale", scale)
        object.__setattr__(self, "digits", digits)
        object.__setattr__(self, "signed", signed)

    def __str__(self) -> str:
        return format(self.value, f".{self.scale}f")

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def _coerce(self, other: object) -> Decimal:
        return other.value if isinstance(other, CobolDecimal) else Decimal(str(other))

    def rescale(self, scale: int, *, rounded: bool = False) -> "CobolDecimal":
        return CobolDecimal(self.value, scale, self.digits, self.signed, rounded)

    def add(self, other: object, *, rounded: bool = False) -> "CobolDecimal":
        return CobolDecimal(self.value + self._coerce(other), self.scale, self.digits, self.signed, rounded)

    def subtract(self, other: object, *, rounded: bool = False) -> "CobolDecimal":
        return CobolDecimal(self.value - self._coerce(other), self.scale, self.digits, self.signed, rounded)

    def multiply(self, other: object, *, rounded: bool = False) -> "CobolDecimal":
        return CobolDecimal(self.value * self._coerce(other), self.scale, self.digits, self.signed, rounded)

    def divide(self, other: object, *, rounded: bool = False) -> "CobolDecimal":
        divisor = self._coerce(other)
        if divisor == 0:
            raise ZeroDivisionError("COBOL decimal division by zero")
        return CobolDecimal(self.value / divisor, self.scale, self.digits, self.signed, rounded)


@dataclass(frozen=True)
class CobolString:
    """Fixed-width alphanumeric value with COBOL-style right padding."""

    value: str
    width: int

    def __init__(self, value: object, width: int):
        if width < 0:
            raise ValueError("width must be non-negative")
        text = str(value)
        object.__setattr__(self, "value", text[:width].ljust(width))
        object.__setattr__(self, "width", width)

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return self.width

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CobolString):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return NotImplemented

    def collating_key(self, encoding: str = "cp037") -> bytes:
        """Return an explicit EBCDIC byte key; encoding failures are not hidden."""
        return self.value.encode(encoding)


class GroupView:
    """A fixed-size group view backed by a shared mutable bytearray.

    Field offsets are byte offsets, not character offsets. Use an encoding that
    matches the storage layout when decoding text fields.
    """

    def __init__(self, storage: bytearray, offset: int, length: int,
                 fields: Mapping[str, tuple[int, int]] | None = None):
        if offset < 0 or length < 0 or offset + length > len(storage):
            raise ValueError("group range lies outside shared storage")
        self._storage = storage
        self.offset = offset
        self.length = length
        self.fields = dict(fields or {})
        for name, (field_offset, field_length) in self.fields.items():
            if field_offset < 0 or field_length < 0 or field_offset + field_length > length:
                raise ValueError(f"field {name!r} lies outside group")

    @property
    def view(self) -> memoryview:
        return memoryview(self._storage)[self.offset:self.offset + self.length]

    def bytes(self) -> bytes:
        return self.view.tobytes()

    def read(self, name: str) -> bytes:
        offset, length = self.fields[name]
        return self.view[offset:offset + length].tobytes()

    def write(self, name: str, value: bytes) -> None:
        offset, length = self.fields[name]
        self.view[offset:offset + length] = bytes(value[:length]).ljust(length, b" ")

    def move_from(self, value: bytes | "GroupView") -> None:
        raw = value.bytes() if isinstance(value, GroupView) else bytes(value)
        self.view[:] = raw[:self.length].ljust(self.length, b" ")

    def __len__(self) -> int:
        return self.length
