from strands import Agent, tool
# from strands.models.ollama import OllamaModel
import chromadb
from local_model.model import model as qwen
import logging

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)

chroma_client = chromadb.HttpClient(host='localhost', port=8000)

CONTENT_SYSTEM_PROMPT = """
You are an expert in customer communication creating personalized content. 
Use tools to create engaging content for customers to interact with and provide valuable concise information
Do not include any reasoning in your output
"""

# Create an Ollama model instance
# ollama_model = OllamaModel(
#     host="http://localhost:11434",  # Ollama server address
#     model_id="qwen3:4b"               # Specify which model to use
# )
agent = Agent(model=qwen, system_prompt=CONTENT_SYSTEM_PROMPT)

@tool
def generate_content(fname: str, lname: str, prompt: str):
    """Generates personalized content from a clients knowledge base and prompt

    Args:
        fname: Customer first name
        lname: Customer last name
        prompt: instructions on what content to generate for a customer
    """

    # Create an agent using the Ollama model
    

    # Use the agent
    collection = chroma_client.get_collection("html_documents")
    context = collection.query(
        query_texts=[prompt],
        include=["documents"]
    )

    agent("""
      <context>
      {context}
      <context>
      
      <customer info>
      {fname} {lname}
      </customer info>
          
      <user prompt>
      {prompt}
      </user prompt>


      Using the <context> provided give the answer the <user prompt>. 
      Keep your answer grounded in the facts of the <context>.
    """.format(prompt=prompt, context=context["documents"], fname=fname, lname=lname))


  