

from langgraph.graph import StateGraph, END, START
from typing import TypedDict, List,Literal
import json

import os
import arxiv
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch


from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")



llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=api_key
)



#
# user_input = {
#     "topic": input("Give clear description of topic: "),
#     "field": input("Field? (Example: CS, Medicine, Business, etc): "),
#     "level": input("What level paper you want? (Undergraduate, Masters, PhD, Journal): "),
#     "objectives": input("What are you trying to prove/find? "),
#     "keywords": input("Enter keywords (comma separated): ")
# }
#



def rungraph(user_input):
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key
    )

    client = arxiv.Client()
    search = arxiv.Search(query=user_input["topic"], max_results=5)
    novelty_list = []
    papers = list(client.results(search))
    for idx, paper in enumerate(papers, start=1):
        abstract = paper.summary

        prompt = f"""
        Read the following research abstract and extract ONLY the novelty.
        {abstract}

        Write the novelty in 1-2  bullet points. Keep it crisp.
        """

        response1 = llm.invoke(prompt)
        novelty_list.append({
            "paper_title": paper.title,
            "novelty": response1.content
        })

    prompt = f"""
    You are an expert research scientist specializing in identifying research gaps and generating novel contributions.

    Your task:
    Given:
    1. The research topic.
    2. The novelty points extracted from the top 10 similar papers.

    Goal:
    → Generate a NEW novelty/contribution that is:
    - Highly unique
    - Not present in any of the existing papers
    - Has a very high chance of being unexplored in prior literature
    - Feasible and technically meaningful
    - Valuable for a real research paper or academic publication

    ### IMPORTANT RULES:
    - Do NOT repeat or rephrase any of the given novelties.
    - Identify hidden gaps, limitations, or missing angles.
    - Propose a contribution that solves a missing piece in the current research landscape.
    - Contribution must be concrete, implementable, and research-worthy.
    - Provide justification for why this novelty is likely unexplored.

    ### Provided Topic:
    {user_input["topic"]}

    ### Existing Novelties from 10 Papers:
    {novelty_list}

    ### Your Output:
    new novelty in 100 words

    Make the answer highly original, creative, and research-ready.
    """

    novelty = llm.invoke(prompt)

    print("\n===== NEW NOVELTY GENERATED =====\n")

    ## STATE ayegi
    class MainState(TypedDict, total=False):
        topic: str
        field: str
        keywords: str
        title:str
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

    ## GENERATORS
    def generate_introduction(state: MainState) -> MainState:
        state['current_section'] = 'introduction'
        improvements_text = ""
        if state.get('improvements'):
            improvements_text = f"""
        PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:
        {chr(10).join(f"{i + 1}. {imp}" for i, imp in enumerate(state['improvements']))}
        """

        prompt = f"""
        Write a detailed introduction section for a research paper.

        Topic: {state['topic']}
        Field: {state['field']}
        Level: {state['level']}
        Objectives: {state['objectives']}
        Novelty: {state['novelty']}
        Keywords: {state['keywords']}
        The introduction should include
        {improvements_text}
        1. Background and context
        2. Problem statement
        3. Research gap (based on novelty)
        4. Research objectives
        5. Paper structure overview
        everything should allign with given data 

        Write 500-700 words in academic tone.
        """

        response = llm.invoke(prompt)
        state['introduction'] = response.content
        state['improvements'] = []

        print("intro done ")
        return state

    def generate_literature_review(state: MainState) -> MainState:
        state['current_section'] = 'literature_review'
        improvements_text = ""
        if state.get('improvements'):
            improvements_text = f"""
        PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:
        {chr(10).join(f"{i + 1}. {imp}" for i, imp in enumerate(state['improvements']))}
        """

        prompt = f"""
        Write a aacurate literature review for a research paper.

        Topic: {state['topic']}
        Field: {state['field']}
        Keywords: {state['keywords']}
        Novelty/Research Gap: {state['novelty']}
        introduction :{state['introduction']}

        The literature review should:
        {improvements_text}
        1. Organize by themes/topics
        2. check  recent studies (2020-2024)
        3. Identify gaps in existing research
        4. Show how your work addresses these gaps
        5. Build towards the research gap mentioned in novelty

        Write 800-1000 words with proper academic structure.
        """

        response = llm.invoke(prompt)
        state['literature_review'] = response.content
        state['improvements'] = []

        print("Literature Review generated!")
        return state

    def generate_methodology(state: MainState) -> MainState:
        state['current_section'] = 'methodology'
        improvements_text = ""
        if state.get('improvements'):
            improvements_text = f"""
        PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:
        {chr(10).join(f"{i + 1}. {imp}" for i, imp in enumerate(state['improvements']))}
        """

        prompt = f"""
        Write a detailed methodology section for a research paper.

        Topic: {state['topic']}
        Field: {state['field']}
        Objectives: {state['objectives']}
        Level: {state['level']}
        introduction :{state['introduction']}
        literature review:{state['literature_review']} 

        The methodology should include:
        {improvements_text}
        1. Research design (qualitative/quantitative/mixed)
        2. Data collection methods
        3. Sample size and selection criteria
        4. Tools and techniques to be used
        5. Data analysis methods
        6. Justification for chosen methods

        Be specific and detailed. Write 600-800 words.
        """

        response = llm.invoke(prompt)
        state['methodology'] = response.content
        state['improvements'] = []
        print("Methodology generated!")
        return state

    def generate_conclusion(state: MainState) -> MainState:
        state['current_section'] = 'conclusion'
        improvements_text = ""
        if state.get('improvements'):
            improvements_text = f"""
        PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:
        {chr(10).join(f"{i + 1}. {imp}" for i, imp in enumerate(state['improvements']))}
        """

        prompt = f"""
        Write a strong conclusion section for a research paper.

        Topic: {state['topic']}
        Objectives: {state['objectives']}
        Novelty/Contribution: {state['novelty']}
        introduction :{state['introduction']}
        literature review:{state['literature_review']} 
        methodology:{state['methodology']}

        Based on the research context, write a conclusion that includes:
        {improvements_text}
        1. Summary of key findings/contributions
        2. How research objectives are addressed
        3. Significance and implications
        4. Limitations of the study
        5. Future research directions

        Write 400-500 words.
        """

        response = llm.invoke(prompt)
        state['conclusion'] = response.content
        state['improvements'] = []

        print("Conclusion generated!")
        return state

    def generate_abstract(state: MainState) -> MainState:
        state['current_section'] = 'abstract'
        improvements_text = ""
        if state.get('improvements'):
            improvements_text = f"""
        PREVIOUS ATTEMPT HAD THESE ISSUES - FIX THEM:
        {chr(10).join(f"{i + 1}. {imp}" for i, imp in enumerate(state['improvements']))}
        """

        prompt = f"""
        Write a comprehensive abstract for a research paper.

        Topic: {state['topic']}
        Field: {state['field']}
        Objectives: {state['objectives']}
        Novelty: {state['novelty']}

        Context from other sections:
        Introduction: {state.get('introduction', 'N/A')}
        Methodology: {state.get('methodology', 'N/A')[:200]}...

        The abstract should include:
        {improvements_text}
        1. Background (1-2 sentences)
        2. Research gap/problem
        3. Objectives
        4. Methodology brief
        5. Expected significance

        Write 150-250 words. Include 5-7 keywords at the end.
        """

        response = llm.invoke(prompt)
        state['abstract'] = response.content
        state['improvements'] = []
        prompt=f"""this is the abstract af an research paper i recently wrote :{state['abstract']}
        give the tilte that should sound academic and professional 
        output should contain only the tile """
        title=llm.invoke(prompt)
        state['title']=title.content

        print("Abstract generated!")
        return state

    def route_after_intro(state: MainState):
        return "introduction" if state.get('needs_rewrite') else "literature_review"

    def route_after_lit(state: MainState):
        return "literature_review" if state.get('needs_rewrite') else "methodology"

    def route_after_method(state: MainState):
        return "methodology" if state.get('needs_rewrite') else "conclusion"

    def route_after_concl(state: MainState):
        return "conclusion" if state.get('needs_rewrite') else "abstract"

    def route_after_abstract(state: MainState):
        return "abstract" if state.get('needs_rewrite') else "__end__"

    def critic(state: MainState) -> MainState:
        section = state['current_section']
        content = state.get(section, "")
        prompt = f"""
        You are a research paper reviewer. Check if this {section} needs rewriting.

        CONTENT:
        {content}

        Return ONLY a JSON object (no extra text):
        {{
            "needs_rewrite": true,
            "improvements": [
                "Specific improvement 1",
                "Specific improvement 2",
                "Specific improvement 3",
                "Specific improvement 4",
                "Specific improvement 5"
            ]
        }}

        Set "needs_rewrite" to true if:
        - Academic tone is weak
        - Structure is poor
        - Too short (< 400 words for intro/lit review)
        - Missing key elements
        - Logic gaps

        Otherwise set to false and provide 5 points on how to make it even better.
        """
        response = llm.invoke(prompt)
        content_raw = response.content.strip()

        if "```json" in content_raw:
            content_raw = content_raw.split("```json")[1].split("```")[0]
        elif "```" in content_raw:
            content_raw = content_raw.split("```")[1].split("```")[0]

        critique = json.loads(content_raw.strip())

        state['needs_rewrite'] = critique.get('needs_rewrite', False)
        state['improvements'] = critique.get('improvements', [])

        if 'retry_count' not in state:
            state['retry_count'] = 0

        if state.get('needs_rewrite', False):
            state['retry_count'] += 1
        else:
            state['retry_count'] = 0

        if state['retry_count'] >= 2:
            print(" Max retries reached, moving forward")
            state['needs_rewrite'] = False
            state['retry_count'] = 0

        return state

    graph = StateGraph(MainState)

    graph.add_node("introduction", generate_introduction)
    graph.add_node("critic_intro", critic)

    graph.add_node("literature_review", generate_literature_review)
    graph.add_node("critic_lit", critic)

    graph.add_node("methodology", generate_methodology)
    graph.add_node("critic_method", critic)

    graph.add_node("conclusion", generate_conclusion)
    graph.add_node("critic_concl", critic)

    graph.add_node("abstract", generate_abstract)

    graph.add_node("critic_abstract", critic)

    graph.add_edge(START, "introduction")
    graph.add_edge("introduction", "critic_intro")
    graph.add_conditional_edges(
        "critic_intro",
        route_after_intro,
        {
            "introduction": "introduction",
            "literature_review": "literature_review"
        }
    )

    graph.add_edge("literature_review", "critic_lit")
    graph.add_conditional_edges(
        "critic_lit",
        route_after_lit,
        {
            "literature_review": "literature_review",
            "methodology": "methodology"
        }
    )

    graph.add_edge("methodology", "critic_method")
    graph.add_conditional_edges(
        "critic_method",
        route_after_method,
        {
            "methodology": "methodology",
            "conclusion": "conclusion"
        }
    )

    graph.add_edge("conclusion", "critic_concl")
    graph.add_conditional_edges(
        "critic_concl",
        route_after_concl,
        {
            "conclusion": "conclusion",
            "abstract": "abstract"
        }
    )

    graph.add_edge("abstract", "critic_abstract")
    graph.add_conditional_edges(
        "critic_abstract",
        route_after_abstract,
        {
            "abstract": "abstract",
            "__end__": END
        }
    )

    app = graph.compile()

    initial_state = {
        "topic": user_input["topic"],
        "field": user_input["field"],
        "keywords": user_input["keywords"],
        "level": user_input["level"],
        "objectives": user_input["objectives"],
        "novelty": novelty,
        "introduction": "",
        "literature_review": "",
        "methodology": "",
        "conclusion": "",
        "abstract": "",
        "retry_count": 0,
        "needs_rewrite": False,
        "improvements": []
    }

    print("Starting Paper Generation...")
    result = app.invoke(initial_state)
    print(result)
    return (result)



# rungraph(user_input)