"""투어에서 배운 내용이 실제로 그런지 검증한다.

문서에 적힌 설명을 테스트로 고정해 두면,
web3.py 버전이 올라가 동작이 달라졌을 때 바로 드러난다.

    .venv/bin/python -m pytest tests/ -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web3 import Web3  # noqa: E402

from sandbox import connect  # noqa: E402


@pytest.fixture
def w3():
    return connect()


# ------------------------------------------------------------ 단위

class TestUnits:
    def test_1_ether_is_10_to_the_18_wei(self):
        assert Web3.to_wei(1, "ether") == 10 ** 18

    def test_1_gwei_is_10_to_the_9_wei(self):
        assert Web3.to_wei(1, "gwei") == 10 ** 9

    def test_round_trip(self):
        assert Web3.from_wei(Web3.to_wei(1.5, "ether"), "ether") == 1.5

    def test_wei_is_integer_not_float(self):
        """부동소수점 오차가 끼어들 자리가 없어야 한다."""
        assert isinstance(Web3.to_wei(0.1, "ether"), int)
        assert Web3.to_wei(0.1, "ether") + Web3.to_wei(0.2, "ether") == Web3.to_wei(
            0.3, "ether"
        )


# ------------------------------------------------------------ 연결

class TestSandbox:
    def test_connects(self, w3):
        assert w3.is_connected()

    def test_starts_at_genesis(self, w3):
        assert w3.eth.block_number == 0

    def test_has_ten_funded_accounts(self, w3):
        accounts = w3.eth.accounts
        assert len(accounts) == 10
        for address in accounts:
            assert w3.eth.get_balance(address) > 0


# ------------------------------------------------------------ 계정

class TestAccounts:
    def test_address_is_20_bytes(self, w3):
        address = w3.eth.accounts[0]
        assert address.startswith("0x")
        assert len(address) == 42  # 0x + 40 hex

    def test_addresses_are_checksummed(self, w3):
        for address in w3.eth.accounts:
            assert Web3.is_checksum_address(address)

    def test_unknown_address_has_zero_balance(self, w3):
        """없는 계정도 오류가 아니라 잔액 0 이다."""
        nowhere = "0x000000000000000000000000000000000000dEaD"
        assert w3.eth.get_balance(nowhere) == 0

    def test_balance_is_wei_integer(self, w3):
        balance = w3.eth.get_balance(w3.eth.accounts[0])
        assert isinstance(balance, int)


# ------------------------------------------------------------ 블록

class TestBlocks:
    def test_genesis_has_zero_parent_hash(self, w3):
        genesis = w3.eth.get_block(0)
        assert genesis["number"] == 0
        assert int(genesis["parentHash"].hex(), 16) == 0

    def test_new_block_links_to_parent(self, w3):
        """parentHash 로 앞 블록을 가리킨다 — 이게 체인을 만든다."""
        before = w3.eth.get_block("latest")

        w3.eth.send_transaction(
            {
                "from": w3.eth.accounts[0],
                "to": w3.eth.accounts[1],
                "value": Web3.to_wei(1, "ether"),
                "gas": 21_000,
            }
        )

        after = w3.eth.get_block("latest")
        assert after["number"] == before["number"] + 1
        assert after["parentHash"] == before["hash"]

    def test_whole_chain_is_linked(self, w3):
        for _ in range(3):
            w3.eth.send_transaction(
                {
                    "from": w3.eth.accounts[0],
                    "to": w3.eth.accounts[1],
                    "value": Web3.to_wei(1, "ether"),
                    "gas": 21_000,
                }
            )

        head = w3.eth.block_number
        assert head == 3

        for n in range(head, 0, -1):
            child = w3.eth.get_block(n)
            parent = w3.eth.get_block(n - 1)
            assert child["parentHash"] == parent["hash"], f"블록 {n} 연결이 끊겼다"

    def test_transaction_lands_in_block(self, w3):
        tx_hash = w3.eth.send_transaction(
            {
                "from": w3.eth.accounts[0],
                "to": w3.eth.accounts[1],
                "value": Web3.to_wei(1, "ether"),
                "gas": 21_000,
            }
        )
        block = w3.eth.get_block("latest")
        assert tx_hash in block["transactions"]


# ------------------------------------------------------------ 거래

class TestTransactions:
    def test_receiver_gets_exact_amount(self, w3):
        """받는 쪽은 수수료를 떼지 않은 정확한 금액을 받는다."""
        alice, bob = w3.eth.accounts[0], w3.eth.accounts[1]
        before = w3.eth.get_balance(bob)
        amount = Web3.to_wei(3, "ether")

        w3.eth.send_transaction(
            {"from": alice, "to": bob, "value": amount, "gas": 21_000}
        )

        assert w3.eth.get_balance(bob) - before == amount

    def test_sender_pays_amount_plus_gas(self, w3):
        alice, bob = w3.eth.accounts[0], w3.eth.accounts[1]
        before = w3.eth.get_balance(alice)
        amount = Web3.to_wei(3, "ether")

        tx_hash = w3.eth.send_transaction(
            {"from": alice, "to": bob, "value": amount, "gas": 21_000}
        )
        receipt = w3.eth.get_transaction_receipt(tx_hash)

        spent = before - w3.eth.get_balance(alice)
        assert spent > amount, "수수료만큼 더 빠져나가야 한다"
        assert receipt["gasUsed"] == 21_000

    def test_receipt_status_is_one_on_success(self, w3):
        tx_hash = w3.eth.send_transaction(
            {
                "from": w3.eth.accounts[0],
                "to": w3.eth.accounts[1],
                "value": Web3.to_wei(1, "ether"),
                "gas": 21_000,
            }
        )
        assert w3.eth.get_transaction_receipt(tx_hash)["status"] == 1

    def test_simple_transfer_always_costs_21000_gas(self, w3):
        estimate = w3.eth.estimate_gas(
            {
                "from": w3.eth.accounts[0],
                "to": w3.eth.accounts[1],
                "value": Web3.to_wei(1, "ether"),
            }
        )
        assert estimate == 21_000

    def test_nonce_increments(self, w3):
        alice = w3.eth.accounts[0]
        assert w3.eth.get_transaction_count(alice) == 0

        w3.eth.send_transaction(
            {
                "from": alice,
                "to": w3.eth.accounts[1],
                "value": Web3.to_wei(1, "ether"),
                "gas": 21_000,
            }
        )
        assert w3.eth.get_transaction_count(alice) == 1

    def test_overspending_is_rejected(self, w3):
        """잔액보다 많이 보내면 블록에 들어가지도 못한다."""
        with pytest.raises(Exception):
            w3.eth.send_transaction(
                {
                    "from": w3.eth.accounts[0],
                    "to": w3.eth.accounts[1],
                    "value": Web3.to_wei(10_000_000, "ether"),
                    "gas": 21_000,
                }
            )
