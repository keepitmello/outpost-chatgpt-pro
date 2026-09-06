---
date: 2026-09-07
scope: [outpost, security, aside]
type: feature
---

## TL;DR

Outpost가 패킷을 브라우저에 올리기 전에 고신뢰 자격증명을 차단하도록 하였다. 기존 복구기가 사용하는 읽기 전용 ChatGPT 요청도 실제 동작에 맞게 보안 경계로 명시하였다.

## 배경

Outpost는 지금까지 패킷의 비밀정보를 사람이 직접 확인하도록 안내했지만 실행기가 이를 검사하지 않았다. 또한 README는 private ChatGPT endpoint를 사용하지 않는다고 설명했으나, 실제 복구기는 전송 결과가 불명확할 때 현재 실행의 ID가 붙은 사용자 메시지를 찾고 답변과 첨부를 회수하기 위해 읽기 전용 요청을 사용하고 있었다.

## 결정

- 패킷에서 자기 식별 형식이 뚜렷하거나 명시적인 인증 문맥에 있는 자격증명만 차단한다.
- 탐지 결과에는 규칙 이름과 줄·열, 고정된 수정 안내만 남긴다. 원문 일부와 길이는 출력하지 않는다.
- 우회 옵션을 만들지 않는다. 오탐이면 패킷을 플레이스홀더로 고쳐 같은 명령을 다시 실행한다.
- 기존 exit 2를 사용한다. 빈 패킷이나 잘못된 제목과 마찬가지로 브라우저가 열리기 전 입력 검증 실패이기 때문이다.
- 메시지 전송은 보이는 ChatGPT UI만 사용한다. 내부 요청은 이 프로세스가 전송을 시도한 뒤 커밋 여부를 확인하는 탐침과, 해당 Outpost ID를 확인한 뒤의 답변·첨부 회수에만 허용한다.

AKIA·ASIA 식별자, 문맥 없는 JWT, 일반적인 `token=`·`password=`, 플레이스홀더, 개인정보는 자동 차단 대상에서 제외하였다. 비밀값이 아닌 자료와 문서 예제를 막아 사용자가 검사 자체를 우회하는 습관이 생기지 않도록 하기 위한 선택이다.

## 구현

- `outpost/scripts/secret_scan.py`: 개인키와 GitHub·Anthropic·OpenAI·Slack·Google·AWS·Bearer 자격증명을 검사한다.
- `outpost/scripts/run_aside_repl_outpost.py`: 패킷을 읽은 직후, Aside와 세션 저장소를 열기 전에 검사를 실행한다.
- `README.md`, `outpost/SKILL.md`, `outpost/references/runbook.md`: 보이는 UI 전송, 읽기 전용 복구, 토큰 비저장, 자동 재전송·인증 우회 금지를 설명한다.
- `outpost/tests/`: 오탐·미탐 경계, 비밀값 비출력, 파일 비변형, 브라우저 미실행, ID 기반 첨부 회수와 GET 전용 복구를 검증한다.

## 검토에서 고친 점

첫 구현은 따옴표가 있는 Authorization 헤더와 curl 헤더를 놓쳤고, 형식 없는 긴 `sk-` 문자열을 OpenAI 키로 단정하였다. OpenAI 키를 구조형 접두사 또는 정확한 구형 길이로 제한하고, AWS 40자 값의 끝 경계와 Bearer 문맥을 보강하였다. 생성된 복구 JavaScript도 Node에서 실행하여 실제 요청 메서드가 모두 GET인지 확인하도록 바꾸었다.

## 검증

```bash
cd /Users/wooojin/dev/outpost-chatgpt-pro
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s outpost/tests -q
git diff --check
```

Outpost 테스트 75개가 통과했고 `git diff --check`도 오류 없이 끝났다.

## Files Changed

| 파일 | 변경 |
|---|---|
| `README.md` | 실제 브라우저·복구 보안 경계 설명 |
| `outpost/SKILL.md` | 전송 전 자격증명 차단 계약 |
| `outpost/references/runbook.md` | 탐침·회수 허용 범위와 금지 동작 |
| `outpost/scripts/secret_scan.py` | 고신뢰 자격증명 탐지 |
| `outpost/scripts/run_aside_repl_outpost.py` | 브라우저 실행 전 검사 연결 |
| `outpost/tests/test_secret_scan.py` | 탐지와 오탐 회귀 검사 |
| `outpost/tests/test_run_aside_repl_outpost.py` | 부작용·복구 불변식 검사 |
| `outpost/tests/test_contract.py` | 문서 계약 검사 |
