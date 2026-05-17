"""GCAO prompt template: Goal, Context, Action, Output."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PromptTemplate(BaseModel):
    """A GCAO-structured prompt as a first-class, validated object.

    GCAO is a framework for writing reusable prompts. Each field answers a
    specific question:
      - goal:    what success looks like
      - context: background the model needs to know
      - action:  the task or instructions to carry out
      - output:  the required format and structure of the response
      - examples: optional few-shot input/output pairs that anchor format

    Render the full prompt with .render(), or split it into a system prompt
    and a user message with .render_system_and_user(input_text).
    """

    goal: str = Field(min_length=1)
    context: str = Field(min_length=1)
    action: str = Field(min_length=1)
    output: str = Field(min_length=1)
    examples: list[dict] | None = None

    @field_validator("goal", "context", "action", "output")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be a non-empty string")
        return value

    @field_validator("examples")
    @classmethod
    def _validate_examples(cls, value: list[dict] | None) -> list[dict] | None:
        if value is None:
            return value
        if len(value) < 1:
            raise ValueError("examples, if provided, must have at least one item")
        for i, ex in enumerate(value):
            if "input" not in ex or "output" not in ex:
                raise ValueError(f"example {i} must have 'input' and 'output' keys")
        return value

    def render(self) -> str:
        """Return the full GCAO prompt as a single XML-tagged string."""
        parts = [
            f"<goal>\n{self.goal}\n</goal>",
            f"<context>\n{self.context}\n</context>",
            f"<action>\n{self.action}\n</action>",
            f"<output>\n{self.output}\n</output>",
        ]
        if self.examples:
            blocks = []
            for ex in self.examples:
                blocks.append(
                    "  <example>\n"
                    f"    <input>{ex['input']}</input>\n"
                    f"    <output>{ex['output']}</output>\n"
                    "  </example>"
                )
            parts.append("<examples>\n" + "\n".join(blocks) + "\n</examples>")
        return "\n\n".join(parts)

    def render_system_and_user(self, input_text: str) -> tuple[str, str]:
        """Split into (system_prompt, user_message). System holds the template;
        user holds only the input. This is the production pattern."""
        return self.render(), input_text
