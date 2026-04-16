def resolve_classification_conflict(prediction, actual_denial, claim_data):
    """
    Processes discrepancies between the pre-submission model predictions and the actual received 
    remittance advice in order to appropriately route the necessary downstream actions. It also
    generates structured conflict metadata which operates as a critical feedback loop for retraining.
    """
    final_label = actual_denial
    conflict_flag = (prediction != actual_denial)
    
    if actual_denial == "CO-16":
        action = "request_missing_info_and_resubmit"
    elif actual_denial == "medical_necessity":
        action = "generate_appeal_with_clinical_justification"
    else:
        action = "standard_denial_workflow"
    
    # Attach context for learning
    metadata = {
        "predicted_label": prediction,
        "actual_label": actual_denial,
        "conflict": conflict_flag,
        "payer_id": claim_data["payer_id"],
        "cpt": claim_data["cpt"],
        "icd": claim_data["icd"]
    }
    
    return final_label, action, metadata
