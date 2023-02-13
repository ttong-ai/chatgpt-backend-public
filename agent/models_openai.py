import json
import openai
import os
import re
import sys
from typing import Optional, List

from agent.utils import create_logger


logger = create_logger(__name__, level="debug")
openai.api_key = os.getenv("OPENAI_API_KEY", "<YOUR_OPEN_API_KEY>")


class OpenAIError(Exception):
    """OpenAI Error"""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


def get_text_completion(
    text,
    model: str = None,
    max_tokens: int = 1000,
    temperature=0.9,
    top_p: float = 1.0,
    frequency_penalty: float = 1.0,
    presence_penalty: float = 0.0,
    best_of: int = 1,
) -> Optional[str]:
    """Using text-davinci-003 for general text completion at the end of prompt
    Will implement a max text length of 4096 characters (backwards from the end of the text)
    Args:
        text: text to complete
        model: model to use
        max_tokens: maximum number of tokens to return
        temperature: temperature of 0.0 is no randomness, 1.0 is maximum randomness
        top_p: controls diversity of returned tokens
        frequency_penalty: penalize new tokens based on their existing frequency in the text so far
        presence_penalty: penalize new tokens based on whether they appear in the text so far
    Returns:
        text completion

    """
    logging_prefix = f"{sys._getframe().f_code.co_name}:: "
    if not model:
        model = "text-davinci-003"
    if len(text) > 4096:
        text = text[-4096:]
    try:
        response = openai.Completion.create(
            model=model,
            prompt=text,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            best_of=best_of,
        )
        logger.debug(f"{logging_prefix}{json.dumps(response)}")
        return response["choices"][0]["text"].replace("[Response]", "").strip()
    except openai.error.InvalidRequestError as e:
        logger.error(f"{logging_prefix}OpenAI Invalid Request: {e}")
        return
    except Exception as e:
        logger.error(f"{logging_prefix}OpenAI Request Error: {e}")
        return


def construct_prompt(
    message: str, context: str, instructions: str = None, metadata: dict = None
) -> str:
    """Construct a prompt for OpenAI
    Args:
        message: message from user
        context: context from previous messages
        instructions: instructions for the chatbot
    Returns:
        prompt
    """
    logging_prefix = f"{sys._getframe().f_code.co_name}:: "

    if message.startswith("User:") and metadata.get("userName") != "User":
        message = message.replace("User:", f"{metadata['userName']}:")

    prompt = f"""[Context]
{context}
[New Message]
{message}
"""
    if instructions:
        prompt += f"[Hidden Instructions]\n({instructions})"
    return prompt


def parse_output(output: str, answers_tag: str = "[Concise Answers]"):
    """Parse the output from OpenAI"""
    answers_tag_pattern = (
        answers_tag.replace("[", r"\[").replace("]", r"\]").replace("*", r"\*").replace("-", r"\-").replace("(", r"\(").replace(")", r"\)")
    )
    match = re.search(rf"(?:{answers_tag_pattern})(.*)", output, re.DOTALL)
    output = []
    if match.group(1):
        sents = match.group(1).strip().split("\n")
        for i, s in enumerate(sents):
            if not s.startswith(f"{i+1}."):
                s = f"{i+1}. {s}"
            m = re.search(r"(?:(\d+). )(.*)", s)
            try:
                if m and int(m.group(1)) == i + 1:
                    output.append(m.group(2))
            except:
                break
    return output


def ask_gpt(
    input: str,
    questions: List[str],
    input_tag: str = "[Input]",
    questions_tag: str = "[Questions]",
    answers_tag: str = "[Concise Answers (one answer per question on a newline with cardinal number at the beginning of the line, e.g. 1. answer)]",
    max_tokens_per_question: int = 30,
    temperature: float = 0.2,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 1.0,
):
    logging_prefix = f"{sys._getframe().f_code.co_name}:: "

    if not questions or not input:
        return
    q_str = ""
    for i, q in enumerate(questions):
        if isinstance(q, str):
            q = q.replace("\n", " ").replace("\t", " ").strip()
        else:
            q = ""
        q_str = q_str + f"{i+1}. {q}\n"
    try:
        prompt = f"{input_tag}\n{input.strip()}\n\n{questions_tag}\n{q_str}\n{answers_tag}\n"
        logger.debug(f"{logging_prefix}{prompt}")
        answers = get_text_completion(
            text=prompt,
            max_tokens=max_tokens_per_question * len(questions),
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        if answers is None:
            logger.error(f"{logging_prefix}Empty response from OpenAI request")
            return
        answers = f"{answers_tag}\n{answers}"
        logger.debug(f"{logging_prefix}{answers}")
        return parse_output(answers, answers_tag=answers_tag)
    except Exception as e:
        raise OpenAIError(e)
