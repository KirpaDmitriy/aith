import os

import openai
import pandas as pd
from langchain import OpenAI
from langchain.agents import create_pandas_dataframe_agent
from async_timeout import timeout

API_KEY = os.environ["GPTAPI"]


async def get_answer_gpt(message):
    openai.api_key = API_KEY
    messages = [{"role": "system", "content": "You are an intelligent assistant."}]
    if message:
        messages.append(
            {"role": "user", "content": message},
        )
        try:
            async with timeout(200):
                print("Chatting with ChatGPT")
                chat = await openai.ChatCompletion.acreate(
                    model="gpt-4",
                    temperature=0.3,
                    presence_penalty=0.1,
                    frequency_penalty=0.1,
                    messages=messages,
                )
                reply = chat.choices[0].message.content
                print("ChatGPT replied")
                return reply
        except Exception:
            print("ChatGPT timeout, cancel the task")


def create_agent(df: pd.DataFrame):
    llm = OpenAI(openai_api_key=API_KEY)
    return create_pandas_dataframe_agent(llm, df, verbose=False)


async def query_agent(agent, query):
    response = await agent.arun(query)
    return response.__str__()
