"""투어 0 — 단위 (wei · gwei · ether)

이더리움에는 소수가 없다. 모든 금액은 **wei 단위의 정수**다.

    1 ether = 1,000,000,000,000,000,000 wei  (10^18)
    1 gwei  = 1,000,000,000 wei              (10^9)

왜 정수만 쓰나? 부동소수점은 0.1 + 0.2 != 0.3 이 되는 세계다.
돈을 다루면서 그런 오차를 허용할 수 없으니 가장 작은 단위의 정수로만 센다.
원화로 치면 "1.5원" 없이 전부 "15전"으로만 세는 셈이다.

가스비를 말할 때 gwei 를 쓰는 건 그냥 읽기 편해서다.
21000 * 20000000000 wei 보다 "가스 20 gwei" 가 입에 붙는다.
"""

from __future__ import annotations

from web3 import Web3


def main() -> None:
    print("=" * 58)
    print("  투어 0 — 단위 변환")
    print("=" * 58)

    print("\n[ether → wei]")
    for amount in (1, 0.5, 0.000001):
        wei = Web3.to_wei(amount, "ether")
        print(f"  {amount:>10} ether = {wei:>22,} wei")

    print("\n[wei → 다른 단위]")
    one_eth = Web3.to_wei(1, "ether")
    for unit in ("wei", "gwei", "ether"):
        print(f"  1 ether = {Web3.from_wei(one_eth, unit):>22} {unit}")

    print("\n[가스비 감각 잡기]")
    gas_limit = 21_000  # 단순 송금에 드는 고정 가스
    for gwei in (1, 20, 100):
        fee_wei = gas_limit * Web3.to_wei(gwei, "gwei")
        fee_eth = Web3.from_wei(fee_wei, "ether")
        print(f"  {gwei:>3} gwei × 21,000 gas = {fee_eth} ETH")

    print("\n  ※ 송금 한 건의 가스는 21,000 으로 고정이다.")
    print("     네트워크가 붐빌수록 gwei 단가가 올라 수수료가 비싸진다.")

    print("\n[정수만 쓰는 이유]")
    print(f"  파이썬 실수:  0.1 + 0.2 = {0.1 + 0.2}")
    print("  wei 정수:     오차가 생길 자리 자체가 없다")


if __name__ == "__main__":
    main()
