"""해시와 타원곡선 서명.

secp256k1(비트코인·이더리움이 쓰는 곡선)을 외부 패키지 없이 직접 구현한다.
라이브러리를 쓰면 한 줄이지만, 그러면 "공개키는 개인키에서 어떻게 나오는가"를
영영 모르고 지나간다. 스터디 목적이라 일부러 펼쳐 둔다.

⚠️ 학습용이다. 실제 서비스에는 쓰지 말 것.
   - 상수시간 연산이 아니라 사이드채널 공격에 노출된다
   - 난수 k 를 secrets 로 뽑지만 RFC6979 결정적 서명이 더 안전하다
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Tuple

# ---------------------------------------------------------------- 해시

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256d(data: bytes) -> bytes:
    """이중 SHA-256. 비트코인이 블록·거래 해시에 쓰는 방식이다."""
    return sha256(sha256(data))


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ripemd160(data: bytes) -> bytes:
    """주소를 짧게 만들 때 쓴다. 없는 환경이면 SHA-256 앞 20바이트로 대체한다."""
    try:
        h = hashlib.new("ripemd160")
        h.update(data)
        return h.digest()
    except (ValueError, TypeError):
        # OpenSSL 3 에서 ripemd160 이 기본 비활성인 경우가 있다.
        return sha256(data)[:20]


# ------------------------------------------------- secp256k1 곡선 상수
#
#   곡선식:  y² = x³ + 7  (mod P)
#
# 개인키는 1 ~ N-1 사이의 정수 하나일 뿐이고,
# 공개키는 그 수만큼 기준점 G 를 더한 점이다. 거꾸로는 못 푼다(이산로그 문제).

P = 2 ** 256 - 2 ** 32 - 977
A = 0
B = 7
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
)

Point = Tuple[int, int]  # 무한원점은 None 으로 표현한다


def _inv(x: int, m: int) -> int:
    """모듈러 역원. 나눗셈 대신 쓴다."""
    return pow(x, m - 2, m)


def point_add(p1, p2):
    """타원곡선 위 두 점의 덧셈."""
    if p1 is None:
        return p2
    if p2 is None:
        return p1

    x1, y1 = p1
    x2, y2 = p2

    if x1 == x2 and (y1 + y2) % P == 0:
        return None  # 서로 역원이라 무한원점

    if p1 == p2:
        # 접선의 기울기
        lam = (3 * x1 * x1 + A) * _inv(2 * y1, P) % P
    else:
        lam = (y2 - y1) * _inv(x2 - x1, P) % P

    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)


def point_mul(k: int, point=G):
    """점을 k 번 더한다. double-and-add 로 O(log k) 에 끝낸다."""
    result = None
    addend = point

    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1

    return result


def is_on_curve(point) -> bool:
    if point is None:
        return True
    x, y = point
    return (y * y - x * x * x - A * x - B) % P == 0


# ---------------------------------------------------------------- 키

def generate_private_key() -> int:
    """1 ~ N-1 범위의 난수. 이게 전부다 — 개인키는 그냥 큰 정수 하나다."""
    return secrets.randbelow(N - 1) + 1


def private_to_public(private_key: int) -> Point:
    if not 1 <= private_key < N:
        raise ValueError("개인키는 1 이상 N 미만이어야 합니다.")
    return point_mul(private_key)


def serialize_public_key(public_key: Point, compressed: bool = True) -> bytes:
    """공개키를 바이트로. 압축 형식은 x 좌표 + y 의 홀짝만 담아 33바이트다."""
    x, y = public_key
    if compressed:
        prefix = b"\x03" if y & 1 else b"\x02"
        return prefix + x.to_bytes(32, "big")
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")


# ------------------------------------------------------------- 서명

def sign(message_hash: bytes, private_key: int) -> Tuple[int, int]:
    """ECDSA 서명. (r, s) 한 쌍을 만든다.

    매번 다른 난수 k 를 쓴다. 같은 k 를 두 번 쓰면 개인키가 그대로 복원된다
    (2010년 플레이스테이션3 사건이 정확히 이 실수였다).
    """
    z = int.from_bytes(message_hash, "big")

    while True:
        k = secrets.randbelow(N - 1) + 1
        point = point_mul(k)
        if point is None:
            continue

        r = point[0] % N
        if r == 0:
            continue

        s = (_inv(k, N) * (z + r * private_key)) % N
        if s == 0:
            continue

        # s 가 N/2 보다 크면 뒤집는다. 같은 서명이 두 가지로 표현되는 걸 막는다.
        if s > N // 2:
            s = N - s

        return (r, s)


def verify(message_hash: bytes, signature: Tuple[int, int], public_key: Point) -> bool:
    """서명이 그 공개키의 주인이 만든 것인지 확인한다. 개인키는 필요 없다."""
    r, s = signature

    if not (1 <= r < N and 1 <= s < N):
        return False
    if public_key is None or not is_on_curve(public_key):
        return False

    z = int.from_bytes(message_hash, "big")
    s_inv = _inv(s, N)

    u1 = (z * s_inv) % N
    u2 = (r * s_inv) % N

    point = point_add(point_mul(u1, G), point_mul(u2, public_key))
    if point is None:
        return False

    return point[0] % N == r


def signature_to_hex(signature: Tuple[int, int]) -> str:
    r, s = signature
    return r.to_bytes(32, "big").hex() + s.to_bytes(32, "big").hex()


def signature_from_hex(raw: str) -> Tuple[int, int]:
    data = bytes.fromhex(raw)
    if len(data) != 64:
        raise ValueError("서명은 64바이트여야 합니다.")
    return (int.from_bytes(data[:32], "big"), int.from_bytes(data[32:], "big"))
