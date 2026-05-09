"""DeepSeek LLM integration via LangChain ChatOpenAI compatible interface"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()


class DeepSeekLLM:
    def __init__(self, temperature=0.1, max_tokens=4096):
        self.chat = ChatOpenAI(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def invoke(self, system_prompt, user_prompt):
        """Send a system + user message and return the text response."""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = self.chat.invoke(messages)
        return response.content
