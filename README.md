# 🍬 Sugar Protocol: Decentralized Knowledge Graph on Sui

![Sui](https://img.shields.io/badge/Sui-Network-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

**Sugar Protocol** is a decentralized news knowledge graph running on the **Sui Network**.

It utilizes AI Agents to autonomously crawl web news, deconstruct unstructured text into "Core Issues" and "Derived Arguments," and permanently inscribe these logical relationships onto the blockchain using Move smart contracts. The result is an interactive, 3D "Galaxy of Truth" visualized in real-time.

![Project Screenshot](./assets/screenshot.jpg)
![alt text](<frontend/screenTest/截圖 2026-02-06 下午2.00.00.png>)

## 🌟 Key Features

* **Automated Intelligence Gathering (AI Agent):** Uses Python crawlers and OpenAI GPT-4o to read news and extract atomic claims.
* **Logic Topology Analysis:** Deconstructs articles into **Root Nodes** (Main Events) and **Derived Nodes** (Details/Arguments), identifying logical bonds (Support/Contradict).
* **On-Chain Graph Storage:** Leverages Sui Move's `vector<ID>` structure to store parent-child relationships directly on-chain, ensuring data immutability.
* **Smart Memory & De-duplication:** Features a local memory module with fuzzy matching to identify existing topics, allowing multiple news sources to merge into a single, organic "Truth Galaxy" without redundant roots.
* **3D Visualization:** An interactive frontend built with React and Three.js (Force Graph) that hydrates on-chain data in real-time to reconstruct the knowledge graph.

## 📂 Project Structure

```text
sugar_protocol/
├── sources/                  # Backend Python Agents & Smart Contracts
│   ├── agent.py              # The Scout: Crawls latest news (e.g., TechCrunch)
│   ├── inspector.py          # The Analyst: Deep analysis of specific URLs with topic merging
│   ├── chain_pusher.py       # The Bridge: Handles complex pysui type conversions & transactions
│   ├── batch_runner.py       # The Commander: Batches multiple URLs for processing
│   ├── doctor_raw.py         # The Medic: Diagnoses on-chain data health via RPC
│   ├── local_memory.json     # Memory Bank: Stores known Root IDs for de-duplication
│   ├── core.move             # Sui Move Smart Contract Core Logic
│   ├── sugar_protocol.move   # Entry functions
│   └── .env                  # Environment Variables (OpenAI Key)
│
├── frontend/                 # Visualization Interface
│   ├── src/App.jsx           # 3D Graph Logic & Data Hydration/Chunking
│   └── ...
│
├── Move.toml                 # Sui Package Configuration
└── ...