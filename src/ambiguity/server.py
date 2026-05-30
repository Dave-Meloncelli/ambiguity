"""FastAPI HTTP server wrapping the ambiguity analysis engine."""

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, RedirectResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ImportError:
    raise ImportError("fastapi and pydantic are required. Install with: pip install fastapi uvicorn[standard]")

from ambiguity.analyzer import Analysis
from ambiguity.review import review, render_review_json

app = FastAPI(
    title="ambiguity",
    description="Deterministic prompt analysis — pre-flight linter for human-to-model translation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    prompt: str


class ReviewRequest(BaseModel):
    prompt: str
    response: str


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        analysis = Analysis(request.prompt)
        return analysis.json_report()
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"analysis failed: {exc}"},
        )


@app.post("/review")
async def analyze_review(request: ReviewRequest):
    try:
        result = review(request.prompt, request.response)
        return render_review_json(result)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"review failed: {exc}"},
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
