### Task:

Please read through the files in this directory. What we have right now is a pipeline that does the following.
Tools: Video_frame_extractor, image_captioner provide the necessary functions to extract frames from a video, and generate captions for the frames.
get_gen_caps takes a video in, outputs general captions for a frame every 3 seconds.

I want to add the two functions in llm_mcq_answerer. One takes in a question and answer choices, finds the top k most related key frames from the given captions, and then asks the LLM to regenerate captions for those k key frames with a more specified prompt using the function from image_captioner, and a list of the key frames.

Then, I want the pipeline fixed so that the question-answerer takes this new specified caption, and derives the answer using the function that laready exists in llm_mcq_answerer.

Be systematic, organized, ask me if you have any questions, and go forth!