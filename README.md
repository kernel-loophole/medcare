# ClaimPilot AI: ML Architecture & Azure Deployment

This repository contains the deliverables for the **Assessment**. It includes the architectural pseudocode mapped to the three automation tracks (Classical ML, LLM Agentic Flows, and Voice Agents), alongside the simulated production deployment configurations for Azure.

## 📂 Repository Structure

* **`track1_ml_pipeline/`**: Contains the feature engineering formulation (`ml_pipeline_track1.py`) and conflict resolution metadata logging logic (`resolve_classification_conflict.py`) utilized to build and track the classical denial prediction models.
* **`track2_llm_agent/`**: Contains the deterministic state-machine orchestration (`llm_agent_track2.py`) and mathematically constrained retrieval-augmented generation processes (`genrate_appeal.py`) for producing automated appeals.
* **`track3_voice_agent/`**: Maps out the concurrent SST/TTS streaming state flow (`voice_agent_track3.py`) and dynamic IVR navigation intent parsing (`navigate_ivr.py`).
* **`azure_deployment/`**: Provides the structural endpoints and service-bus queue consumer bindings (`azure_deployment_api.py`), as well as idempotent batch reprocessing mechanisms (`reclaim.py`).
* **`common/`**: Contains the core dataclass schema definitions (`data_models.py`) used across all entities.

---

## ☁️ Task 2: Azure Deployment Documentation

### Architecture & Data Flow
The deployment leverages an event-driven, hub-and-spoke model on Azure. 
1. **Client Submission**: A billing system sends a `POST /claims` request to the HTTP-triggered Azure Function.
2. **Buffering**: The HTTP Function validates the payload, logs it to Azure SQL Serverless as `pending`, and publishes the metadata safely to **Azure Service Bus**.
3. **Queue Processing**: A separate Service Bus-triggered Azure Function (Worker) picks up the workload from the queue asynchronously and executes the denial prediction simulation.
4. **Resiliency**: If a worker fails, the message returns to the queue. After 3 continuous failures, it is moved to the **Dead Letter Queue (DLQ)**.

### Setup Instructions (Azure deployment)

Deploy from scratch easily using the Azure CLI:

```bash
# 1. Create a Resource Group
az group create --name claimpilot-rg --location eastus

# 2. Deploy Azure Service Bus (Basic Tier)
az servicebus namespace create --resource-group claimpilot-rg --name claimpilot-bus --location eastus --sku Basic
az servicebus queue create --resource-group claimpilot-rg --namespace-name claimpilot-bus --name claim-processing-queue

# 3. Create Serverless SQL Database
az sql server create --name claimpilot-sql --resource-group claimpilot-rg --admin-user sqladmin --admin-password <StrongPassword>
az sql db create --resource-group claimpilot-rg --server claimpilot-sql --name claimpilot-db --edition GeneralPurpose --compute-model Serverless --family Gen5 --capacity 1

# 4. Create and publish the Azure Function App
az functionapp create --resource-group claimpilot-rg --consumption-plan-location eastus --runtime python --runtime-version 3.11 --functions-version 4 --name claimpilot-func-app --storage-account <StorageAccountName>
func azure functionapp publish claimpilot-func-app
```

### Service Bus Configuration
* **Max Delivery Count:** Set to `3`. If the Python worker throws an exception (e.g. simulating the `FORCE_FAIL` error), the Queue automatically triggers a retry.
* **Dead Letter Queue (DLQ):** Enabled by default in Service Bus. If the delivery count exceeds 3, the payload safely routes to the DLQ to avoid blocking new incoming tasks.
* **Lock Duration:** `30 seconds`, guaranteeing the worker has enough time to run the ML simulation logic without the system mistakenly assigning the task redundantly.
* **Message TTL:** `24 Hours`.

### System Security (RBAC / Managed Identity)
**No external connection strings or API keys are hardcoded**. Security has been strictly managed:
1. **System-Assigned Managed Identity**: Granted directly to the Azure Function.
2. **Azure Role-Based Access Control (RBAC)**:
   * The Function has `Azure Service Bus Data Receiver/Sender` permissions specifically for its namespace so it can enqueue and dequeue effectively.
   * Granted `Key Vault Secrets User` permission to dynamically retrieve database strings without committing any plaintext secrets to this repository.

### Output Verification & Sample Logs

*(Note for Submission: Place your screenshots here)*
* [Insert Screenshot] Application Insights showing `clean` HTTP 202 request correlated to HTTP 200 completion processing.
* [Insert Screenshot] Service Bus Retry loop showing 3 error traces routing to DLQ successfully.

---

### Implementation Write-up

**1. Service Choices:** I utilized Azure Functions integrated alongside Service Bus to completely decouple API ingestion from processing. Because ML prediction spikes heavily in daily batches, serverless component scaling ensures instantaneous processing capacity, while scaling efficiently to zero to respect strict Azure Free Tier limits. Azure SQL Serverless was selected due to its auto-pause traits while satisfying complex relational schemas tying claims directly to denials and logs.

**2. Service Bus Failure Handling:** If a runtime failure occurs internally within the ML worker pipeline, the Function actively throws an exception forcing the execution to halt. Because the Function did not gracefully return, the lock provided by the Service Bus on the specific message is released, making it available again for a configurable retry attempt (set to limits of 3). After continuous processing failure, instead of silently dropping crucial healthcare claims, the payload is pushed securely to the DLQ where a manual human reviewer or a designated pipeline can interact with it without clogging normal throughput.

**3. Architecting for 10,000 Claims/Day:** At 10,000 claims per day, our primary bottleneck becomes feature ingestion limits and simultaneous SQL connections. I would transition from Azure SQL Serverless to heavily provisioned **Cosmos DB** leveraging low-latency, scalable NoSQL ingestion. Furthermore, I would establish Event Hubs operating upstream from the Service Bus queue to act as a resilient batching telemetry buffer. 
