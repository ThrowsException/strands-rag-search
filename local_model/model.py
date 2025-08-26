from strands.models.ollama import OllamaModel
from strands.models.bedrock import BedrockModel

# model = OllamaModel(
#     host="http://localhost:11434",  # Ollama server address
#     model_id="qwen3:8b",               # Specify which model to use
#     temperature=0.1,
# )

model = BedrockModel(
  model_id="amazon.nova-micro-v1:0"
)