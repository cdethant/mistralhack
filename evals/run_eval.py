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
async def focus_model(input_text: str) -> dict:
    prompt = f"""
    Analyze the following user activity log and determine if the user is focused on their primary task.
    Primary Task: Hackathon project development.
    
    Log:
    {input_text}
    
    Response format: JSON with fields: 'is_focused' (bool), 'score' (int 1-10), 'insight' (string).
    """
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            LLM_ENDPOINT,
            json={
                "model": "mistralai/Ministral-8B-Instruct-2410",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0
            }
        )
        # In a real scenario, we'd parse the JSON from the model's text response
        # This is a placeholder for the evaluation logic
        return {"is_focused": True, "score": 8}

def focus_scorer(model_output, expected):
    return {
        "score_match": abs(model_output["score"] - expected["score"]) <= 2,
        "is_focused_match": model_output["is_focused"] == expected["is_focused"]
    }

async def main():
    weave.init("mistral-hackathon-focus")
    
    with open("evals/focus_dataset.json", "r") as f:
        dataset = json.load(f)
    
    evaluation = weave.Evaluation(
        dataset=dataset,
        scorers=[focus_scorer],
    )
    
    await evaluation.evaluate(focus_model)

if __name__ == "__main__":
    asyncio.run(main())
