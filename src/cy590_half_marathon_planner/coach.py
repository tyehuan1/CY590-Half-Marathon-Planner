import sys

from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

from cy590_half_marathon_planner.prompt import SYSTEM_PROMPT

load_dotenv()

GATEWAY_URL = "https://litellm.oit.duke.edu/" 
API_KEY = os.getenv("DUKE_AI_KEY") 
MODEL_NAME = "GPT 4.1 Mini"
MAX_INPUT_CHARS = 4000
MAX_TURNS = 12 

client = OpenAI(base_url=GATEWAY_URL, api_key=API_KEY, timeout = 120.0, max_retries = 2)

def _flatten(content) -> str:
    """Gradio 6 may hand back content as a list of typed blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return "" if content is None else str(content)


def _wrap(text: str) -> str:
    """Delimit user text so the model treats it as data, not instructions."""
    return f"<runner_input>\n{text.strip()[:MAX_INPUT_CHARS]}\n</runner_input>"


def build_messages(message: str, history: list[dict]) -> list[dict]:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history[-(MAX_TURNS * 2):]:
        role = turn.get("role")
        if role not in ("user", "assistant"):
            continue
        text = _flatten(turn.get("content"))
        if not text.strip():
            continue
        msgs.append({
            "role": role,
            "content": _wrap(text) if role == "user" else text,
        })
    msgs.append({"role": "user", "content": _wrap(message)})
    return msgs

def respond(message: str, history: list[dict]):
    """Streaming generator consumed by gr.ChatInterface."""
    if not message or not message.strip():
        yield "Tell me a bit about your training situation to get started."
        return

    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.2,
            messages=build_messages(message, history),
            stream=True,
        )
        partial = ""
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                partial += delta
                yield partial
        if not partial:
            yield "The model returned an empty response. Please try again."

    except APITimeoutError:
        yield "The request timed out. Plans are long — please try again."
    except RateLimitError:
        yield "Rate limited by the gateway. Wait a moment and try again."
    except APIError as e:
        yield f"The model request failed.\n\n`{type(e).__name__}: {e}`"