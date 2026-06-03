import json

from .case import AnswerCaseArtifact


INSTALL_URL = "git+https://github.com/yanggs07/answer-artifact-kit.git"

CASE_TEMPLATE = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

try:
    from answer_artifact_kit import run_case_cli_from_url
except ModuleNotFoundError:
    raise SystemExit(
        'Missing dependency. Install it with:\\n'
        '  pip install "{install_url}"'
    )


SOURCE_URL = {source_url}
CASE_TEXT = {case_text}
META_JSON = {meta_json}


if __name__ == "__main__":
    raise SystemExit(run_case_cli_from_url(SOURCE_URL, CASE_TEXT, meta_json=META_JSON, argv=sys.argv[1:]))
"""

TAGS_TEMPLATE = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

try:
    from answer_artifact_kit import run_tags_cli_from_url
except ModuleNotFoundError:
    raise SystemExit(
        'Missing dependency. Install it with:\\n'
        '  pip install "{install_url}"'
    )


SOURCE_URL = {source_url}
TAGS = {tags}
META_JSON = {meta_json}


if __name__ == "__main__":
    raise SystemExit(run_tags_cli_from_url(SOURCE_URL, TAGS, meta_json=META_JSON, argv=sys.argv[1:]))
"""


def render_case_script(source_url, case_text):
    return CASE_TEMPLATE.format(
        install_url=INSTALL_URL,
        source_url=py_string(source_url.strip().strip('"')),
        case_text=py_string(case_text),
        meta_json=py_meta_string(fetch_meta_json(source_url, "answer_case")),
    )


def render_tags_script(source_url, tags):
    return TAGS_TEMPLATE.format(
        install_url=INSTALL_URL,
        source_url=py_string(source_url.strip().strip('"')),
        tags=py_value(tags),
        meta_json=py_meta_string(fetch_meta_json(source_url, "answer_tags")),
    )


def fetch_meta_json(source_url, artifact_type):
    meta = AnswerCaseArtifact.from_url(source_url, "").fetch_meta()
    meta["artifactType"] = artifact_type
    return json.dumps(meta, ensure_ascii=False, separators=(",", ":"))


def py_string(value):
    return json.dumps(value, ensure_ascii=False)


def py_meta_string(value):
    return repr(value)


def py_value(value):
    return json.dumps(value, ensure_ascii=False, indent=4)
