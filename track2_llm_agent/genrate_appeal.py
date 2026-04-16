def generate_appeal(denial, claim_data, retrieval_context):
    """
    Executes the retrieval-augmented generation strategy to draft mathematically-sound appeals 
    grounded directly within clinical rules and payer guidelines. It actively truncates large 
    patient history tokens to respect strictly imposed context window constraints prior to calling the LLM.
    """
    
    # Step 1: Retrieve top-k relevant documents from Azure AI Search
    # This includes LCD/NCD medical necessity policies, payer-specific guidelines,
    # prior approved claims matching this CPT/ICD, and historically successful appeal letters.
    docs = retrieve_context(denial, claim_data)

    # Step 2: Rank and filter the retrieved context
    # Employs a hybrid ranking strategy: calculating semantic similarity via embeddings
    # combined with deterministic structured filters (matching specific payer, CPT, and ICD codes).
    ranked_docs = rank_by_similarity_and_rules(docs)

    # Step 3: Select context within token budget
    # The LLM's context window is 128K tokens. We limit our context injection to ~120K to leave 
    # safe room for both the system prompt instructions and the generated response completion.
    # Lower-priority documents are summarized to compress information without losing critical signals.
    selected_context = truncate_and_select(ranked_docs, max_tokens=120000)

    # Step 4: Construct the final payload prompt
    # Injects the prioritized clinical document sections (e.g., diagnosis justification) 
    # and matching Azure AI policy excerpts alongside the raw denial reason and original claim features.
    prompt = build_prompt(denial, claim_data, selected_context)

    # Step 5: Generate appeal via Azure OpenAI
    # The LLM is forced to output structured responses aligned to specific appeal requirements.
    # Note: Generated appeals should still route to Track 2's validation state for hallucination checks.
    appeal = call_llm(prompt)

    return appeal
