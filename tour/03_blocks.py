"""투어 2 — 블록 (Block Data)

블록은 거래를 묶은 상자이자, 앞 블록을 가리키는 고리다.

핵심 필드 몇 개만 보면 구조가 잡힌다.

  number       몇 번째 블록인가 (제네시스는 0)
  hash         이 블록의 지문
  parentHash   앞 블록의 지문  ← 이게 '체인'을 만든다
  timestamp    언제 만들어졌나
  transactions 담긴 거래 목록
  stateRoot    이 블록 직후 전체 상태의 요약 (머클 패트리샤 트리 루트)

parentHash 가 핵심이다. 중간 블록을 하나 고치면 그 해시가 바뀌고,
그러면 다음 블록의 parentHash 와 어긋나 뒤가 전부 깨진다.
"변조하면 들킨다"는 성질이 여기서 나온다.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sandbox import connect  # noqa: E402


INTERESTING = [
    ("number", "블록 번호"),
    ("timestamp", "생성 시각"),
    ("miner", "제안자"),
    ("gasLimit", "가스 상한"),
    ("gasUsed", "쓴 가스"),
    ("baseFeePerGas", "기본 수수료"),
    ("size", "크기(byte)"),
]


def show_block(w3, block) -> None:
    print(f"  number       : {block['number']}")
    print(f"  hash         : {block['hash'].hex()}")
    print(f"  parentHash   : {block['parentHash'].hex()}")

    stamp = datetime.fromtimestamp(block["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
    print(f"  timestamp    : {block['timestamp']}  ({stamp})")

    print(f"  transactions : {len(block['transactions'])}건")

    for key, label in INTERESTING:
        if key in block and key not in ("number", "timestamp"):
            value = block[key]
            if isinstance(value, int):
                print(f"  {key:<13}: {value:,}  ({label})")


def main() -> None:
    w3 = connect()

    print("=" * 70)
    print("  투어 2 — 블록")
    print("=" * 70)

    print("\n[제네시스 블록 — 0번]")
    genesis = w3.eth.get_block(0)
    show_block(w3, genesis)
    print("  ※ parentHash 가 전부 0 이다. 앞이 없는 첫 블록이라서다.")

    print("\n[거래를 하나 넣어 블록을 만든다]")
    tx_hash = w3.eth.send_transaction(
        {
            "from": w3.eth.accounts[0],
            "to": w3.eth.accounts[1],
            "value": w3.to_wei(1, "ether"),
            "gas": 21_000,
        }
    )
    print(f"  보낸 거래: {tx_hash.hex()}")
    print("  ※ eth-tester 는 거래를 넣으면 즉시 블록이 채굴된다.")
    print("     실제 메인넷은 12초쯤 기다려야 한다.")

    print("\n[최신 블록 — latest]")
    latest = w3.eth.get_block("latest")
    show_block(w3, latest)

    print("\n[체인이 이어져 있는지 확인]")
    head = w3.eth.block_number
    print(f"  현재 높이: {head}\n")
    ok = True
    for n in range(head, 0, -1):
        child = w3.eth.get_block(n)
        parent = w3.eth.get_block(n - 1)
        linked = child["parentHash"] == parent["hash"]
        ok = ok and linked
        mark = "✓" if linked else "✗"
        print(f"  {mark} 블록 {n}.parentHash == 블록 {n - 1}.hash")

    print(f"\n  → 체인 무결성: {'정상' if ok else '깨짐'}")
    print("  ※ 이 한 줄 비교가 블록체인 검증의 핵심이다.")
    print("     각 노드가 받은 블록마다 이걸 확인하기 때문에 위조가 통하지 않는다.")

    print("\n[블록 조회 방법들]")
    print("  get_block(0)          번호로")
    print("  get_block('latest')   최신")
    print("  get_block('earliest') 제네시스")
    print("  get_block('pending')  아직 블록에 안 들어간 대기 중인 것")
    print(f"  get_block(해시)        {latest['hash'].hex()[:20]}...")


if __name__ == "__main__":
    main()
