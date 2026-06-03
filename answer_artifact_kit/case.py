import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_HOST = "https://yitang-admin.yitang.top"

DEFAULT_PROMPT_TEMPLATE = """我们对这份作业得出了这样的案例结果

{case_text}

我们希望在此基础之上做如下加工，你直接输出新的案例文本即可。不要输出解释、分析过程、标题或 JSON。

{user_prompt}

作业原文是

{source_text}
"""


class AnswerCaseArtifact:
    def __init__(self, answer_id, sign, case_text, host=DEFAULT_HOST, prompt_template=DEFAULT_PROMPT_TEMPLATE):
        self.answer_id = int(answer_id)
        self.sign = sign
        self.case_text = case_text
        self.host = host.rstrip("/")
        self.prompt_template = prompt_template

    @classmethod
    def from_url(cls, source_url, case_text, prompt_template=DEFAULT_PROMPT_TEMPLATE):
        parsed = urllib.parse.urlparse(source_url)
        query = urllib.parse.parse_qs(parsed.query)
        answer_id = first_query_value(query, "id")
        sign = first_query_value(query, "sign")
        if not answer_id or not sign:
            raise ValueError("source_url must contain id and sign query params")
        host = f"{parsed.scheme}://{parsed.netloc}"
        return cls(
            answer_id=answer_id,
            sign=sign,
            case_text=case_text,
            host=host,
            prompt_template=prompt_template,
        )

    def source_url(self):
        return f"{self.host}/answer/detail?id={self.answer_id}&sign={self.sign}"

    def answer_view_url(self):
        return f"{self.host}/answer/view?id={self.answer_id}"

    def build_json_payload(self):
        answer = self.fetch_answer()
        data = answer.get("data", {})
        meta = {
            "artifactType": "answer_case",
            "answerId": self.answer_id,
            "sign": self.sign,
            "sourceUrl": self.source_url(),
            "answerViewUrl": self.answer_view_url(),
        }
        for key in ["id", "ssoId", "submitTime", "status", "score", "textCount", "textCountReal"]:
            if key in data:
                meta[key] = data[key]
        return {
            "caseText": self.case_text,
            "meta": meta,
        }

    def fetch_answer(self):
        request = urllib.request.Request(self.source_url(), method="GET")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"Answer fetch failed: HTTP {exc.code}\n{detail}") from exc
        except urllib.error.URLError as exc:
            raise SystemExit(f"Answer fetch failed: {exc}") from exc

        if payload.get("code") != 0:
            raise SystemExit("Answer fetch failed: " + json.dumps(payload, ensure_ascii=False))
        return payload

    def fetch_source_text(self):
        data = self.fetch_answer().get("data", {})
        answers = data.get("answers", {})
        if not isinstance(answers, dict):
            return ""

        chunks = []
        for question_id in sorted(answers.keys(), key=question_sort_key):
            value = answers[question_id]
            if isinstance(value, str):
                chunks.append(f"{question_id}:\n{value}")
            else:
                chunks.append(f"{question_id}:\n{json.dumps(value, ensure_ascii=False)}")
        return "\n\n".join(chunks)

    def reprocess(self, user_prompt):
        prompt = self.prompt_template.format(
            case_text=self.case_text,
            user_prompt=user_prompt,
            source_text=self.fetch_source_text(),
        )
        return call_llm(prompt)

    def main(self, argv=None, description=None):
        argv = sys.argv[1:] if argv is None else argv
        parser = argparse.ArgumentParser(
            description=description or f"Emit or reprocess the case artifact for answer {self.answer_id}.",
        )
        parser.add_argument("--text", action="store_true", help="print the case text")
        parser.add_argument("--json", action="store_true", help="print case text and live meta as JSON; source text is excluded")
        parser.add_argument("--prompt", help="reprocess the case with this instruction")
        parser.add_argument("--prompt-file", help="read extra reprocessing instruction from a UTF-8 text file")

        if not argv:
            parser.print_help()
            return 0

        args = parser.parse_args(argv)
        modes = sum(bool(x) for x in [args.text, args.json, args.prompt or args.prompt_file])
        if modes != 1:
            parser.error("choose exactly one mode: --text, --json, or --prompt/--prompt-file")

        if args.text:
            print(self.case_text)
            return 0

        if args.json:
            print(json.dumps(self.build_json_payload(), ensure_ascii=False, indent=2))
            return 0

        user_prompt = read_prompt(args)
        if not user_prompt:
            parser.error("--prompt or --prompt-file cannot be empty")

        print(self.reprocess(user_prompt))
        return 0


def run_case_cli(answer_id, sign, case_text, host=DEFAULT_HOST, prompt_template=DEFAULT_PROMPT_TEMPLATE, argv=None):
    return AnswerCaseArtifact(
        answer_id=answer_id,
        sign=sign,
        case_text=case_text,
        host=host,
        prompt_template=prompt_template,
    ).main(argv)


def run_case_cli_from_url(source_url, case_text, prompt_template=DEFAULT_PROMPT_TEMPLATE, argv=None):
    return AnswerCaseArtifact.from_url(
        source_url=source_url,
        case_text=case_text,
        prompt_template=prompt_template,
    ).main(argv)


def first_query_value(query, name):
    value = query.get(name, [""])[0]
    return value.strip() if isinstance(value, str) else value


def question_sort_key(question_id):
    if question_id.startswith("q") and question_id[1:].isdigit():
        return int(question_id[1:]), question_id
    return 10**9, question_id


def call_llm(prompt):
    endpoint = os.getenv("LLM_ENDPOINT", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model_id = os.getenv("LLM_MODEL_ID", "").strip()

    missing = [name for name, value in {
        "LLM_ENDPOINT": endpoint,
        "LLM_API_KEY": api_key,
        "LLM_MODEL_ID": model_id,
    }.items() if not value]
    if missing:
        raise SystemExit("Missing env: " + ", ".join(missing))

    body = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"LLM request failed: HTTP {exc.code}\n{detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"LLM request failed: {exc}") from exc

    return extract_text(payload)


def extract_text(payload):
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"].strip()

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    texts.append(item["text"])
            if texts:
                return "\n".join(texts).strip()

    output = payload.get("output")
    if isinstance(output, list):
        texts = []
        for item in output:
            for content in item.get("content", []):
                text = content.get("text") if isinstance(content, dict) else None
                if isinstance(text, str):
                    texts.append(text)
        if texts:
            return "\n".join(texts).strip()

    raise SystemExit("LLM response did not contain text output.")


def read_prompt(args):
    chunks = []
    if args.prompt:
        chunks.append(args.prompt)
    if args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            chunks.append(f.read())
    return "\n\n".join(chunk.strip() for chunk in chunks if chunk.strip())
