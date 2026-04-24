# Travel Deal Investigator — Agentic AI Chrome Plugin

An Agentic AI Chrome Extension with a Python FastAPI backend powered by Google Gemini 2.0 Flash.
The agent investigates travel deals using a multi-step reasoning chain with 3 custom tools.

## Architecture

```
Chrome Extension (JS)  ──HTTP POST──►  Python FastAPI Server (localhost:5000)
  - Thin UI client                       - Gemini agentic loop (agent.py)
  - Displays reasoning chain             - 3 custom tools (tools.py)
  - Shows LLM logs                       - Full conversation history tracking
                                                    │
                                                    ▼
                                            Google Gemini 2.0 Flash API
```

## Assignment Requirements

- Call LLM multiple times in a loop: Agentic loop in agent.py
- Each query stores ALL past interactions: Gemini chat.history accumulates every turn
- Display agent reasoning chain: Color-coded step cards (Thought/Tool Call/Tool Result)
- At least 3 custom tool functions: analyze_deal, check_price_history, get_destination_info
- Show each tool call and result: Every call and result displayed with full data
- LLM Logs for submission: Toggle logs + Copy button

## The 3 Custom Tools (tools.py)

1. analyze_deal — Parses deal text, extracts price/origin/destination/dates/airline/type
2. check_price_history — Historical pricing: lowest/avg/highest + 6-month trend
3. get_destination_info — Visa, weather, safety, tips, daily budget

## Setup

### Step 1: Get Gemini API Key (Free)
Go to https://aistudio.google.com/apikey and create a key.

### Step 2: Start Python Backend
```bash
cd backend
pip install -r requirements.txt
python server.py
```

### Step 3: Install Chrome Extension
1. Go to chrome://extensions/
2. Enable Developer mode
3. Click Load unpacked
4. Select the extension/ folder

### Step 4: Use It
1. Click extension icon
2. Verify green backend indicator
3. Paste API key → Save
4. Enter a deal → Click Investigate
5. Watch reasoning chain → See verdict → Copy logs

## Example Deals to Try

- Round trip flights from NYC to Tokyo for $450 in December 2025 on Delta Airlines
- 5-night resort in Bali for $200 total, all-inclusive, January 2026
- One-way flight London to Dubai for $120 on Emirates, March 2026
- Flight + Hotel Mumbai to Paris $800/person, 7 nights, June 2026, Air France

## Project Structure

```
travel-deal-agent/
├── backend/
│   ├── server.py           # FastAPI server
│   ├── agent.py            # Gemini agentic loop
│   ├── tools.py            # 3 custom tool functions
│   └── requirements.txt    # Python dependencies
├── extension/
│   ├── manifest.json       # Chrome Manifest V3
│   ├── popup.html/css/js   # Extension UI
│   ├── content.js          # Page text extraction
│   └── icons/
└── README.md
```

## API Docs
Run server → visit http://localhost:5000/docs for Swagger UI.
