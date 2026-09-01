from paperlyagents.nodes.utils import extract_text, load_prompt


def generate_introduction(state, llm, progress_callback=None):
    if progress_callback:
        progress_callback("introduction")

    state['current_section'] = 'introduction'
    improvements_text = ""
    if state.get('improvements'):
        improvements_text = "PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:\n" + "\n".join(
            f"{i + 1}. {imp}" for i, imp in enumerate(state['improvements'])
        )

    template = load_prompt("introduction")
    prompt = template.format(
        topic=state['topic'],
        field=state['field'],
        level=state['level'],
        objectives=state['objectives'],
        novelty=state['novelty'],
        keywords=state['keywords'],
        improvements_text=improvements_text
    )

    response = llm.invoke(prompt)
    state['introduction'] = extract_text(response.content)
    state['improvements'] = []
    return state


def generate_literature_review(state, llm, progress_callback=None):
    if progress_callback:
        progress_callback("literature_review")

    state['current_section'] = 'literature_review'
    improvements_text = ""
    if state.get('improvements'):
        improvements_text = "PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:\n" + "\n".join(
            f"{i + 1}. {imp}" for i, imp in enumerate(state['improvements'])
        )

    template = load_prompt("literature_review")
    prompt = template.format(
        topic=state['topic'],
        field=state['field'],
        keywords=state['keywords'],
        novelty=state['novelty'],
        introduction=state.get('introduction', ''),
        improvements_text=improvements_text
    )

    response = llm.invoke(prompt)
    state['literature_review'] = extract_text(response.content)
    state['improvements'] = []
    return state


def generate_methodology(state, llm, progress_callback=None):
    if progress_callback:
        progress_callback("methodology")

    state['current_section'] = 'methodology'
    improvements_text = ""
    if state.get('improvements'):
        improvements_text = "PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:\n" + "\n".join(
            f"{i + 1}. {imp}" for i, imp in enumerate(state['improvements'])
        )

    template = load_prompt("methodology")
    prompt = template.format(
        topic=state['topic'],
        field=state['field'],
        objectives=state['objectives'],
        level=state['level'],
        introduction=state.get('introduction', ''),
        literature_review=state.get('literature_review', ''),
        improvements_text=improvements_text
    )

    response = llm.invoke(prompt)
    state['methodology'] = extract_text(response.content)
    state['improvements'] = []
    return state


def generate_conclusion(state, llm, progress_callback=None):
    if progress_callback:
        progress_callback("conclusion")

    state['current_section'] = 'conclusion'
    improvements_text = ""
    if state.get('improvements'):
        improvements_text = "PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:\n" + "\n".join(
            f"{i + 1}. {imp}" for i, imp in enumerate(state['improvements'])
        )

    template = load_prompt("conclusion")
    prompt = template.format(
        topic=state['topic'],
        objectives=state['objectives'],
        novelty=state['novelty'],
        introduction=state.get('introduction', ''),
        literature_review=state.get('literature_review', ''),
        methodology=state.get('methodology', ''),
        improvements_text=improvements_text
    )

    response = llm.invoke(prompt)
    state['conclusion'] = extract_text(response.content)
    state['improvements'] = []
    return state


def generate_abstract(state, llm, progress_callback=None):
    if progress_callback:
        progress_callback("abstract")

    state['current_section'] = 'abstract'
    improvements_text = ""
    if state.get('improvements'):
        improvements_text = "PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:\n" + "\n".join(
            f"{i + 1}. {imp}" for i, imp in enumerate(state['improvements'])
        )

    template = load_prompt("abstract")
    prompt = template.format(
        topic=state['topic'],
        field=state['field'],
        objectives=state['objectives'],
        novelty=state['novelty'],
        introduction=state.get('introduction', 'N/A'),
        methodology_snippet=state.get('methodology', 'N/A')[:200],
        improvements_text=improvements_text
    )

    response = llm.invoke(prompt)
    state['abstract'] = extract_text(response.content)
    state['improvements'] = []

    title_prompt = f"Abstract: {state['abstract']}\nGive an academic title. Output ONLY the title."
    title_res = llm.invoke(title_prompt)
    state['title'] = extract_text(title_res.content).strip()

    return state
