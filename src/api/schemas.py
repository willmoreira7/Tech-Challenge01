"""Pydantic models para validação de requests e responses."""


from typing import Literal

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Schema de request para predição individual."""

    gender: Literal["Male", "Female"] = Field(..., description="Gênero do cliente")
    SeniorCitizen: int = Field(..., ge=0, le=1, description="É senior citizen (0/1)")
    Partner: Literal["Yes", "No"] = Field(..., description="Tem parceiro (Yes/No)")
    Dependents: Literal["Yes", "No"] = Field(..., description="Tem dependentes (Yes/No)")
    tenure: int = Field(..., ge=0, description="Meses como cliente")
    PhoneService: Literal["Yes", "No"] = Field(..., description="Tem phone service (Yes/No)")
    MultipleLines: str = Field(..., description="Tem múltiplas linhas")
    InternetService: str = Field(..., description="Tipo de internet service")
    OnlineSecurity: str = Field(..., description="Online security (Yes/No/No internet service)")
    OnlineBackup: str = Field(..., description="Online backup (Yes/No/No internet service)")
    DeviceProtection: str = Field(
        ..., description="Device protection (Yes/No/No internet service)"
    )
    TechSupport: str = Field(..., description="Tech support (Yes/No/No internet service)")
    StreamingTV: str = Field(..., description="Streaming TV (Yes/No/No internet service)")
    StreamingMovies: str = Field(
        ..., description="Streaming movies (Yes/No/No internet service)"
    )
    Contract: str = Field(..., description="Tipo de contrato")
    PaperlessBilling: Literal["Yes", "No"] = Field(..., description="Paperless billing (Yes/No)")
    PaymentMethod: str = Field(..., description="Método de pagamento")
    MonthlyCharges: float = Field(..., ge=0, description="Cobrança mensal")
    TotalCharges: float = Field(..., ge=0, description="Cobrança total")

    class Config:
        json_schema_extra = {
            "example": {
                "gender": "Male",
                "SeniorCitizen": 0,
                "Partner": "Yes",
                "Dependents": "No",
                "tenure": 12,
                "PhoneService": "Yes",
                "MultipleLines": "No phone service",
                "InternetService": "Fiber optic",
                "OnlineSecurity": "No",
                "OnlineBackup": "No",
                "DeviceProtection": "No",
                "TechSupport": "No",
                "StreamingTV": "No",
                "StreamingMovies": "No",
                "Contract": "Month-to-month",
                "PaperlessBilling": "Yes",
                "PaymentMethod": "Electronic check",
                "MonthlyCharges": 70.35,
                "TotalCharges": 844.20,
            }
        }


class PredictResponse(BaseModel):
    """Schema de response para predição individual."""

    churn_probability: float = Field(..., ge=0, le=1, description="Probabilidade de churn")
    churn_predicted: bool = Field(..., description="Predição binária de churn")
    model_version: str = Field(..., description="Versão do modelo")
    processing_time_ms: float = Field(..., ge=0, description="Tempo de processamento em ms")


class PredictionRecord(BaseModel):
    """Schema de um record de predição em batch."""

    record_index: int = Field(..., ge=0, description="Índice do record original")
    churn_probability: float = Field(..., ge=0, le=1, description="Probabilidade de churn")
    churn_predicted: bool = Field(..., description="Predição binária de churn")


class PredictBatchRequest(BaseModel):
    """Schema de request para predição em batch."""

    records: list[PredictRequest] = Field(..., min_length=1, max_length=10000)

    class Config:
        json_schema_extra = {
            "example": {
                "records": [
                    {
                        "gender": "Male",
                        "SeniorCitizen": 0,
                        "Partner": "Yes",
                        "Dependents": "No",
                        "tenure": 12,
                        "PhoneService": "Yes",
                        "MultipleLines": "No phone service",
                        "InternetService": "Fiber optic",
                        "OnlineSecurity": "No",
                        "OnlineBackup": "No",
                        "DeviceProtection": "No",
                        "TechSupport": "No",
                        "StreamingTV": "No",
                        "StreamingMovies": "No",
                        "Contract": "Month-to-month",
                        "PaperlessBilling": "Yes",
                        "PaymentMethod": "Electronic check",
                        "MonthlyCharges": 70.35,
                        "TotalCharges": 844.20,
                    }
                ]
            }
        }


class PredictBatchResponse(BaseModel):
    """Schema de response para predição em batch."""

    batch_id: str = Field(..., description="ID único do batch")
    predictions: list[PredictionRecord] = Field(..., description="Lista de predições")
    model_version: str = Field(..., description="Versão do modelo")
    total_records: int = Field(..., ge=0, description="Total de records processados")
    processing_time_ms: float = Field(..., ge=0, description="Tempo total de processamento em ms")


class HealthResponse(BaseModel):
    """Schema de response para health check."""

    status: str = Field(..., description="Status do serviço")
    model_version: str = Field(..., description="Versão do modelo")
    uptime_seconds: float = Field(..., ge=0, description="Uptime em segundos")
    timestamp: str = Field(..., description="Timestamp ISO 8601")


class RootResponse(BaseModel):
    """Schema de response para rota raiz."""

    app: str = Field(..., description="Nome da aplicação")
    version: str = Field(..., description="Versão da API")
    description: str = Field(..., description="Descrição da API")
    documentation: str = Field(..., description="URL da documentação")
    endpoints: dict = Field(..., description="Endpoints disponíveis")


class ErrorResponse(BaseModel):
    """Schema de response de erro."""

    error: str = Field(..., description="Tipo de erro")
    detail: str = Field(..., description="Detalhe do erro")
    status_code: int = Field(..., description="Código HTTP")
