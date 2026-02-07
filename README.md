# 🍬 Sugar Protocol: Decentralized Discourse Genealogy on Sui

![Sui](https://img.shields.io/badge/Sui-Network-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

**Sugar Protocol** is a decentralized "Discourse Genealogy" system built on the **Sui Network**.

Unlike traditional knowledge graphs, Sugar Protocol focuses on capturing the **Stance** and **Conflict** within news and public discourse. It utilizes AI Agents to deconstruct unstructured news into a four-layer topology (`Entity` -> `Stance` -> `Claim` -> `Evidence`) and immutably records these logical relationships on the blockchain. The result is a 3D "Galaxy of Truth" where conflicting narratives (red lines) and supporting arguments (green lines) are visually interwoven.

![Project Screenshot](./assets/screenshot.jpg)
*(Replace with your red/green galaxy screenshot)*

## 🌟 Key Features

* **🧬 L1-L4 Discourse Genealogy Analysis:** A unique topological structure that breaks down information into:
    * **L1 Entity:** The core subject (e.g., Bitcoin, Elon Musk).
    * **L2 Stance:** The attitude towards the entity (e.g., Bullish, Skeptical).
    * **L3 Claim:** Specific logical arguments.
    * **L4 Evidence:** Source URLs and citations.
* **⚔️ Visual Conflict Detection:**
    * 🟢 **Green Links:** Represent support, derivation, or evidence (`bond_type: 1`).
    * 🔴 **Red Links:** Represent rebuttal, conflict, or contradiction (`bond_type: 3`).
* **🔗 On-Chain Immutability:** Uses Sui Move's `vector<ID>` structure to store parent-child relationships, ensuring the historical trajectory of discourse cannot be tampered with.
* **🧠 Intelligent Memory De-duplication:** A local memory module automatically identifies existing L1 Entities, ensuring that arguments from different news sources are organically grafted onto the same core node, preventing data silos.

## 📂 Project Structure

```text
sugar_protocol/
├── sources/                  # Backend Agents & Contracts
│   ├── agent.py              # The Scout: Auto-crawls news and standardizes data
│   ├── inspector.py          # The Analyst: Core logic for L1-L4 recursive minting
│   ├── chain_pusher.py       # The Bridge: Handles Python-to-Move type conversion
│   ├── batch_runner.py       # The Commander: Batch execution with auto-memory cleaning
│   ├── local_memory.json     # Memory Bank: Entity de-duplication index
│   └── ...
│
├── frontend/                 # 3D Visualization
│   ├── src/App.jsx           # React component for Red/Green galaxy rendering
│   └── ...
│
├── core.move                 # Sui Move Smart Contract
└── ...

🚀 Quick Start
1. Prerequisites
Python 3.10+

Node.js 18+

Sui CLI (Testnet configured)

OpenAI API Key

2. Backend Setup
Bash
cd sources
python3 -m venv venv
source venv/bin/activate
pip install pysui openai requests beautifulsoup4 python-dotenv
Create a .env file and add your API Key:

程式碼片段
OPENAI_API_KEY=sk-your-api-key-here
3. Deploy Smart Contract
Deploy the Move contract to the Sui Testnet. Once deployed, update the Package ID in chain_pusher.py (Line 13) and frontend/src/App.jsx (Line 6).

Bash
sui client publish --gas-budget 100000000
4. Run Analysis
Use the batch runner to generate the initial galaxy (includes automatic memory cleaning):

Bash
python3 batch_runner.py
This script will process the default list of news URLs, perform L1-L4 analysis, and mint the data on-chain.

5. Launch Frontend
Install the required 3D visualization packages and start the dev server:

Bash
cd frontend
npm install react-force-graph three @mysten/sui.js
npm run dev