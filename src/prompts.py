"""Prompt de sistema do artigo (Seção 3.2). O prompt de usuário é apenas o código da classe."""
from .refactorings import REFACTORINGS

FENCE = "`" * 3

SYSTEM_PROMPT_TEMPLATE = (
    "You are an AI that responds with source code and natural language. "
    "You will be given a Python class. Please apply the following refactorings "
    "(if applicable) to the given class.\n"
    "Refactorings: {refactorings}\n"
    "Please return the refactored class and the list of refactorings applied. "
    "The class must be encapsulated in a code block, like this:\n"
    + FENCE + "python\n"
    'print("Hello World!")\n'
    + FENCE + "\n"
    "The list of refactorings must be encapsulated in a text block, like this:\n"
    + FENCE + "text\n"
    "Refactoring 1, Refactoring 2, Refactoring 3\n"
    + FENCE
)


def build_system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(refactorings=", ".join(REFACTORINGS))


def build_user_prompt(task: dict) -> str:
    # No artigo: "The 'user' prompt is the dataset entry, i.e., the code of the class".
    return task["solution_code"]
