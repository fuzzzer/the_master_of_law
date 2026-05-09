"""
Case agent tool definitions — Gemini FunctionDeclaration schemas.

These tools let the AI agent modify case data through natural conversation.
Each tool maps to a CaseDetailCubit operation on the frontend's Hive-stored CaseData.
"""

from __future__ import annotations

from google.genai import types

DESTRUCTIVE_TOOLS = frozenset({
    "delete_fact",
    "delete_argument",
    "unlink_article",
    "delete_action_item",
})

CASE_TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_case_summary",
        description=(
            "Read the full case summary including all facts, arguments, evidence, "
            "strategy, risks, and action items. Use this to understand the current "
            "case state before suggesting modifications. "
            "საქმის სრული მიმოხილვის წაკითხვა."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={},
        ),
    ),
    types.FunctionDeclaration(
        name="add_fact",
        description=(
            "Add a new fact to the user's legal case. Use when the user mentions "
            "a new event, circumstance, or detail relevant to the case. "
            "ახალი ფაქტის დამატება საქმეში."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "text": types.Schema(
                    type=types.Type.STRING,
                    description="The fact description. ფაქტის აღწერა.",
                ),
                "classification": types.Schema(
                    type=types.Type.STRING,
                    enum=["favorable", "unfavorable", "neutral"],
                    description="How this fact affects the case. ფაქტის კლასიფიკაცია.",
                ),
            },
            required=["text", "classification"],
        ),
    ),
    types.FunctionDeclaration(
        name="edit_fact",
        description=(
            "Modify an existing fact's text or classification. "
            "არსებული ფაქტის რედაქტირება."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "fact_id": types.Schema(
                    type=types.Type.STRING,
                    description="The ID of the fact to edit.",
                ),
                "text": types.Schema(
                    type=types.Type.STRING,
                    description="New text for the fact (optional).",
                ),
                "classification": types.Schema(
                    type=types.Type.STRING,
                    enum=["favorable", "unfavorable", "neutral"],
                    description="New classification (optional).",
                ),
            },
            required=["fact_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="delete_fact",
        description=(
            "Remove a fact from the case. This is destructive and requires user confirmation. "
            "ფაქტის წაშლა საქმიდან."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "fact_id": types.Schema(
                    type=types.Type.STRING,
                    description="The ID of the fact to delete.",
                ),
            },
            required=["fact_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="add_argument",
        description=(
            "Add a legal argument supporting the case. "
            "იურიდიული არგუმენტის დამატება."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "title": types.Schema(
                    type=types.Type.STRING,
                    description="Short title of the argument. არგუმენტის სათაური.",
                ),
                "explanation": types.Schema(
                    type=types.Type.STRING,
                    description="Detailed explanation of the argument. არგუმენტის განმარტება.",
                ),
                "strength": types.Schema(
                    type=types.Type.STRING,
                    enum=["strong", "moderate", "weak"],
                    description="How strong this argument is. არგუმენტის სიძლიერე.",
                ),
            },
            required=["title", "explanation", "strength"],
        ),
    ),
    types.FunctionDeclaration(
        name="delete_argument",
        description=(
            "Remove an argument from the case. Destructive — requires confirmation. "
            "არგუმენტის წაშლა."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "argument_id": types.Schema(
                    type=types.Type.STRING,
                    description="The ID of the argument to delete.",
                ),
            },
            required=["argument_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="link_article",
        description=(
            "Link a law article to the case for reference. "
            "კანონის მუხლის მიბმა საქმეზე."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "code_name": types.Schema(
                    type=types.Type.STRING,
                    description="Name of the legal code (e.g. 'სისხლის სამართლის კოდექსი').",
                ),
                "article_number": types.Schema(
                    type=types.Type.STRING,
                    description="Article number (e.g. 'მუხლი 177').",
                ),
                "snippet": types.Schema(
                    type=types.Type.STRING,
                    description="Brief relevant excerpt or explanation.",
                ),
            },
            required=["code_name", "article_number", "snippet"],
        ),
    ),
    types.FunctionDeclaration(
        name="unlink_article",
        description=(
            "Remove a linked law article from the case. Destructive — requires confirmation. "
            "მუხლის მოხსნა საქმიდან."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "article_id": types.Schema(
                    type=types.Type.STRING,
                    description="The ID of the linked article to remove.",
                ),
            },
            required=["article_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="set_strategy",
        description=(
            "Set or update the case defense strategy. "
            "დაცვის სტრატეგიის დაყენება."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "primary": types.Schema(
                    type=types.Type.STRING,
                    description="Primary defense strategy description. მთავარი სტრატეგია.",
                ),
                "backup": types.Schema(
                    type=types.Type.STRING,
                    description="Backup strategy if primary fails (optional). სარეზერვო სტრატეგია.",
                ),
                "confidence": types.Schema(
                    type=types.Type.INTEGER,
                    description="Confidence score 0-100. ნდობის ქულა.",
                ),
            },
            required=["primary", "confidence"],
        ),
    ),
    types.FunctionDeclaration(
        name="add_action_item",
        description=(
            "Add a to-do item to the case action checklist. "
            "დავალების დამატება."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "task": types.Schema(
                    type=types.Type.STRING,
                    description="Description of what needs to be done. დავალების აღწერა.",
                ),
                "priority": types.Schema(
                    type=types.Type.STRING,
                    enum=["high", "medium", "low"],
                    description="Priority level. პრიორიტეტი.",
                ),
                "deadline": types.Schema(
                    type=types.Type.STRING,
                    description="Deadline description (e.g. 'Within 48h', 'Before court'). ვადა.",
                ),
            },
            required=["task", "priority"],
        ),
    ),
    types.FunctionDeclaration(
        name="complete_action_item",
        description=(
            "Mark an action item as completed. "
            "დავალების შესრულებულად მონიშვნა."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "item_id": types.Schema(
                    type=types.Type.STRING,
                    description="The ID of the action item to mark done.",
                ),
            },
            required=["item_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="delete_action_item",
        description=(
            "Remove an action item from the checklist. Destructive — requires confirmation. "
            "დავალების წაშლა."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "item_id": types.Schema(
                    type=types.Type.STRING,
                    description="The ID of the action item to delete.",
                ),
            },
            required=["item_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="add_risk",
        description=(
            "Add a risk or weakness assessment to the case. "
            "რისკის/სისუსტის დამატება."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "description": types.Schema(
                    type=types.Type.STRING,
                    description="Description of the risk. რისკის აღწერა.",
                ),
                "severity": types.Schema(
                    type=types.Type.STRING,
                    enum=["high", "medium", "low"],
                    description="How severe this risk is. სიმძიმე.",
                ),
                "mitigation": types.Schema(
                    type=types.Type.STRING,
                    description="Suggested mitigation strategy (optional). შერბილების გზა.",
                ),
            },
            required=["description", "severity"],
        ),
    ),
]

CASE_TOOLS = [types.Tool(function_declarations=CASE_TOOL_DECLARATIONS)]
