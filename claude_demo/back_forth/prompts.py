def get_initial_prompt(question, choices):

    initial_prompt =f"""You are an expert question answerer working with a video analysis system. You need to answer this multiple choice question, but ONLY when you have sufficient information.

    QUESTION: {question}

    ANSWER CHOICES:
    {chr(10).join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)])}

    You have access to two AI assistants:
    1. FRAME_SELECTOR: Finds relevant video frames based on your questions
    2. VLM: Analyzes specific frames and answers detailed questions about them

    IMPORTANT INSTRUCTIONS:
    - You should ask multiple questions to gather sufficient information
    - you should ALWAYS ASK THE FRAME SELECTOR TO FIND FRAMES THAT COULD HELP ANSWER THE QUESTION. Don't reason through it all on your own.
    - this is NOT A SIMULATION. ASK THE Frame Selector and VLM directly, and don't make assumptions or create placeholders. Be thorough.
    - Make sure you are able to ANSWER EVERY QUESTION, with RELIABLE ANSWERS, EXPLICIT FRAMES, and RELEVANT DETAILS.
    - Sometimes the Frame Selector doesn't look through all the frames. Always ask it to look through all the frames, and find all the possible relevant frames.
    - Be curious and thorough - ask follow-up questions if the answers aren't detailed enough
    - You can ask the VLM different questions about the same frames to get more details
    - You can ask the Frame Selector to find different types of frames for different aspects
    - Only provide a FINAL_ANSWER when you are truly confident you have enough information
    - Don't ask the VLM to process more than 5 frames at a time.
    - Don't be afraid to probe, and ask many times. 


    Choose ONE ACTION: EITHER FRAME_SELECTOR, VLM, or FINAL_ANSWER, and format your requests as EXACTLY ONE OF THE FOLLOWING:
    FRAME_SELECTOR: [Your specific question/request to find relevant frames]
    VLM: [Your specific question about the frames - be detailed about what you want to know]
    CONTINUE: [Explanation of what more information you need and your next question]
    FINAL_ANSWER: [Only when confident - your chosen answer letter and detailed reasoning]

    Start by asking the Frame Selector to find frames that could help answer the question.
    """
    return initial_prompt

def get_frame_selector_prompt(query, original_question, choices, captions_text):
    prompt = f"""You are an expert video analyst. Based on the following query and context, select the most relevant frames.

    QUERY FROM COORDINATOR: {query}

    ORIGINAL QUESTION: {original_question}

    ANSWER CHOICES:
    {chr(10).join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)])}

    VIDEO FRAMES:
    {captions_text}

    Analyze each frame and select the most relevant ones for answering the query. Focus on frames that contain:
    1. Objects, actions, or spatial relationships mentioned in the query
    2. Visual evidence that could help answer the original question
    3. Key visual elements that distinguish between answer choices

    Select all the most relevant frames.
    SELECTED_FRAMES: [comma-separated frame numbers, e.g., 1, 3, 7, 12]

    Provide brief reasoning for your selection. If you are unsure that you've looked through and found all the relevant frames, say so. 
    """
    return prompt

def get_vlm_prompt(query):
    prompt = f"""You are a visual analysis expert. Carefully examine these video frames to answer: {query}

IMPORTANT: Provide extremely detailed observations about each frame. Include:
1. Specific objects and their exact locations/positions
2. People's actions, gestures, body language, and what they're interacting with
3. Spatial relationships between objects (above, below, left, right, in front of, behind)
4. Environmental details (lighting, setting, context)
5. Any text, signs, or labels visible
6. Colors, materials, textures, and conditions of objects
7. Temporal aspects - what appears to be happening or about to happen

For each frame, structure your response as:
Frame [timestamp]: [Detailed description addressing the query]

Be as specific as possible. If you cannot clearly see something or are uncertain, explicitly state that. Your detailed observations will help determine the correct answer to a multiple choice question."""
    return prompt