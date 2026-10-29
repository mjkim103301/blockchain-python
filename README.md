# 이더리움 × 파이썬 — 체인과 대화하기

[이더리움 공식 튜토리얼 "파이썬 개발자를 위한 이더리움, 1부"](https://ethereum.org/ko/developers/tutorials/a-developers-guide-to-ethereum-part-one/)를
따라가며 만든 실습 프로젝트다.

**밑바닥부터 블록체인을 만드는 게 아니라, 이미 있는 체인과 코드로 대화하는 법**을 익힌다.
노드를 설치하거나 테스트 ETH를 구걸할 필요 없이, 메모리 위에서 도는 가짜 체인으로 연습한다.

```
Web3.py  ──▶  eth-tester  (내 컴퓨터 메모리 안의 이더리움)
                 · 블록이 즉시 채굴된다
                 · 계정 10개에 각 1,000,000 ETH
                 · 끄면 전부 사라진다 — 마음껏 부숴도 된다
```

---

## 빠른 시작

```bash
cd ~/Documents/dev/git/study/blockchain-python

# 1) 가상환경 (이미 .venv 가 있다면 생략)
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# 2) 연결 확인
./.venv/bin/python sandbox.py

# 3) 투어 순서대로
./.venv/bin/python tour/01_units.py
./.venv/bin/python tour/02_accounts.py
./.venv/bin/python tour/03_blocks.py
./.venv/bin/python tour/04_transactions.py

# 4) 테스트
./.venv/bin/python -m pytest tests/ -v
```

> 매번 `./.venv/bin/python` 치기 번거로우면 `source .venv/bin/activate` 후 `python` 만 쓰면 된다.

### 대화형으로 만져보기

튜토리얼이 권하는 방식이다. 탭 자동완성이 되니 `w3.eth.` 까지 치고 Tab 을 눌러 보자.

```bash
./.venv/bin/ipython
```

```python
from sandbox import connect
w3 = connect()

w3.eth.accounts                      # 테스트 계정 10개
w3.eth.get_balance(w3.eth.accounts[0])
w3.eth.get_block('latest')
```

---

## 투어 구성

| 파일 | 배우는 것 |
| --- | --- |
| `sandbox.py` | 샌드박스 연결. 모든 투어가 여기서 `connect()` 를 가져다 쓴다 |
| `tour/01_units.py` | wei · gwei · ether. **왜 정수만 쓰는가** |
| `tour/02_accounts.py` | EOA, 주소 체크섬, 잔액은 어디에 있는가 |
| `tour/03_blocks.py` | 블록 구조, `parentHash` 로 체인이 이어지는 원리 |
| `tour/04_transactions.py` | 거래 생애주기, 영수증, nonce, 가스 |

각 파일은 **독립 실행**된다. 순서대로 봐도 되고 궁금한 것만 돌려도 된다.

---

## 핵심 개념 정리

### 단위 — 소수는 없다

```
1 ether = 1,000,000,000,000,000,000 wei   (10^18)
1 gwei  =             1,000,000,000 wei   (10^9)
```

이더리움은 모든 금액을 **wei 단위 정수**로만 센다. 부동소수점은
`0.1 + 0.2 = 0.30000000000000004` 가 되는 세계라, 돈을 다루면서 쓸 수 없다.
원화로 치면 "1.5원" 없이 전부 "15전"으로만 세는 셈이다.

### 계정 — 생성이라는 단계가 없다

```
EOA         개인키로 움직인다. 사람의 지갑
컨트랙트     코드로 움직인다. 개인키가 없다
```

주소 `0x000...dEaD` 를 조회하면 오류가 아니라 **잔액 0** 이 나온다.
2^160 개의 주소가 이미 존재하고, 대부분 잔액이 0 일 뿐이다.
"계정을 만든다"는 건 그냥 개인키를 하나 뽑는 것이다.

주소의 대소문자가 섞인 건 멋이 아니라 **오타 방지 체크섬**(EIP-55)이다.

### 블록 — parentHash 가 전부다

```
블록 0 (제네시스)        블록 1                  블록 2
  hash: cd61...  ◀────── parentHash: cd61...
                         hash: eea8...  ◀────── parentHash: eea8...
                                                hash: 3f0a...
```

중간 블록을 하나 고치면 그 해시가 바뀌고, 다음 블록의 `parentHash` 와 어긋나
**뒤가 전부 깨진다.** 노드마다 이 한 줄을 검사하기 때문에 위조가 통하지 않는다.

`tour/03_blocks.py` 가 실제로 전 구간을 돌며 이 연결을 확인한다.

### 거래 — 상태를 바꾸는 유일한 수단

조회는 공짜지만 뭔가를 바꾸려면 반드시 거래를 보내고 가스를 내야 한다.

```
만들기 → 서명 → 전파(pending) → 채굴 → 영수증 확인
```

실측 결과:

```
Alice  -3.000021 ETH     ← 보낸 금액 + 수수료
Bob    +3.000000 ETH     ← 정확히 보낸 만큼
수수료  0.000021 ETH     ← 보낸 사람만 낸다
```

⚠️ **블록에 담겼다고 성공한 게 아니다.** 실패한 거래도 블록에 들어가고
가스는 그대로 빠져나간다. 반드시 `receipt['status']` 를 봐야 한다 (1=성공, 0=실패).

`nonce` 는 계정마다 0부터 올라가는 번호다. 이미 쓴 nonce 는 재사용할 수 없어
같은 거래가 두 번 처리되는 복제 공격이 막힌다.

---

## 부록 — 밑에서 무슨 일이 일어나는가

튜토리얼은 "체인과 대화하는 법"을 다루지만, 개인키에서 주소가 **어떻게** 나오는지는
다루지 않는다. `appendix/` 에 그 부분을 외부 패키지 없이 직접 구현해 뒀다.

```bash
cd appendix
../.venv/bin/python -c "
import crypto, wallet
w = wallet.Wallet()
print('주소:', w.address)
msg = crypto.sha256(b'Alice -> Bob 3 ETH')
sig = w.sign(msg)
print('검증:', wallet.Wallet.verify(msg, sig, w.public_key_hex))
"
```

| 파일 | 내용 |
| --- | --- |
| `appendix/crypto.py` | SHA-256, secp256k1 타원곡선, ECDSA 서명·검증 |
| `appendix/wallet.py` | 개인키 → 공개키 → 주소 파생, 압축 공개키 복원 |

```
개인키(정수 하나)  ──곱셈──▶  공개키(곡선 위의 점)  ──해시──▶  주소
     비밀                      공유 가능              공유 가능
```

거꾸로는 못 간다(이산로그 문제). 이게 **지갑에 코인이 들어있지 않은** 이유다 —
들어있는 건 개인키 하나뿐이고, 잔액은 체인 위에 적혀 있다.

> ⚠️ 학습용이다. 상수시간 연산이 아니라 사이드채널에 취약하고, 서명 난수도
> RFC6979 결정적 방식이 아니다. 실제 서비스에는 `eth-account` 를 쓸 것.

---

## 환경

```
Python     3.9.6   (시스템 기본)
web3       7.16.0
eth-tester 0.13.0b1
```

`.venv/` 는 git 에 올리지 않는다. 받은 사람은 `requirements.txt` 로 다시 만들면 된다.

### 알려진 경고

```
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+ ...
```

macOS 시스템 파이썬이 LibreSSL 로 빌드돼 있어 나오는 경고다. **동작에는 영향이 없다.**
거슬리면 `export PYTHONWARNINGS=ignore` 하거나 `brew install python@3.12` 로
최신 파이썬을 쓰면 사라진다.

---

## 다음 단계 (튜토리얼 2부 이후)

이 프로젝트는 1부까지다. 이어서 할 것:

- **스마트 컨트랙트 배포** — Solidity 작성 → 컴파일 → `w3.eth.contract()` 로 호출
- **진짜 테스트넷** — Sepolia 에 붙어 보기 ([포셋](https://cloud.google.com/application/web3/faucet/ethereum/sepolia))
- **이벤트 구독** — 컨트랙트 이벤트를 받아 처리하기
- **직접 서명** — 테스트 노드가 대신 해 주던 서명을 `eth-account` 로 직접

---

## 참고

- [파이썬 개발자를 위한 이더리움, 1부](https://ethereum.org/ko/developers/tutorials/a-developers-guide-to-ethereum-part-one/) — 이 프로젝트의 원본
- [Web3.py 공식 문서](https://web3py.readthedocs.io/)
- [eth-tester](https://github.com/ethereum/eth-tester)
- [이더리움 개발자 문서 (한국어)](https://ethereum.org/ko/developers/docs/)
