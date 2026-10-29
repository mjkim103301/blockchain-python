"""지갑 — 개인키 · 공개키 · 주소.

지갑에는 코인이 들어있지 않다. 들어있는 건 **개인키 하나**뿐이고,
잔액은 체인 위에 기록되어 있다. 개인키를 잃으면 체인 위의 내 돈을
움직일 방법이 사라지는 것이지, 돈이 지갑에서 없어지는 게 아니다.
"""

from __future__ import annotations

from typing import Optional, Tuple

import crypto


class Wallet:
    """개인키 하나에서 공개키와 주소가 파생된다. 거꾸로는 불가능하다.

        개인키(정수)  ──곱셈──▶  공개키(곡선 위의 점)  ──해시──▶  주소
           비밀              공유 가능                  공유 가능
    """

    def __init__(self, private_key: Optional[int] = None, label: str = "") -> None:
        self.private_key = private_key if private_key is not None else crypto.generate_private_key()
        self.public_key = crypto.private_to_public(self.private_key)
        self.label = label

    # ------------------------------------------------------------ 주소

    @staticmethod
    def address_from_public_key(public_key) -> str:
        """공개키 → 주소. SHA-256 후 RIPEMD-160 으로 20바이트까지 줄인다."""
        serialized = crypto.serialize_public_key(public_key)
        digest = crypto.ripemd160(crypto.sha256(serialized))
        return "1x" + digest.hex()

    @property
    def address(self) -> str:
        return self.address_from_public_key(self.public_key)

    @property
    def public_key_hex(self) -> str:
        return crypto.serialize_public_key(self.public_key).hex()

    # ------------------------------------------------------------ 서명

    def sign(self, message_hash: bytes) -> Tuple[int, int]:
        return crypto.sign(message_hash, self.private_key)

    @staticmethod
    def verify(message_hash: bytes, signature: Tuple[int, int], public_key_hex: str) -> bool:
        """공개키만으로 검증한다. 검증하는 쪽은 개인키를 영원히 알 수 없다."""
        public_key = Wallet.public_key_from_hex(public_key_hex)
        return crypto.verify(message_hash, signature, public_key)

    # ------------------------------------------------------- 직렬화

    @staticmethod
    def public_key_from_hex(raw: str):
        """압축 공개키(33바이트)를 점으로 되돌린다.

        x 만 있고 y 는 홀짝 1비트만 저장돼 있으므로, 곡선식에 x 를 넣어
        y² = x³ + 7 을 풀고 홀짝이 맞는 쪽을 고른다.
        """
        data = bytes.fromhex(raw)

        if len(data) == 65 and data[0] == 0x04:
            return (
                int.from_bytes(data[1:33], "big"),
                int.from_bytes(data[33:], "big"),
            )

        if len(data) != 33 or data[0] not in (0x02, 0x03):
            raise ValueError("압축 공개키는 02/03 으로 시작하는 33바이트여야 합니다.")

        x = int.from_bytes(data[1:], "big")
        y_squared = (pow(x, 3, crypto.P) + crypto.B) % crypto.P

        # P % 4 == 3 이라 제곱근을 지수 연산 한 번으로 구할 수 있다.
        y = pow(y_squared, (crypto.P + 1) // 4, crypto.P)
        if (y * y - y_squared) % crypto.P != 0:
            raise ValueError("곡선 위의 점이 아닙니다.")

        want_odd = data[0] == 0x03
        if bool(y & 1) != want_odd:
            y = crypto.P - y

        return (x, y)

    def export_private_key(self) -> str:
        """백업용. 이 문자열이 곧 돈이므로 절대 공유하면 안 된다."""
        return self.private_key.to_bytes(32, "big").hex()

    @classmethod
    def from_private_key_hex(cls, raw: str, label: str = "") -> "Wallet":
        return cls(int(raw, 16), label=label)

    def __repr__(self) -> str:
        name = f" {self.label}" if self.label else ""
        return "<Wallet{} {}>".format(name, self.address[:12] + "...")
