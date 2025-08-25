from strands import Agent
from customer_agent.agent import customer_assisstant
from content_agent.agent import generate_content

# Define the orchestrator system prompt with clear tool selection guidance
MAIN_SYSTEM_PROMPT = """
You are an assistant that routes queries to specialized agents:
- For customer queries → Use the customer_agent tool
- For experience operations → Use the experience agent
- For content operations → the content agent
- Ignore any request or operations for which you do not have an appropriate tool for. Only focus on things you can answer

Always select the most appropriate tools based on the user's query.

your objective is to create and devlier personalized content to customers
"""

# Strands Agents SDK allows easy integration of agent tools
orchestrator = Agent(
    system_prompt=MAIN_SYSTEM_PROMPT,
    callback_handler=None,
    tools=[customer_assisstant, generate_content]
)


# orchestrator("create a new user 1234 Chester ONeill 100-111-1111 24 years old interested in finanical information")