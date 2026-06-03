import argparse
import json
import sys

from .case import AnswerCaseArtifact, call_llm


DEFAULT_TAG_PROMPT_TEMPLATE = """我们对这份作业得出了这样的文本标签结果

{tag_text}

我们希望在此基础之上做如下加工，你直接输出新的标签文本即可。输出格式必须是英文逗号分隔的标签字符串，不要输出解释、分析过程、标题或 JSON。

{user_prompt}

作业原文是

{source_text}
"""


class AnswerTagsArtifact:
    def __init__(self, source_url, tags, prompt_template=DEFAULT_TAG_PROMPT_TEMPLATE):
        self.source_url = source_url
        self.tags = normalize_tags(tags)
        self.prompt_template = prompt_template
        self.answer = AnswerCaseArtifact.from_url(source_url, "")

    def text(self):
        return ",".join(self.tags)

    def json_payload(self):
        return self.tags

    def reprocess(self, user_prompt):
        prompt = self.prompt_template.format(
            tag_text=self.text(),
            user_prompt=user_prompt,
            source_text=self.answer.fetch_source_text(),
        )
        return call_llm(prompt)

    def main(self, argv=None, description=None):
        argv = sys.argv[1:] if argv is None else argv
        parser = argparse.ArgumentParser(
            description=description or "Emit or reprocess answer tag artifact.",
        )
        parser.add_argument("--text", action="store_true", help="print tags as an English-comma-separated string")
        parser.add_argument("--json", action="store_true", help="print tags as a JSON array")
        parser.add_argument("--prompt", help="reprocess the tags with this instruction")
        parser.add_argument("--prompt-file", help="read extra reprocessing instruction from a UTF-8 text file")

        if not argv:
            parser.print_help()
            return 0

        args = parser.parse_args(argv)
        modes = sum(bool(x) for x in [args.text, args.json, args.prompt or args.prompt_file])
        if modes != 1:
            parser.error("choose exactly one mode: --text, --json, or --prompt/--prompt-file")

        if args.text:
            print(self.text())
            return 0

        if args.json:
            print(json.dumps(self.json_payload(), ensure_ascii=False, indent=2))
            return 0

        user_prompt = read_prompt(args)
        if not user_prompt:
            parser.error("--prompt or --prompt-file cannot be empty")

        print(self.reprocess(user_prompt))
        return 0


def run_tags_cli_from_url(source_url, tags, prompt_template=DEFAULT_TAG_PROMPT_TEMPLATE, argv=None):
    return AnswerTagsArtifact(
        source_url=source_url,
        tags=tags,
        prompt_template=prompt_template,
    ).main(argv)


def normalize_tags(tags):
    if isinstance(tags, str):
        return [tag.strip() for tag in tags.split(",") if tag.strip()]
    return [str(tag).strip() for tag in tags if str(tag).strip()]


def read_prompt(args):
    chunks = []
    if args.prompt:
        chunks.append(args.prompt)
    if args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            chunks.append(f.read())
    return "\n\n".join(chunk.strip() for chunk in chunks if chunk.strip())
