### 4 terminals are required for the workflow:
1. a brev instance to train the model
brev shell optiministral
brev ls

2. an instance of electron
npm run start

3. a terminal to host the local llm
bash host/local_llm.sh

4. a terminal to manually make POSTs
curl -X POST http://127.0.0.1:8080/poke