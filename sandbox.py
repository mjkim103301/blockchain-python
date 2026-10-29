"""샌드박스 체인에 연결한다.

튜토리얼 "Spin Up a Sandbox" 단계를 함수 하나로 묶었다.
eth-tester 는 메모리 안에서만 도는 가짜 이더리움 노드다.

  - 블록이 즉시 채굴된다 (기다릴 필요 없음)
  - 테스트 계정 10개에 각각 1,000,000 ETH 가 들어 있다
  - 프로세스를 끄면 전부 사라진다

진짜 네트워크가 아니므로 마음껏 부숴도 된다. 그게 샌드박스를 쓰는 이유다.
"""

from __future__ import annotations

from web3 import Web3


def connect() -> Web3:
    """메모리 위의 테스트 체인에 연결한 Web3 객체를 돌려준다."""
    w3 = Web3(Web3.EthereumTesterProvider())

    if not w3.is_connected():
        raise RuntimeError(
            "샌드박스에 연결하지 못했습니다. `pip install 'web3[tester]'` 를 확인하세요."
        )

    return w3


def describe(w3: Web3) -> None:
    """연결 상태를 한눈에 찍어 준다."""
    print(f"  연결       : {w3.is_connected()}")
    print(f"  클라이언트 : {w3.client_version}")
    print(f"  체인 ID    : {w3.eth.chain_id}")
    print(f"  현재 블록  : {w3.eth.block_number}")
    print(f"  계정 수    : {len(w3.eth.accounts)}")


if __name__ == "__main__":
    print("샌드박스 체인에 연결합니다...\n")
    describe(connect())
