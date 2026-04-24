"""
Travel Deal Investigator — FastAPI Backend
Exposes the agentic loop as a REST API for the Chrome Extension.

Run with:  uvicorn server:app --reload --port 5000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_agent

app = FastAPI(
    title="Travel Deal Investigator Agent",
    description="Agentic AI backend powered by Gemini — investigates travel deals with 3 custom tools",
    version="1.0.0"
)

# Allow Chrome Extension to call this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Chrome extensions have chrome-extension:// origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvestigateRequest(BaseModel):
    deal_text: str
    api_key: str


class StepResponse(BaseModel):
    type: str       # "thought", "tool-call", "tool-result", "error"
    title: str
    content: str


class InvestigateResponse(BaseModel):
    steps: list[StepResponse]
    final_answer: str
    logs: str
    iterations: int



@app.get("/")
def root():
    return {
        "service": "Travel Deal Investigator Agent",
        "status": "running",
        "endpoints": {
            "POST /investigate": "Send a travel deal for analysis",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/investigate", response_model=InvestigateResponse)
def investigate(request: InvestigateRequest):
    """
    Main endpoint — runs the full agentic loop:
    Query → Gemini → Tool Call → Tool Result → Query → Gemini → ... → Final Verdict
    """
    if not request.deal_text.strip():
        raise HTTPException(status_code=400, detail="deal_text cannot be empty")
    if not request.api_key.strip():
        raise HTTPException(status_code=400, detail="api_key is required")

    try:
        result = run_agent(
            deal_text=request.deal_text.strip(),
            api_key=request.api_key.strip()
        )
        return InvestigateResponse(
            steps=result["steps"],
            final_answer=result["final_answer"],
            logs=result["logs"],
            iterations=result["iterations"]
        )
    except Exception as e:
        print(f"❌ Agent error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Travel Deal Investigator Agent on http://localhost:5000")
    print("📖 API docs at http://localhost:5000/docs")
    uvicorn.run(app, host="0.0.0.0", port=5000)
