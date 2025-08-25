from strands import Agent
from strands.models.ollama import OllamaModel
import chromadb

chroma_client = chromadb.HttpClient(host='localhost', port=8000)

# Create an Ollama model instance
ollama_model = OllamaModel(
    host="http://localhost:11434",  # Ollama server address
    model_id="qwen3:4b"               # Specify which model to use
)

# Create an agent using the Ollama model
agent = Agent(model=ollama_model, system_prompt="You are an expert marketer writing copy for businesses.")

# Use the agent

users_prompt = "What healthcare plans are available for me and my family? Im also a small business owner as well"
collection = chroma_client.get_collection("html_documents")
context = collection.query(
    query_texts=[users_prompt],
    include=["documents"]
)


print("""
  <context>
  {context}
  <context>
  
  <user prompt>
  {prompt}
  </user prompt>

  Using the <context> provided give the answer the <user prompt>. Keep your answer grounded in the facts of the <context>. If the <context> doesn't contain the answer, say you don't know
""".format(prompt=users_prompt, context=context["documents"]))


agent("""
  <user prompt>
  {prompt}
  </user prompt>

  <context>
  {context}
  <context>

  Using the <context> provided give the answer the <user prompt>. Keep your answer grounded in the facts of the <context>. If the <context> doesn't contain the answer, say you don't know
""".format(prompt=users_prompt, context=context))