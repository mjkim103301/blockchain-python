"""투어 1 — 계정 (Accounts)

이더리움 계정은 두 종류다.

  EOA (외부 소유 계정)   개인키로 움직인다. 사람의 지갑.
  컨트랙트 계정          코드로 움직인다. 개인키가 없다.

여기서 보는 건 전부 EOA 다. eth-tester 가 미리 10개를 만들고
각각 1,000,000 ETH 를 넣어 둔다 — 테스트 체인이라 가능한 일이다.

잔액은 '계정 안에' 있는 게 아니라 **체인의 상태(state)에 기록된 숫자**다.
비트코인이 UTXO(쓰지 않은 거스름돈)를 세는 것과 달리,
이더리움은 계정별 잔액을 하나의 장부에 직접 적어 둔다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web3 import Web3  # noqa: E402

from sandbox import connect  # noqa: E402


def main() -> None:
    w3 = connect()

    print("=" * 66)
    print("  투어 1 — 계정")
    print("=" * 66)

    accounts = w3.eth.accounts
    print(f"\n미리 준비된 테스트 계정: {len(accounts)}개\n")

    for i, address in enumerate(accounts):
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, "ether")
        mark = "  ← 기본 송신자" if i == 0 else ""
        print(f"  [{i}] {address}  {balance_eth:>12,.0f} ETH{mark}")

    print("\n[주소의 생김새]")
    first = accounts[0]
    print(f"  원본      : {first}")
    print(f"  길이      : {len(first)}자 (0x + 40자리 16진수 = 20바이트)")
    print(f"  체크섬    : {Web3.is_checksum_address(first)}")
    print(f"  소문자화  : {first.lower()}")
    print("  ※ 대소문자가 섞인 건 오타 방지용 체크섬이다(EIP-55).")
    print("     주소 하나 잘못 쳐서 돈을 날리는 걸 막아 준다.")

    print("\n[잔액 조회는 상태를 읽는 것]")
    print(f"  get_balance 반환형 : {type(w3.eth.get_balance(first)).__name__} (wei 정수)")
    print(f"  값                 : {w3.eth.get_balance(first):,} wei")
    print("  ※ 조회는 공짜다. 체인을 바꾸지 않으니 가스가 들지 않는다.")

    print("\n[없는 계정을 조회하면?]")
    nowhere = "0x000000000000000000000000000000000000dEaD"
    print(f"  {nowhere}")
    print(f"  잔액: {w3.eth.get_balance(nowhere)} wei")
    print("  ※ 오류가 아니라 0 이다. 이더리움에 '계정 생성'이라는 단계는 없다.")
    print("     주소는 2^160 개가 이미 존재하고, 잔액이 0 일 뿐이다.")


if __name__ == "__main__":
    main()
