## Architecture: The Context-Aware "Compute Tax"

To ensure absolute privacy and add a layer of gamified accountability, **all focus assessment and response generation runs locally.** We do not stream your screen activity, private messages, or doom-scrolling habits to the cloud. 

When your accountability partner "pokes" you, your local sidecar agent assesses your recent activity logs. If you've drifted off-task, the system executes a "Compute Tax" to generate your punishment.

1. **Zero Data Exfiltration:** Your messy desktop and distracting tabs never leave your device.
2. **The Functional Tax:** Running a local LLM is computationally expensive. If the model catches you slacking, it spins up locally to ingest your recent usage data. The resulting CPU/GPU spike—making your fans scream—is the literal cost of the AI analyzing exactly *what* you are doing to generate a hyper-specific, quippy reprimand.
3. **The Roast:** The context-aware response is piped into **ElevenLabs**, delivering a custom, playful voice nudge directly to your headphones (e.g., *"Really? We're watching 45 minutes of mechanical keyboard sound tests instead of fixing the API route?"*).

### Tech Stack & Workflow

* **Mistral / Ministral:** The core reasoning engine. It analyzes local activity logs to determine focus levels and generates the context-aware roasts.
* **Nvidia Brev:** Our heavy-lifting development environment—used for running evaluations, tracing prompt quality with **W&B Weave**, and optimizing the model for edge deployment.
* **Local Inference:** The optimized Mistral model runs directly on the user's machine to process sensitive activity logs and execute the "Compute Tax."
* **ElevenLabs API:** Converts the LLM's custom roast into a high-quality, playful audio intervention.

---

### Developer Quickstart

**1. Model Optimization (Remote on Brev)**
* Spin up the Brev instance: `brev open <instance-name>`
* Run the evaluation suite (`evals/run_eval.py`) and trace the quality of the generated roasts using **W&B Weave**.

**2. Local Deployment (The Siphon & Roast)**
* Configure the local environment to run the optimized model directly on the metal. 
* Start the local sidecar: `python sidecar/main.py`
* The sidecar will passively monitor window/app logs. Upon receiving a network "poke," it will trigger the local LLM to assess focus, spike the compute, and generate the ElevenLabs audio response.