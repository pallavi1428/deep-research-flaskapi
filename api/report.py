from providers import get_model, trim_prompt
from prompt import system_prompt


def write_final_report(prompt: str, learnings: list[str], visited_urls: list[str]) -> str:
    model = get_model()
    formatted_learnings = "\n".join(f"<learning>\n{l}\n</learning>" for l in learnings)

    full_prompt = f"""
Write a comprehensive markdown research report based on the prompt and learnings below. The report should span at least 3 pages and include all insights. Add a "Sources" section at the end.

<prompt>{prompt}</prompt>

<learnings>
{formatted_learnings}
</learnings>
"""
    messages = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": trim_prompt(full_prompt)},
    ]

    report_body = model.generate(messages)

    urls_section = "\n\n## Sources\n" + "\n".join(f"- {url}" for url in visited_urls)
    return report_body.strip() + urls_section


def write_final_answer(prompt: str, learnings: list[str]) -> str:
    model = get_model()
    formatted_learnings = "\n".join(f"<learning>\n{l}\n</learning>" for l in learnings)

    full_prompt = f"""
Using the learnings below, write a short final answer to the user's original prompt. Be concise and respect the format of the original question if specified.

<prompt>{prompt}</prompt>

<learnings>
{formatted_learnings}
</learnings>
"""
    messages = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": trim_prompt(full_prompt)},
    ]

    return model.generate(messages).strip()
