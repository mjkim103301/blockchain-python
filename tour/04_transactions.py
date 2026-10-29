"""투어 3 — 거래 (Transactions)

거래는 체인의 상태를 바꾸는 **유일한 수단**이다.
조회는 공짜지만, 뭔가를 바꾸려면 반드시 거래를 보내고 가스를 내야 한다.

거래 한 건의 생애:

    1. 만들기   from · to · value · gas 를 채운다
    2. 서명     개인키로 서명한다 (여기선 테스트 노드가 대신 해 준다)
    3. 전파     네트워크에 뿌린다 → pending 상태
    4. 채굴     블록에 담긴다
    5. 영수증   receipt 로 성공·실패와 실제 쓴 가스를 확인한다

주의: 거래가 블록에 담겼다고 성공한 건 아니다.
      실패한 거래도 블록에 들어가고 가스는 그대로 빠져나간다.
      반드시 receipt 의 status 를 봐야 한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sandbox import connect  # noqa: E402


def balances(w3, *addresses):
    return [w3.from_wei(w3.eth.get_balance(a), "ether") for a in addresses]


def main() -> None:
    w3 = connect()

    alice = w3.eth.accounts[0]
    bob = w3.eth.accounts[1]

    print("=" * 70)
    print("  투어 3 — 거래")
    print("=" * 70)

    print("\n[보내기 전]")
    before_a, before_b = balances(w3, alice, bob)
    print(f"  Alice {alice[:10]}...  {before_a:>14,.6f} ETH")
    print(f"  Bob   {bob[:10]}...  {before_b:>14,.6f} ETH")

    amount = w3.to_wei(3, "ether")
    print(f"\n[Alice → Bob  3 ETH 송금]")

    tx_hash = w3.eth.send_transaction(
        {
            "from": alice,
            "to": bob,
            "value": amount,
            "gas": 21_000,
        }
    )
    print(f"  거래 해시: {tx_hash.hex()}")

    print("\n[거래 내용 조회]")
    tx = w3.eth.get_transaction(tx_hash)
    for key in ("blockNumber", "from", "to", "value", "gas", "nonce"):
        value = tx.get(key)
        if key == "value":
            print(f"  {key:<12}: {value:,} wei  ({w3.from_wei(value, 'ether')} ETH)")
        elif isinstance(value, int):
            print(f"  {key:<12}: {value:,}")
        else:
            print(f"  {key:<12}: {value}")

    print("\n[영수증 — 성공했는지 확인]")
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    status = receipt["status"]
    print(f"  status       : {status}  ({'성공' if status == 1 else '실패'})")
    print(f"  gasUsed      : {receipt['gasUsed']:,}")
    print(f"  blockNumber  : {receipt['blockNumber']}")
    print("  ※ status 가 0 이면 실패다. 실패해도 가스는 돌려받지 못한다.")

    print("\n[보낸 뒤]")
    after_a, after_b = balances(w3, alice, bob)
    print(f"  Alice  {after_a:>14,.6f} ETH   ({after_a - before_a:+,.6f})")
    print(f"  Bob    {after_b:>14,.6f} ETH   ({after_b - before_b:+,.6f})")

    diff_a = before_a - after_a
    print(f"\n  Alice 가 잃은 양 : {diff_a:,.6f} ETH")
    print(f"  Bob 이 받은 양   : {after_b - before_b:,.6f} ETH")
    print(f"  차이(수수료)     : {diff_a - (after_b - before_b):,.6f} ETH")
    print("  ※ 보낸 사람만 가스를 낸다. 받는 쪽은 정확히 보낸 만큼 받는다.")

    print("\n[nonce — 같은 거래가 두 번 처리되는 걸 막는다]")
    nonce = w3.eth.get_transaction_count(alice)
    print(f"  Alice 의 다음 nonce: {nonce}")
    print("  ※ 계정마다 0 부터 하나씩 올라간다. 순서대로만 처리되고,")
    print("     이미 쓴 nonce 는 재사용할 수 없어 복제 공격이 막힌다.")

    print("\n[가스 미리 재보기 — 보내기 전에 확인할 수 있다]")
    estimate = w3.eth.estimate_gas(
        {"from": alice, "to": bob, "value": w3.to_wei(1, "ether")}
    )
    print(f"  estimate_gas : {estimate:,}")
    print("  ※ 단순 송금은 항상 21,000 이다. 컨트랙트 호출이면 훨씬 커진다.")

    print("\n[잔액보다 많이 보내면?]")
    try:
        w3.eth.send_transaction(
            {
                "from": bob,
                "to": alice,
                "value": w3.to_wei(10_000_000, "ether"),
                "gas": 21_000,
            }
        )
        print("  (예상과 달리 통과했다)")
    except Exception as exc:  # noqa: BLE001 - 학습용이라 메시지를 그대로 본다
        print(f"  거부됨: {type(exc).__name__}")
        print(f"  {str(exc)[:110]}")
        print("  ※ 노드가 거래를 받기 전에 걸러낸다. 블록에도 안 들어간다.")


if __name__ == "__main__":
    main()
