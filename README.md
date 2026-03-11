# barrier-free-agent

Simple ReAct agent
Agent generated with [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack) version `0.38.0`

## Project Structure

```
barrier-free-agent/
│
├── app/                       # 🧠 [백엔드] 에이전트의 심장과 손발
│   ├── agent.py               # 에이전트 본체 (Gemini API 연동, 페르소나/프롬프트 정의, ReAct 루프 관리)
│   ├── navigation_tool.py     # 도구 1: 노년층을 위한 화면 이동 및 UI 안내 도구
│   ├── literacy_tool.py       # 도구 2: 주린이를 위한 금융 용어 RAG 도구
│   └── guardrail_tool.py      # 도구 3: 투자 권유 필터링 (금소법 준수)
│
├── tests/                     # 🛡️ [평가] 에이전트가 고장나지 않게 지키는 검문소 (AgentOps)
│   ├── unit/                  # Layer 1: 도구들이 잘 작동하는지 검사 (예: test_tools.py)
│   └── integration/           # Layer 2: 에이전트가 엉뚱한 판단을 하지 않는지 궤적 검사
│
├── data/                      # 📚 [데이터] 에이전트의 지식 베이스
│   ├── eval/                  # 테스트 정답지 (예: golden_set_nh_bank.json)
│   └── rag/                   # 금융 용어사전, 올원뱅크 IRP 약관 텍스트 파일들
│
├── ui/                        # 🎨 [프론트엔드] 사용자가 보는 화면 데모
│   ├── demo.py                 # Streamlit 실행의 진입점 (메인 화면)
│   └── assets/                # 농협 어플 스크린샷 이미지 등 시각 자료
│
├── .env                       # 🔑 비밀키 보관소 (Gemini API Key 등)
├── pyproject.toml             # 📦 패키지 관리 (pytest, streamlit 등 설치 목록)
└── memory.md / GEMINI.md      # 🤖 AI 코딩 조수를 위한 외부 뇌 (하네스)
```

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **make**: Build automation tool - [Install](https://www.gnu.org/software/make/) (pre-installed on most Unix-based systems)


## Quick Start

Install required packages and launch the local development environment:

```bash
make install && make playground
```

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install dependencies using uv                                                               |
| `make playground`    | Launch local development environment                                                        |
| `make lint`          | Run code quality checks                                                                     |
| `make test`          | Run unit and integration tests                                                              |

For full command options and usage, refer to the [Makefile](Makefile).

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `uvx agent-starter-pack enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `uvx agent-starter-pack setup-cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `uvx agent-starter-pack upgrade` | Auto-upgrade to latest version while preserving customizations |
| `uvx agent-starter-pack extract` | Extract minimal, shareable version of your agent |

---

## Development

Edit your agent logic in `app/agent.py` and test with `make playground` - it auto-reloads on save.
See the [development guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/development-guide) for the full workflow.

## Deployment

```bash
gcloud config set project <your-project-id>
make deploy
```

To add CI/CD and Terraform, run `uvx agent-starter-pack enhance`.
To set up your production infrastructure, run `uvx agent-starter-pack setup-cicd`.
See the [deployment guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/deployment) for details.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.
See the [observability guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/observability) for queries and dashboards.
