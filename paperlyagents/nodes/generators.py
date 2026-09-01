from paperlyagents.nodes.utils import extract_text, load_prompt


from paperlyagents.nodes.utils import extract_text, load_prompt


def generate_introduction(state, llm, progress_callback=None):
    if progress_callback:
        progress_callback("introduction")

    state_copy = dict(state)
    improvements_text = ""
    if state_copy.get('improvements'):
        improvements_text = "PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:\n" + "\n".join(
            f"{i + 1}. {imp}" for i, imp in enumerate(state_copy['improvements'])
        )

    template = load_prompt("introduction")
    prompt = template.format(
        topic=state_copy['topic'],
        field=state_copy['field'],
        level=state_copy['level'],
        objectives=state_copy['objectives'],
        novelty=state_copy.get('novelty', ''),
        keywords=state_copy['keywords'],
        improvements_text=improvements_text
    )

    response = llm.invoke(prompt)
    return extract_text(response.content)


def generate_literature_review(state, llm, progress_callback=None):
    if progress_callback:
        progress_callback("literature_review")

    state_copy = dict(state)
    improvements_text = ""
    if state_copy.get('improvements'):
        improvements_text = "PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:\n" + "\n".join(
            f"{i + 1}. {imp}" for i, imp in enumerate(state_copy['improvements'])
        )

    template = load_prompt("literature_review")
    prompt = template.format(
        topic=state_copy['topic'],
        field=state_copy['field'],
        keywords=state_copy['keywords'],
        novelty=state_copy.get('novelty', ''),
        introduction=state_copy.get('introduction', ''),
        improvements_text=improvements_text
    )

    response = llm.invoke(prompt)
    return extract_text(response.content)


def generate_methodology(state, llm, progress_callback=None):
    if progress_callback:
        progress_callback("methodology")

    state_copy = dict(state)
    improvements_text = ""
    if state_copy.get('improvements'):
        improvements_text = "PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:\n" + "\n".join(
            f"{i + 1}. {imp}" for i, imp in enumerate(state_copy['improvements'])
        )

    template = load_prompt("methodology")
    prompt = template.format(
        topic=state_copy['topic'],
        field=state_copy['field'],
        objectives=state_copy['objectives'],
        level=state_copy['level'],
        introduction=state_copy.get('introduction', ''),
        literature_review=state_copy.get('literature_review', ''),
        improvements_text=improvements_text
    )

    response = llm.invoke(prompt)
    return extract_text(response.content)


def generate_conclusion(state, llm, progress_callback=None):
    if progress_callback:
        progress_callback("conclusion")

    state_copy = dict(state)
    improvements_text = ""
    if state_copy.get('improvements'):
        improvements_text = "PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:\n" + "\n".join(
            f"{i + 1}. {imp}" for i, imp in enumerate(state_copy['improvements'])
        )

    template = load_prompt("conclusion")
    prompt = template.format(
        topic=state_copy['topic'],
        objectives=state_copy['objectives'],
        novelty=state_copy.get('novelty', ''),
        introduction=state_copy.get('introduction', ''),
        literature_review=state_copy.get('literature_review', ''),
        methodology=state_copy.get('methodology', ''),
        improvements_text=improvements_text
    )

    response = llm.invoke(prompt)
    return extract_text(response.content)


def generate_abstract(state, llm, progress_callback=None):
    if progress_callback:
        progress_callback("abstract")

    state_copy = dict(state)
    improvements_text = ""
    if state_copy.get('improvements'):
        improvements_text = "PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:\n" + "\n".join(
            f"{i + 1}. {imp}" for i, imp in enumerate(state_copy['improvements'])
        )

    template = load_prompt("abstract")
    prompt = template.format(
        topic=state_copy['topic'],
        field=state_copy['field'],
        objectives=state_copy['objectives'],
        novelty=state_copy.get('novelty', ''),
        introduction=state_copy.get('introduction', 'N/A'),
        methodology_snippet=state_copy.get('methodology', 'N/A')[:200],
        improvements_text=improvements_text
    )

    response = llm.invoke(prompt)
    return extract_text(response.content)

