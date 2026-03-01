## Pipeline: Brev → Quantize → Siphon → Local

This is the full 4-stage pipeline from cloud evaluation to local "Compute Tax" inference.

### Stage 1: Brev — Eval Baseline

Run the vLLM server on your GPU instance to validate the roast quality.

```bash
brev shell optiministral
git clone <repo>
cd mistralhack
bash brev/setup.sh        # Install vLLM + weave
bash brev/serve.sh        # Launch Ministral-8B on port 8000
```

Then, from your **local machine**, open an SSH port-forward tunnel:
```bash
# In a dedicated terminal — forwards localhost:8000 → Brev:8000
ssh -N -L 8000:localhost:8000 optiministral
```
*(Brev writes the SSH host config to `~/.ssh/config` automatically.)*

Then run evals in a second terminal:
```bash
LLM_ENDPOINT=http://localhost:8000/v1/chat/completions python evals/run_eval.py
```

---

### Stage 2: Quantize — Compress on Brev

After evals pass, convert the model to GGUF for local use:

```bash
# On the Brev instance:
bash brev/quantize.sh
```

This produces `models/ministral-8b-Q4_K_M.gguf` (~5GB) using `llama.cpp`. The Q4_K_M format is the best quality-to-size tradeoff and runs well on a laptop CPU/GPU.

---

### Stage 3: Siphon — Transfer to Laptop

Pull the quantized model from Brev to your local machine:

```bash
# On your LOCAL laptop:
bash brev/siphon.sh
```

This SCPs the GGUF file into `./models/` locally. One-time operation.

---

### Stage 4: Run Locally — The Compute Tax

Start the local inference server. **This is where your fans scream.**

```bash
# On your LOCAL laptop:
bash local/serve.sh
```

This launches `llama-server` on `localhost:8000`. Point your sidecar at it by setting:
```bash
# sidecar/.env
LLM_ENDPOINT=http://localhost:8000/v1/chat/completions
```

Then start the sidecar as normal:
```bash
cd sidecar && uv run main.py
```