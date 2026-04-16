def reprocess_claim(claim_id):
    """
    Provides an idempotent batch reprocessing pipeline to securely re-evaluate predictions for legacy 
    claims potentially impacted by system outages or flawed features. Ensures downstream duplicate events
    are not accidentally re-triggered unless the regenerated predictions demonstrably differ from origin.
    """
    record = get_claim_record(claim_id)

    if record["reprocessed_flag"]:
        return "already_processed"

    features = recompute_features(record["raw_data"])

    new_pred = model.predict(features)

    old_pred = record["prediction"]

    if new_pred != old_pred:
        publish_event("prediction_updated", claim_id, new_pred)

    update_record(claim_id, {
        "new_prediction": new_pred,
        "reprocessed_flag": True
    })
