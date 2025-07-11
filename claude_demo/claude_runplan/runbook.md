Your task:

There are 43 questions in the question_set/spatial_reasoning_dataset.csv. They test understanding of an hour-long video, and each is solvable with enough exploration, organized reasoning, and visual understanding.

Your goal is to answer all 43 questions correctly. You can spend as much time and resources as you want. The main objective here is accuracy and confidence in your answers.

Please write and continually update three files:
1. Please keep a detailed log of all your thoughts + reasoning in an organized filed, called 'detailed_log.md'. Whenever you query the VLM, note the prompt you used, which frames you queried, and the result you received.
2. Please keep a small "scratchpad.txt" file of the key relevant information you've found for each problem so far, so you don't forget it. Read the scratchpad at the end before you produce your final answer, and reset your scratchpad for every new question.
3. Please keep a log of the final answers + reasoning, in a clearly readable format in a file called 'final_answers.md'.

At the beginning of the run, go through the video captions once, identify major events/landmark frames where new events begin/end, and get a grasp of phases of the video. Mark down accurate timestamps for these shifts. Write these down.

You can use the following tools:

1. There is a set of 1200 detailed general captions in captions/video_captions.json, taken once of a frame every 3 seconds. Each caption is associated with a timestamp.

2. You also have access to the 1200 frames. You can API to a VLM and an LLM with the script vlm_query.py (Parse the file, you can edit the prompts) to view and understand the frames. You may be rate-limited by this VLM. If you are, wait 20 seconds, and try again. Be persistent.

3. You can also query to a reasoning LLM by changing above model to the deepseek model: deepseek-ai/DeepSeek-V3

Some of the questions will require temporal information. Please use timestamp information from the frame file-names as well. 

After every few questions, read this file again.