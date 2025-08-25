from strands import Agent, tool
from strands.models.ollama import OllamaModel

import sqlite3
import json
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

con = sqlite3.connect("customer.db", check_same_thread=False)
cur = con.cursor()

# Generate tables
cur.execute("CREATE TABLE IF NOT EXISTS customer(ccid, fname, lname, channel_addr, metadata)")

# Create an Ollama model instance
ollama_model = OllamaModel(
    host="http://localhost:11434",  # Ollama server address
    model_id="qwen3:4b"               # Specify which model to use
)


@tool
def create_customer(ccid:str, fname:str, lname:str, channel_addr:str, metadata: dict):
    """Create a new customer with a ccid(primary id), first name, last name and channel address (phone number).

    Args:
        ccid: Customer id, primary key
        fname: Customer firstname
        lname: Customer last name
        channel_addr: customer phone number
        metadata: Dictionary of additional customer data to be stored as JSON
    """

    metadata_json = json.dumps(metadata)
    logger.info(metadata_json)
    try:
        with con:
            result = cur.execute("INSERT INTO customer VALUES (?, ?, ?, ?, ?)", (ccid, fname, lname, channel_addr, metadata_json))
            return result
    except Exception as e:
        logger.exception(f"Error inserting customer: {e}")
        raise

@tool
def get_customer(ccid:str):
    """Retrieves customer ifnormation by  ccid(primary id).

    Args:
        ccid: Customer id, primary key
    """
    try:
        with con:
            result = cur.execute("SELECT * FROM customer where ccid=?", (ccid,))
            return result.fetchone()
    except Exception as e:
        logger.exception(f"Error inserting customer: {e}")
        raise

@tool
def update_customer(ccid:str, fname:str, lname:str, channel_addr:str, metadata: dict):
    """Updates customer information by ccid(primary id).

    Args:
        ccid: Customer id, primary key
        fname: Customer firstname
        lname: Customer last name
        channel_addr: customer phone number
        metadata: Dictionary of additional customer data to be stored as JSON
    """
    try:
        with con:
            result = cur.execute("UPDATE customer SET fname=?, lname=?, channel_addr=?, metadata=? WHERE ccid=?", (fname, lname, channel_addr, json.dumps(metadata), ccid))
            return result
    except Exception as e:
        logger.exception(f"Error updating customer: {e}")
        raise

# Create an agent using the Ollama model
# agent = Agent(model=ollama_model, 
#               tools=[create_customer],
#               system_prompt="you are a helpful assisstant retrieving, updating, creating and remove customers from a database")

CUSTOMER_ASSISSTANT_PROMPT = """
you are a helpful assisstant retrieving, updating, creating and remove customers from a database:
- When creating customer first ensure no customer already exists with a given CCID
- If a customer does exist with a given CCID instead of creating a new one update the existing customer with relevant information 

Always select the most appropriate tool based on the user's query.
"""

@tool
def customer_assisstant(query: str) -> str:
    """
    Process and respond to customer-related queries.

    Args:
        query: A customer question requiring action

    Returns:
        Result of a customer action
    """
    try:
        # Strands Agents SDK makes it easy to create a specialized agent
        customer_assisstant = Agent(
            system_prompt=CUSTOMER_ASSISSTANT_PROMPT,
            tools=[create_customer, get_customer, update_customer]
        )

        # Call the agent and return its response
        response = customer_assisstant(query)
        return str(response)
    except Exception as e:
        return f"Error in research assistant: {str(e)}"

# print("""
#   <context>
#   {context}
#   <context>
  
#   <user prompt>
#   {prompt}
#   </user prompt>

#   Using the <context> provided give the answer the <user prompt>. Keep your answer grounded in the facts of the <context>. If the <context> doesn't contain the answer, say you don't know
# """.format(prompt=users_prompt, context=context["documents"]))


# agent("""
#   <user prompt>
#   {prompt}
#   </user prompt>

#   <context>
#   {context}
#   <context>

#   Using the <context> provided give the answer the <user prompt>. Keep your answer grounded in the facts of the <context>. If the <context> doesn't contain the answer, say you don't know
# """.format(prompt=users_prompt, context=context))