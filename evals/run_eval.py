import weave
import json
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Define the model / endpoint to evaluate
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8000/v1/chat/completions")

@weave.op()
async def focus_model(input: str) -> str | None:
    prompt = f"""You are a focus guardian for a hackathon developer.
Analyze the following sequence of active window snapshots and determine if the user has gone off-task.
Primary Task: Hackathon project development.

Window Log:
{input}

Rules:
- If the user is on-task (coding, terminal, docs, relevant research, team comms), respond with exactly: null
- If the user is clearly off-task (social media, shopping, entertainment, unrelated browsing), respond with a single short, quippy roast in plain text. No JSON, no quotes, just the roast.
- Be concise and funny. Do not over-explain.
"""

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                LLM_ENDPOINT,
                json={
                    "model": "mistralai/Ministral-8B-Instruct-2410",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
                timeout=30.0
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"].strip()
                return None if content.lower() == "null" else content
            else:
                return None
        except Exception:
            return None

def focus_scorer(output, expected):
    """
    Evaluator: checks whether the model correctly identified on-task vs off-task.
    - expected expected=null → user is on task, model should return None
    - expected expected=string → user is off task, model should return a non-None string
    """
    expected_on_task = (expected is None)
    model_on_task = (output is None)
    return {
        "correct": expected_on_task == model_on_task,
    }

async def main():
    weave.init("mistral-hackathon-focus")

    dataset_path = os.path.join(os.path.dirname(__file__), "focus_dataset.json")
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    evaluation = weave.Evaluation(
        dataset=dataset,
        scorers=[focus_scorer],
    )

    await evaluation.evaluate(focus_model)

if __name__ == "__main__":
    asyncio.run(main())
