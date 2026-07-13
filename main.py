from itertools import count

from fastapi import FastAPI

from models import CampaignStatus, DraftResponse, GenerateRequest, HealthResponse

app = FastAPI()

_campaign_ids = count(1)


@app.get("/")
def hello():
    return {"status": "FDE plan: started"}


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@app.post("/generate", response_model=DraftResponse)
def generate(request: GenerateRequest):
    return DraftResponse(
        campaign_id=next(_campaign_ids),
        content=f"[placeholder draft for {request.alert_type_code} via {request.channel.value}]",
        status=CampaignStatus.PENDING_APPROVAL,
        validation_notes=[],
    )


@app.post("/campaigns/{campaign_id}/approve", response_model=DraftResponse)
def approve(campaign_id: int):
    return DraftResponse(
        campaign_id=campaign_id,
        content="[placeholder draft]",
        status=CampaignStatus.APPROVED,
        validation_notes=[],
    )
