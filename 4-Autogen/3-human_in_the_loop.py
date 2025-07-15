import asyncio
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
import os


load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
model_client = OpenAIChatCompletionClient(model='gpt-4o-mini', api_key=api_key)


async def main():
    essay_generator = AssistantAgent(
        name='essay_generator',
        description='You are an essay generator',
        model_client=model_client,
        system_message='You generate essay on a given topic in less than 25 words in a simple language.'
    )

    user_proxy_agent = UserProxyAgent(
        name ='user_proxy',
        description='you are a user proxy agent',
        input_func=input
    )

    termination = TextMentionTermination("APPROVE")

    team = RoundRobinGroupChat([essay_generator, user_proxy_agent], termination_condition=termination)

    stream = team.run_stream(task="In favor of AI")
    await Console(stream)
    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
