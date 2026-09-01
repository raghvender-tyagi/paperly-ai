from typing import TypedDict
from concurrent.futures import ThreadPoolExecutor
import arxiv

from paperlyagents.nodes.utils import get_llm, extract_text, load_prompt
from paperlyagents.nodes.generators import (
    generate_introduction,
    generate_literature_review,
    generate_methodology,
    generate_conclusion,
    generate_abstract,
)


class MainState(TypedDict, total=False):
    topic: str
    field: str
    keywords: str
    title: str
    level: str
    objectives: str
    novelty: str
    introduction: str
    literature_review: str
    methodology: str
    conclusion: str
    abstract: str
    current_section: str
    needs_rewrite: bool
    improvements: list
    retry_count: int


def rungraph(user_input, progress_callback=None):
    llm = get_llm()

    if progress_callback:
        progress_callback("novelty")

    novelty_list = []
    try:
        client = arxiv.Client()
        search = arxiv.Search(query=user_input["topic"], max_results=3)
        papers = list(client.results(search))
        if papers:
            novelty_list = [f"- {p.title}: {p.summary[:200]}..." for p in papers]
    except Exception as e:
        print(f"arXiv search warning: {e}")

    template = load_prompt("novelty")
    prompt = template.format(
        topic=user_input["topic"],
        objectives=user_input["objectives"],
        prior_literature="\n".join(novelty_list) if novelty_list else "No prior literature fetched."
    )

    novelty_res = llm.invoke(prompt)
    novelty = extract_text(novelty_res.content)

    state = {
        "topic": user_input["topic"],
        "field": user_input["field"],
        "keywords": user_input["keywords"],
        "level": user_input["level"],
        "objectives": user_input["objectives"],
        "novelty": extract_text(novelty),
        "introduction": "",
        "literature_review": "",
        "methodology": "",
        "conclusion": "",
        "abstract": "",
        "retry_count": 0,
        "needs_rewrite": False,
        "improvements": []
    }

    if progress_callback:
        progress_callback("generating sections (parallel)")

    def run_intro():
        st = dict(state)
        res = generate_introduction(st, llm)
        return res.get("introduction", "")

    def run_lit():
        st = dict(state)
        res = generate_literature_review(st, llm)
        return res.get("literature_review", "")

    def run_method():
        st = dict(state)
        res = generate_methodology(st, llm)
        return res.get("methodology", "")

    with ThreadPoolExecutor(max_workers=3) as executor:
        f_intro = executor.submit(run_intro)
        f_lit = executor.submit(run_lit)
        f_method = executor.submit(run_method)

        state["introduction"] = f_intro.result()
        state["literature_review"] = f_lit.result()
        state["methodology"] = f_method.result()

    if progress_callback:
        progress_callback("conclusion")
    state = generate_conclusion(state, llm)

    if progress_callback:
        progress_callback("abstract")
    state = generate_abstract(state, llm)

    return state

