from openai import OpenAI
from decouple import config

client = OpenAI(
    api_key=config("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

response = client.chat.completions.create(
    max_tokens=1024,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Give me 5 names of animals"},
    ],
    model=config("DEEPSEEK_MODEL"),
)
print(response.choices[0].message.content)