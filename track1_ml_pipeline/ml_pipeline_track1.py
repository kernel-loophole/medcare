def extract_features(claim_data, historical_data):
    """
    Extracts informative features across three dimensions: claim-level details, payer-specific
    temporal trends, and historically aggregated interactions. These comprehensive
    features form the core dataset required to train the denial prediction model.
    """
   
    cpt_embeddings = encode_cpt_codes(claim_data['cpt_codes'], claim_data['modifiers'])
    icd_embeddings = hierarchical_icd_encode(claim_data['icd_codes'])
    payer_behavior = get_payer_temporal_patterns(claim_data['payer'], claim_data['date'])
    rolling_denial_rate = compute_rolling_rate(
        claim_data['provider_id'], 
        claim_data['payer'], 
        window_days=[7, 30, 90]
    )
    
    return concatenate([cpt_embeddings, icd_embeddings, payer_behavior, rolling_denial_rate])

def train_and_evaluate_model(features, labels):
    """
    Splits the dataset and trains the primary classification model utilizing cost-based optimization. 
    It evaluates model performance dynamically by calibrating the decision threshold to account 
    for the asymmetrical financial costs of false negatives versus false positives.
    """
    X_train, X_val, y_train, y_val = time_based_split(features, labels)
    baseline_model = LogisticRegression().fit(X_train_simple, y_train)
    model = XGBoostClassifier()
    model.fit(X_train, y_train)
    optimal_threshold = find_optimal_threshold(model.predict_proba(X_val), y_val, fn_cost=50, fp_cost=5)
    predictions = (model.predict_proba(X_val) > optimal_threshold).astype(int)
    
    metrics = {
        'recall': calculate_recall(y_val, predictions),
        'precision': calculate_precision(y_val, predictions),
        'f1': calculate_f1(y_val, predictions),
        'auc_roc': calculate_roc_auc(y_val, model.predict_proba(X_val))
    }
    return model, metrics
