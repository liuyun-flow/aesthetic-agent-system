"""Pydantic schemas for the settings API."""

from typing import Literal

from pydantic import BaseModel, Field


class DeepSeekStatus(BaseModel):
    is_configured: bool
    api_key_masked: str
    base_url: str
    default_model: str
    reasoning_model: str


class VisionStatus(BaseModel):
    provider: str
    is_configured: bool
    openai_api_key_masked: str
    openai_vision_model: str


class SettingsStatusResponse(BaseModel):
    deepseek: DeepSeekStatus
    vision: VisionStatus


class SettingsSaveRequest(BaseModel):
    deepseek_api_key: str = ""
    deepseek_base_url: str = ""
    deepseek_default_model: str = ""
    deepseek_reasoning_model: str = ""
    vision_provider: str = ""
    openai_api_key: str = ""
    openai_vision_model: str = ""


class ClearKeyRequest(BaseModel):
    key_type: Literal["deepseek", "openai"]


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    model_used: str = ""
