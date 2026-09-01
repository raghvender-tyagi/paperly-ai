import json
import re
from paperlyagents.nodes.utils import extract_text, load_prompt


def critic(state, llm):
    section = state['current_section']
    content = state.get(section, "")
    template = load_prompt("critic")
    prompt = template.format(section=section, content=content)

    response = llm.invoke(prompt)
    content_raw = extract_text(response.content).strip()

    critique = {"needs_rewrite": False, "improvements": []}
    try:
        clean_str = content_raw
        if "```json" in clean_str:
            clean_str = clean_str.split("```json")[1].split("```")[0]
        elif "```" in clean_str:
            clean_str = clean_str.split("```")[1].split("```")[0]
        critique = json.loads(clean_str.strip())
    except Exception:
        json_match = re.search(r'\{.*\}', content_raw, re.DOTALL)
        if json_match:
            try:
                critique = json.loads(json_match.group(0))
            except Exception:
                critique = {"needs_rewrite": False, "improvements": []}

    state['needs_rewrite'] = False
    state['improvements'] = critique.get('improvements', [])
    return state
