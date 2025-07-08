### Task:

Please read through the files in this directory. What we have right now is a pipeline that does the following.
Tools: Video_frame_extractor, image_captioner provide the necessary functions to extract frames from a video, and generate captions for the frames.
get_gen_caps takes a video in, outputs general captions for a frame every 3 seconds.

Currently, get_gen_caps is outputting general captions super slowly because of rate limits by query. Can you combine many images to be captioned in one query, so that this rate limit can be bypassed? Please look at the printed captions and make sure they're high quality. Some example high quality captions already exist in captions/video_captions.json. If they're wrong, play with the prompt until they come out right. 

Then, once the general captions have been made, I want the pipeline fixed so that another LLM that is good at reasoning can take in all the general captions, look at the question/answer-choices, and then iterate through each caption and decide if it's useful to answering the question. Play with prompts again here. Tell the LLM it can choose some number of key frames, but to try to keep it minimal, and then query another VLM with those x key frames to finally choose the correct answer, and give reasoning about it. 


Then, I want the pipeline fixed so that the question-answerer takes this new specified caption, and derives the answer using the function that laready exists in llm_mcq_answerer.

START HERE: 

Please run the pipeline and test. After every set of captions comes out, read that set of captions. If it doesn't look right - not detailed,  not long, not specific, or if there's an obvious error, please figure out what's wrong with the prompt and fix it. 

Expect the pipeline to take a very long time. But it will stream captions to the video_captions.json every few seconds, and you should read them as soon as they come out and make sure the quality is good. 

Be systematic, organized, ask me if you have any questions, and go forth!