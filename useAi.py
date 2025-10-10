from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chunk_with_ai(sentence: str):
    prompt = f"Break this sentence into phrase-level chunks (NP, VP, PP): {sentence}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

print(chunk_with_ai("Students assemble in the quad with their teacher at the time of evacuation. The teacher will do a head count and check the roll."))
