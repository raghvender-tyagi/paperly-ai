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


def fetch_arxiv_papers(query):
    try:
        client = arxiv.Client(page_size=3, delay_seconds=0.5, num_retries=1)
        search = arxiv.Search(query=query, max_results=3)
        papers = list(client.results(search))
        if papers:
            return [f"- {p.title}: {p.summary[:200]}..." for p in papers]
    except Exception as e:
        print(f"arXiv search timeout/error: {e}")
    return []


def rungraph(user_input, progress_callback=None):
    llm = get_llm()

    if progress_callback:
        progress_callback("Analyzing prior research & novelty")

    novelty_list = []
    with ThreadPoolExecutor(max_workers=1) as arxiv_executor:
        future = arxiv_executor.submit(fetch_arxiv_papers, user_input["topic"])
        try:
            novelty_list = future.result(timeout=2.0)
        except Exception:
            print("arXiv query timed out after 2 seconds, proceeding with default context.")

    template = load_prompt("novelty")
    prompt = template.format(
        topic=user_input["topic"],
        objectives=user_input["objectives"],
        prior_literature="\n".join(novelty_list) if novelty_list else "No prior literature fetched."
    )

    novelty_res = llm.invoke(prompt)
    novelty_text = extract_text(novelty_res.content)

    state = {
        "topic": user_input["topic"],
        "field": user_input["field"],
        "keywords": user_input["keywords"],
        "level": user_input["level"],
        "objectives": user_input["objectives"],
        "novelty": novelty_text,
        "introduction": "",
        "literature_review": "",
        "methodology": "",
        "conclusion": "",
        "abstract": "",
        "title": user_input["topic"],
        "retry_count": 0,
        "needs_rewrite": False,
        "improvements": []
    }

    if progress_callback:
        progress_callback("Generating all paper sections in parallel")

    def run_intro():
        return generate_introduction(state, llm)

    def run_lit():
        return generate_literature_review(state, llm)

    def run_method():
        return generate_methodology(state, llm)

    def run_concl():
        return generate_conclusion(state, llm)

    def run_abstr():
        return generate_abstract(state, llm)

    with ThreadPoolExecutor(max_workers=5) as executor:
        f_intro = executor.submit(run_intro)
        f_lit = executor.submit(run_lit)
        f_method = executor.submit(run_method)
        f_concl = executor.submit(run_concl)
        f_abstr = executor.submit(run_abstr)

        state["introduction"] = f_intro.result()
        state["literature_review"] = f_lit.result()
        state["methodology"] = f_method.result()
        state["conclusion"] = f_concl.result()
        state["abstract"] = f_abstr.result()

    # Generate academic title from abstract
    try:
        title_prompt = f"Topic: {state['topic']}\nAbstract: {state['abstract'][:300]}\nGenerate a concise academic title. Output ONLY the title."
        title_res = llm.invoke(title_prompt)
        state["title"] = extract_text(title_res.content).strip().strip('"')
    except Exception:
        state["title"] = state["topic"]

    return state


