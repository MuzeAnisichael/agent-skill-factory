from __future__ import annotations

import json
from typing import Any


EVAL_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/MuzeAnisichael/agent-skill-factory/blob/main/docs/eval-schema.json",
    "title": "Agent Skill Factory Eval File",
    "description": "Schema for <skill>/evals/evals.json files used by skill-factory eval.",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "trigger_tests": {
            "type": "array",
            "items": {"$ref": "#/$defs/triggerTest"},
            "minItems": 1,
        },
        "task_tests": {
            "type": "array",
            "items": {"$ref": "#/$defs/taskTest"},
            "minItems": 1,
        },
    },
    "anyOf": [
        {"required": ["trigger_tests"]},
        {"required": ["task_tests"]},
    ],
    "$defs": {
        "nonEmptyString": {
            "type": "string",
            "minLength": 1,
            "pattern": "\\S",
        },
        "nonEmptyStringArray": {
            "type": "array",
            "items": {"$ref": "#/$defs/nonEmptyString"},
            "minItems": 1,
        },
        "triggerTest": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "query", "should_trigger"],
            "properties": {
                "id": {"$ref": "#/$defs/nonEmptyString"},
                "query": {"$ref": "#/$defs/nonEmptyString"},
                "should_trigger": {"type": "boolean"},
                "keywords": {"$ref": "#/$defs/nonEmptyStringArray"},
                "negative_keywords": {"$ref": "#/$defs/nonEmptyStringArray"},
            },
        },
        "taskTest": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "assertions"],
            "properties": {
                "id": {"$ref": "#/$defs/nonEmptyString"},
                "prompt": {"type": "string"},
                "assertions": {
                    "type": "array",
                    "items": {
                        "anyOf": [
                            {"$ref": "#/$defs/nonEmptyString"},
                            {"$ref": "#/$defs/assertionObject"},
                        ]
                    },
                    "minItems": 1,
                },
            },
        },
        "assertionObject": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "target": {
                    "type": "string",
                    "enum": ["text", "description", "body"],
                    "default": "text",
                },
                "contains": {"$ref": "#/$defs/nonEmptyString"},
                "not_contains": {"$ref": "#/$defs/nonEmptyString"},
                "any_contains": {"$ref": "#/$defs/nonEmptyStringArray"},
                "all_contains": {"$ref": "#/$defs/nonEmptyStringArray"},
            },
            "oneOf": [
                {"required": ["contains"]},
                {"required": ["not_contains"]},
                {"required": ["any_contains"]},
                {"required": ["all_contains"]},
            ],
        },
    },
}


def eval_schema_json() -> str:
    return json.dumps(EVAL_SCHEMA, indent=2, sort_keys=True) + "\n"
