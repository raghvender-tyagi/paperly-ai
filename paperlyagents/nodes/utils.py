import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None


def extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                if "text" in part:
                    text_parts.append(str(part["text"]))
                elif "content" in part:
                    text_parts.append(str(part["content"]))
            elif hasattr(part, "text"):
                text_parts.append(str(part.text))
            else:
                text_parts.append(str(part))
        return "\n".join(text_parts)
    return str(content)


def load_prompt(prompt_name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", f"{prompt_name}.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def get_llm():
    load_dotenv()
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key and gemini_key != "your_gemini_api_key_here":
        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
        if ChatGoogleGenerativeAI is not None:
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=gemini_key
            )
        return ChatOpenAI(
            model=model_name,
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=openai_key
    )
