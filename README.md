# answer-artifact-kit

Tiny helpers for answer-derived text artifacts.

Install from GitHub:

```bash
pip install "git+https://github.com/yanggs07/answer-artifact-kit.git"
```

Use in an artifact script:

```python
from answer_artifact_kit import run_case_cli_from_url

SOURCE_URL = "https://yitang-admin.yitang.top/answer/detail?id=123&sign=..."
CASE_TEXT = "..."

if __name__ == "__main__":
    raise SystemExit(run_case_cli_from_url(SOURCE_URL, CASE_TEXT))
```

The script supports:

```bash
python case.py
python case.py --text
python case.py --json
python case.py --prompt "rewrite this case..."
```

LLM configuration is read from env:

```bash
LLM_ENDPOINT
LLM_API_KEY
LLM_MODEL_ID
```
