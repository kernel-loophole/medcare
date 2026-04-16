from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime

@dataclass
class ClaimRecord:
    """
    Data model capturing the foundational properties and processing state of each individual 
    insurance claim submitted successfully through the API gateway. This serves as the primary entity mapped
    to the underlying operational SQL tables.
    """
    job_id: str
    claim_id: str
    status: str # pending, processing, completed, failed
    cpt_codes: List[str]
    icd_codes: List[str]
    modifiers: List[str]
    payer: str
    billed_amount: float
    patient_id: str
    provider_npi: str
    date_of_service: str
    prediction_result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    completed_at: Optional[datetime] = None

@dataclass
class AgentTraceRecord:
    """
    Data model designed to persistently log intermediate reasoning pathways and tool invocations generated 
    during an LLM's active execution cycle. This ensures strict debugging continuity and satisfies 
    internal compliance requirements inside the agentic reasoning loop.
    """
    trace_id: str
    claim_id: str
    steps_taken: List[Dict] # Tool calls, RAG contexts, reasoning paths
    final_output: Dict
    tokens_used: int
    execution_time_ms: int
    timestamp: datetime = datetime.utcnow()

@dataclass
class CallLogRecord:
    """
    Data model encompassing the complete historical context and metadata associated with outbound 
    AR follow-up phone calls. Encapsulates full text transcriptions dynamically paired with extracted 
    structured resolutions representing actionable account events.
    """
    call_id: str
    claim_id: str
    payer: str
    duration_seconds: int
    full_transcript: str
    structured_outcome: Dict # Resolution status, required next actions
    timestamp: datetime = datetime.utcnow()
