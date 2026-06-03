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

For tag artifacts:

```python
from answer_artifact_kit import run_tags_cli_from_url

SOURCE_URL = "https://yitang-admin.yitang.top/answer/detail?id=123&sign=..."
TAGS = ["标签1", "标签2", "标签3"]

if __name__ == "__main__":
    raise SystemExit(run_tags_cli_from_url(SOURCE_URL, TAGS))
```

Render artifact scripts from source URL plus text outputs:

```python
from answer_artifact_kit import render_case_script, render_tags_script

case_py = render_case_script(SOURCE_URL, CASE_TEXT)
tags_py = render_tags_script(SOURCE_URL, TAGS)
```

Rendering fetches answer meta once and embeds it as a one-line `META_JSON` string. It does not embed answer body text; prompt reprocessing fetches the source text at runtime.

The script supports:

```bash
python case.py
python case.py --text
python case.py --json
python case.py --prompt "rewrite this case..."
```

Case JSON shape:

```json
{
  "caseText": "...",
  "meta": {}
}
```

Tag JSON shape:

```json
{
  "tags": ["标签1", "标签2", "标签3"],
  "meta": {}
}
```

LLM configuration is read from env:

```bash
LLM_ENDPOINT
LLM_API_KEY
LLM_MODEL_ID
```
