from pydantic import BaseModel

from app.models.dispatch import DispatchRecommendation


class DispatchResponse(BaseModel):
    recommendation: DispatchRecommendation


class ActiveDispatchResponse(BaseModel):
    recommendations: list[DispatchRecommendation]
