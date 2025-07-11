#!/usr/bin/env python3

import base64
import time
import os
from together import Together

# Initialize client with API key
os.environ['TOGETHER_API_KEY'] = 'c0b5142ff581b2e2a6f64a778d4bd396b419a0bfffc0efbc3bdf635f03b1f3d0'
client = Together()

def query_vlm_about_frame(image_path, query):
    """Query VLM about spatial relationships in a frame"""
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            }],
            stream=False
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying VLM: {e}")
        return None

def query_reasoning_llm(query):
    """Query reasoning LLM for analysis"""
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[{
                "role": "user", 
                "content": query
            }],
            stream=False
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying reasoning LLM: {e}")
        return None

# Test reasoning LLM query
reasoning_query = """
I'm analyzing a video sequence and trying to answer this question:
"What event immediately follows the camera wearer placing a kettle on the kitchen counter?"

Options:
A. Starts the kettle to boil water.
B. Returns to the fridge to get milk.
C. Pours the tea into the cup.
D. Sits down to joint the man for the meal.
E. Carries the cup to where the man is eating.

I found these video sequences:
1. Frame 699 (2097s): "The hand is holding a white teapot and appears to be placing it on the countertop"
2. Frame 700 (2100s): "The hand is holding a bottle and appears to be placing it on the tray"

And also:
1. Frames 401-405: "wiping a metal kettle with a cloth" 
2. Frame 406: "pouring coffee from a metal pot into a cup on the kitchen counter"

Which sequence better matches the question about "placing a kettle on the kitchen counter" and what would be the most logical immediate next action?
"""

print("Querying reasoning LLM about the question...")
reasoning_result = query_reasoning_llm(reasoning_query)

def analyze_room_layout(frame_path, query_text):
    """Analyze a frame to understand room layout and spatial relationships"""
    print(f"Analyzing frame: {frame_path}")
    result = query_vlm_about_frame(frame_path, query_text)
    if result:
        print("VLM Response:")
        print(result)
        return result
    else:
        print("Failed to get VLM response")
        return None

if __name__ == "__main__":
    # Question 6: Spatial relationships in kitchen
    print("=== Question 6: Kitchen spatial relationships - fridge, sink, cutting board ===")
    
    # Analyze frames that show kitchen layout and spatial relationships
    kitchen_spatial_frames = [
        "/resource/frames/frame_0138.00s.jpg",  # Frame 46 - cutting board, knife on counter
        "/resource/frames/frame_0144.00s.jpg",  # Frame 48 - cutting board right of sink
        "/resource/frames/frame_0483.00s.jpg",  # Frame 161 - L-shaped counter, cutting board
        "/resource/frames/frame_0591.00s.jpg",  # Frame 197 - L-shaped counter with sink
        "/resource/frames/frame_1197.00s.jpg",  # Frame 399 - red cutting board
    ]
    
    for frame_path in kitchen_spatial_frames:
        query = f"""Please analyze this kitchen image for spatial relationships:
1. Where is the refrigerator/fridge located in this image?
2. Where is the sink located?
3. Where is the cutting board/chopping board located?
4. What is the spatial relationship between the fridge and sink?
5. What is the spatial relationship between the fridge and cutting board?
6. Which is closer to the fridge: the sink or the cutting board?
7. Describe the overall kitchen layout and how these items are positioned relative to each other.

Frame: {frame_path}"""
        analyze_room_layout(frame_path, query)
        print("\n" + "="*50 + "\n")
    
    # Question 1: Identify technology interactions
    print("=== Question 1: Technology interactions ===")
    
    # Analyze frames where technology might be used
    tech_frames = [
        "/resource/frames/frame_0300.00s.jpg",  # Kitchen with stove
        "/resource/frames/frame_1500.00s.jpg",  # Living room with TV
        "/resource/frames/frame_2400.00s.jpg",  # TV area
        "/resource/frames/frame_2700.00s.jpg",  # Study with computer
        "/resource/frames/frame_3597.00s.jpg",  # End - phone usage
        "/resource/frames/frame_3300.00s.jpg",  # Person with phone
    ]
    
    for frame_path in tech_frames:
        query = f"""Please analyze this image for technology usage:
1. What technological devices do you see in this image?
2. Is anyone actively using or interacting with technology?
3. Are there any electronic appliances, devices, or gadgets visible?
4. Can you identify: mobile phone, television, computer/monitor, cooker/stove, microwave, tablet, smart home devices?
5. What specific technology interactions are taking place?
6. Are there any signs of technology that was recently used or will be used?

Frame: {frame_path}"""
        analyze_room_layout(frame_path, query)
        print("\n" + "="*50 + "\n")
    
    # Original Question 0 analysis (keep for reference)
    print("=== Question 0: Navigation from living room to storage room ===")
    
    # First, let's identify living room frames
    living_room_frames = [
        "/resource/frames/frame_1500.00s.jpg",  # Living room/TV area
        "/resource/frames/frame_1800.00s.jpg",  # Living room activities
        "/resource/frames/frame_2400.00s.jpg",  # TV stand area
    ]
    
    for frame_path in living_room_frames:
        query = f"""Please analyze this image carefully and describe:
1. What room is this? (kitchen, living room, bedroom, bathroom, etc.)
2. What are the main features and furniture in this room?
3. What doors or openings do you see? Where do they lead?
4. Are there any storage areas visible?
5. What spatial relationships can you identify between objects and areas?
6. Can you describe the layout and how someone might move through this space?

Frame: {frame_path}"""
        analyze_room_layout(frame_path, query)
        print("\n" + "="*50 + "\n")
    
    # Look for storage room references
    storage_frames = [
        "/resource/frames/frame_0300.00s.jpg",  # Various room activities
        "/resource/frames/frame_0600.00s.jpg",  # Kitchen area
        "/resource/frames/frame_3000.00s.jpg",  # Later activities
    ]
    
    print("=== Looking for storage areas ===")
    for frame_path in storage_frames:
        query = f"""Please analyze this image and help identify:
1. What room or area is shown in this image?
2. Are there any storage areas, closets, or storage rooms visible?
3. What doors or passages do you see?
4. How might someone navigate from this area to other rooms?
5. Are there any containers, boxes, or storage items visible?

Frame: {frame_path}"""
        analyze_room_layout(frame_path, query)
        print("\n" + "="*50 + "\n")
    
    # Analyze hallway frames for navigation
    print("=== Analyzing hallway and transition frames ===")
    hallway_frames = [
        "/resource/frames/frame_0000.00s.jpg",  # Start - hallway
        "/resource/frames/frame_0003.00s.jpg",  # Hallway with reflections
        "/resource/frames/frame_0027.00s.jpg",  # Transition areas
        "/resource/frames/frame_2700.00s.jpg",  # Navigation between rooms
    ]
    
    for frame_path in hallway_frames:
        query = f"""Please analyze this image for spatial navigation:
1. What type of space is this? (hallway, doorway, room transition, etc.)
2. What doors, openings, or passages do you see?
3. Are there any storage closets, cabinets, or storage rooms visible?
4. How are the rooms connected? What is the layout?
5. Can you identify any directional indicators or spatial relationships?
6. Are there any signs of storage areas or utility rooms?

Frame: {frame_path}"""
        analyze_room_layout(frame_path, query)
        print("\n" + "="*50 + "\n")