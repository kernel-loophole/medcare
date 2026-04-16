def navigate_ivr(call_session, payer_config, target_department):
    """
    Navigates dynamic, potentially unknown insurance Interactive Voice Response (IVR) phone menus 
    using intents detected directly from raw transcoded payer audio. Intelligently determines 
    whether to respond natively with required DTMF touch-tones or spoken phrasing to successfully connect.
    """
    state = "INIT"

    while state != "CONNECTED":
        if state == "INIT":
            play_greeting()
            state = "LISTEN_MENU"

        elif state == "LISTEN_MENU":
            menu_text = transcribe_audio(call_session)

            intent = classify_intent(menu_text)

            if intent == target_department:
                state = "SELECT_OPTION"
            else:
                state = "FALLBACK"

        elif state == "SELECT_OPTION":
            if payer_config["mode"] == "DTMF":
                send_dtmf(payer_config["option"])
            else:
                speak_response(target_department)

            state = "WAIT_RESPONSE"

        elif state == "WAIT_RESPONSE":
            response = listen_for_response()

            if is_human_agent(response):
                state = "CONNECTED"
            else:
                state = "LISTEN_MENU"

        elif state == "FALLBACK":
            retry_or_escalate()

    return "connected_to_agent"
