from strands import Agent, tool
from strands.models.ollama import OllamaModel
import chromadb

chroma_client = chromadb.HttpClient(host='localhost', port=8000)

CONTENT_SYSTEM_PROMPT = """
You are an expert in customer communication creating personalized content. 

Your goal is to create engaging content for customers to interact with and provide valuable concise information that 
they can act on. 

Only output the generate content. Do not include any reasoning or notes simply the finished publishable content that can be sent to a customer


"""

# Create an Ollama model instance
ollama_model = OllamaModel(
    host="http://localhost:11434",  # Ollama server address
    model_id="qwen3:4b"               # Specify which model to use
)
agent = Agent(model=ollama_model, system_prompt=CONTENT_SYSTEM_PROMPT)

@tool
def generate_content(fname: str, lname: str, prompt: str):
    """Generates personalized content from a clients knowledge base and prompt

    Args:
        fname: Customer first name
        lanme: Customer last name
        prompts: instructions on what content to generate for a customer
    """

    # Create an agent using the Ollama model
    

    # Use the agent
    collection = chroma_client.get_collection("html_documents")
    context = collection.query(
        query_texts=[prompt],
        include=["documents"]
    )


    print("""
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


  