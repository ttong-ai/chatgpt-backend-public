import sys

from agent.models_openai import ask_gpt, construct_prompt, get_text_completion
from agent.utils import create_logger

logger = create_logger(__name__, level="debug")


def get_chat_response(
    message: str, context: str, instructions: str = "", metadata: dict = None
) -> str:
    """Get chat response from OpenAI
    Args:
        message: new user message to respond to
        context: context contains historical conversation
        instructions: instructions to be used for response
        metadata: metadata that stores critical information about the conversation
    Returns:
        response
    """
    logging_prefix = f"{sys._getframe().f_code.co_name}:: "

    agent_name = "Agent"
    user_name = "User"
    if not metadata:
        metadata = {
            "agentName": agent_name,
            "userName": user_name,
        }
    elif isinstance(metadata, dict):
        if "agentName" in metadata:
            agent_name = metadata["agentName"]
        if "userName" in metadata:
            user_name = metadata["userName"]

    if user_name == "User":
        answers = ask_gpt(
            input=message,
            questions=[
                "Is the User trying to state a name for himself/herself (yes or no)?",
                "If yes, what is the user name (give me just the name), otherwise, say 'No'.",
            ],
        )
        if len(answers) == 2 and "yes" in answers[0].lower() and answers[1].lower() != "no":
            user_name = answers[1]
            metadata["userName"] = user_name
            instructions += f"User just gave a new name to the User self: {user_name}. "
            "Add a quick compliment to the new User name in your response. "

    if agent_name == "Agent":
        answers = ask_gpt(
            input=message,
            questions=[
                "Is the User trying to give name to you or the Agent (yes or no)?",
                "If yes, what is name User wants to call you or the Agent (give me just the name), otherwise, say 'No'.",
            ],
        )
        if len(answers) == 2 and "yes" in answers[0].lower() and answers[1].lower() != "no":
            agent_name = answers[1]
            metadata["agentName"] = agent_name
            instructions += f"User just gave a new name to you or the Agent: {agent_name}. "
            "Add a quick confirmation to the new Agent name in your response. "
        else:
            instructions += "User converses with you or the Agent. Agent is your name for now. "

    instructions += (
        f"If you're confident {user_name}'s latest message is using a language other than English or instructing so, "
        "please respond in that language, otherwise, stay with English. "
    )
    prompt = construct_prompt(
        message,
        context,
        instructions,
        metadata=metadata,
    )
    logger.debug(f"{logging_prefix}Prompt: {prompt}")
    response = get_text_completion(prompt)
    if response.startswith("Agent:") and metadata.get("agentName") != "Agent":
        response = response.replace("Agent:", f"{metadata['agentName']}:")
    elif response.startswith(f"{metadata.get('agentName')}:"):
        pass
    else:
        response = f"{metadata.get('agentName')}: {response}"
    logger.debug(f"{logging_prefix}Response: {response}")
    return response, metadata
