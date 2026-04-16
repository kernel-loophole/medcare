def voice_agent_call_flow(claim_id, payer_phone):
    """
    Represents the complete outbound conversational flow managing VoIP negotiations with 
    insurance payer representatives. Facilitates real-time concurrent speech generation pipelines
    in order to maintain low latency budgets and captures negotiated claim status logs upon wrap-up.
    """
    state = "DIALING"
    session = initialize_call_session(claim_id)
    
    while state != "TERMINATED":
        if state == "DIALING":
            connection = azure_communication_services_dial(payer_phone)
            if connection.is_successful():
                state = "IVR_NAVIGATION"
            else:
                state = "TERMINATED"
                
        elif state == "IVR_NAVIGATION":
            # Call IVR step from navigate_ivr.py
            status = navigate_ivr(session, get_payer_config_for(payer_phone), "claims")
            if status == "connected_to_agent":
                state = "LIVE_AGENT"
            else:
                log_call_failure(status)
                state = "TERMINATED"
                
        elif state == "LIVE_AGENT":
            # Concurrent SST and TTS to achieve < 800ms latency
            agent_audio = stream_speech_to_text(session)
            
            if detect_hold_music(agent_audio):
                state = "HOLD_WAIT"
                continue
                
            # Intercept human response and incrementally formulate response
            llm_response = generate_incremental_response_llm(agent_audio, session['context'])
            stream_text_to_speech(llm_response)
            
            if conversation_resolved(session['context']):
                state = "WRAP_UP"
                
        elif state == "HOLD_WAIT":
            # Periodically verify if agent resumed speaking
            if detect_human_speech(session):
                state = "LIVE_AGENT"
                
        elif state == "WRAP_UP":
            structured_outcome = extract_structured_outcome(session['transcript'])
            log_call_outcome(structured_outcome)
            # Propagate feedback to Track 1 (ML Classification)
            publish_event("track3_outcome_resolved", structured_outcome)
            state = "TERMINATED"
