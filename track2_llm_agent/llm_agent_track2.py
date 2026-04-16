def denial_resolution_agent(denial_event):
    """
    Orchestrates the lifecycle of the LLM-driven autonomous denial resolution agent utilizing a 
    predictable state machine configuration. It sequentially manages denial classification, retrieval 
    of medical policies, appeal generation, and finally rule-based hallucination validation.
    """
    state = "CLASSIFICATION"
    context = {}
    
    while state != "DONE":
        if state == "CLASSIFICATION":
            context['carc_category'] = classify_denial_reason(denial_event)
            state = "RETRIEVAL"
            
        elif state == "RETRIEVAL":
            # Invoke tools to get necessary context (RAG Layer)
            context['ncci_validation'] = rule_engine_check_ncci(denial_event['cpt_codes'])
            context['lcd_ncd_policies'] = query_azure_ai_search(context['carc_category'], denial_event['payer'])
            context['clinical_docs'] = get_patient_clinical_docs(denial_event['patient_id'])
            state = "GENERATION"
            
        elif state == "GENERATION":
            # Generate appeal using retrieved context (from genrate_appeal.py)
            context['draft_appeal'] = generate_appeal(denial_event, denial_event['claim_data'], context)
            state = "VALIDATION"
            
        elif state == "VALIDATION":
            # Guardrails validation post-generation
            is_valid, errors = validate_hallucinations_against_master_db(
                context['draft_appeal'], 
                allowed_cpt_codes,
                context['clinical_docs']
            )
            
            if is_valid:
                state = "DONE"
            else:
                log_hallucination_for_monitoring(errors)
                state = "GENERATION" # Retry generation with deterministic error feedback
                
    return context['draft_appeal']
