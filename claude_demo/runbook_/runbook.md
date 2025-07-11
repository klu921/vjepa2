### Task:

START HERE: 

I have a current pipeline.

I want a new file that basically allows two models (a VLM, an LLM frame selector, and an LLM to interact)

It will work as follows:

LLM receives an input MCQ and no context. It is told it has to answer the question correctly, or else bad things happen. It can ask any questions it wants, and it will receive responses. 

Those questions go to an LLM frame selector, which selects the best frames from a given set of captions to answer the question. Those frame timestamps are then sent to a VLM, along with the original LLM's questions, and the VLM is told to extract the answers to those questions. 

The VLM then sends those answers back to th eorigina LLM. 

This is allowed to go in loop until the LLM is confident in a correct answer, and this should be automated.

This pipeline should allow the LLM to query the LLM frame selector and the VLM, and all vice versa.

Please also log every interaction in a text file.

Automate this pipeline for me. We're going to use the Together API. We're going to use deepseek-ai/DeepSeek-V3 as the LLM and the LLM frame selector, and Llama Mav for the VLM. 

You should read the files in the directory, because they show how API queries should be structured.

ANOTHER issue is that we're severely rate-limited. 




Ignore/history: Please read through the files in this directory. What we have right now is a pipeline that does the following.
Tools: Video_frame_extractor, image_captioner provide the necessary functions to extract frames from a video, and generate captions for the frames.
get_gen_caps takes a video in, outputs general captions for a frame every 3 seconds.

Currently, get_gen_caps is outputting general captions super slowly because of rate limits by query. Can you combine many images to be captioned in one query, so that this rate limit can be bypassed? Please look at the printed captions and make sure they're high quality. Some example high quality captions already exist in captions/video_captions.json. If they're wrong, play with the prompt until they come out right. 

Then, once the general captions have been made, I want the pipeline fixed so that another LLM that is good at reasoning can take in all the general captions, look at the question/answer-choices, and then iterate through each caption and decide if it's useful to answering the question. Play with prompts again here. Tell the LLM it can choose some number of key frames, but to try to keep it minimal, and then query another VLM with those x key frames to finally choose the correct answer, and give reasoning about it. 


Then, I want the pipeline fixed so that the question-answerer takes this new specified caption, and derives the answer using the function that laready exists in llm_mcq_answerer.