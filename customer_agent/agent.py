from typing import Optional
import sqlite3
import json
import logging
import sys

from strands import Agent, tool
from pydantic import BaseModel, Field
# from strands.models.ollama import OllamaModel

from local_model.model import model as gwen



class Customer(BaseModel):
    ccid: str
    fname: Optional[str]
    lname: Optional[str]
    channel_addr: Optional[str]

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

con = sqlite3.connect("customer.db", check_same_thread=False)
cur = con.cursor()

# Generate tables
cur.execute("CREATE TABLE IF NOT EXISTS customer(ccid, fname, lname, channel_addr, metadata)")


@tool
def create_customer(ccid:str, fname:str, lname:str, channel_addr:str, metadata: dict):
    """Create a new customer with a ccid(primary id), first name, last name and channel address (phone number).

    Args:
        ccid: Customer Id
        fname: Customer first name
        lname: Customer last name
        channel_addr: customer phone number
        metadata: Dictionary of additional customer data to be stored as JSON

    Returns:
        Customer
    """

    metadata_json = json.dumps(metadata)
    try:
        with con:
            cur.execute("INSERT INTO customer VALUES (?, ?, ?, ?, ?)", (ccid, fname, lname, channel_addr, metadata_json))
            return Customer(ccid=ccid, fname=fname,lname=lname,channel_addr=channel_addr)
    except Exception as e:
        logger.exception(f"Error inserting customer: {e}")
        raise

@tool
def get_customer(ccid:str):
    """Retrieves customer ifnormation by  ccid

    Args:
        ccid: Customer id, primary key
    
    Returns: 
        Customer
    """
    try:
        with con:
            result = cur.execute("SELECT * FROM customer where ccid=?", (ccid,))
            return Customer(ccid=ccid)
    except Exception as e:
        logger.exception(f"Error inserting customer: {e}")
        raise

@tool
def update_customer(ccid:str, fname:str, lname:str, channel_addr:str, metadata: dict):
    """Updates customer information by ccid

    Args:
        ccid: Customer id, primary key
        fname: Customer firstname
        lname: Customer last name
        channel_addr: customer phone number
        metadata: Dictionary of additional customer data to be stored as JSON

    Returns:
        Customer
    """
    try:
        with con:
            cur.execute("UPDATE customer SET fname=?, lname=?, channel_addr=?, metadata=? WHERE ccid=?", (fname, lname, channel_addr, json.dumps(metadata), ccid))
            return Customer(ccid=ccid, fname=fname,lname=lname,channel_addr=channel_addr)
    except Exception as e:
        logger.exception(f"Error updating customer: {e}")
        raise

CUSTOMER_ASSISSTANT_PROMPT = """
you are a helpful assisstant retrieving, updating, and creating customers

When handling requests, follow this priority order:

1. SEARCH FIRST: Always search for existing customers using the provided tools
2. DECISION LOGIC:
   - If customer found with a given CCID → UPDATE existing record
   - If no customer found → CREATE new customer 

Always select the most appropriate tool based on the user's query.
"""

@tool
def customer_assisstant(query: str) -> str:
    """
    Manage customers in a database

    Args:
        query: A request to retrieve, update, or create a Customer

    Returns:
        A Customer
    """
    try:
        # Strands Agents SDK makes it easy to create a specialized agent
        customer_assisstant = Agent(
            model=gwen,
            system_prompt=CUSTOMER_ASSISSTANT_PROMPT,
            tools=[create_customer, get_customer, update_customer]
        )

        # Call the agent and return its response
        response = customer_assisstant.structured_output(Customer, query)
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