from pydantic import BaseModel, Field

class ArtworkModelSettings(BaseModel):
    environment: list[str] = Field(default_factory=lambda: ["city"])
    contactShadow: bool = Field(default=True)
    intensity: list[float] = Field(default_factory=lambda: [1.0])
    exposure: list[float] = Field(default_factory=lambda: [1.0]) 
    modelColor: str = Field(default="#ffffff")
    backgroundColor: str = Field(default="#050505")
    autoRotate: bool = Field(default=False)
    lightPosition: list[float] = Field(default_factory=lambda: [5.0, 5.0, 5.0])
    lockCameraReset: bool = Field(default=False)
    lockInteraction: bool = Field(default=False)