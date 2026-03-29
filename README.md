# Astro-1221-Project-2

# Installation and Run Instructions:
1. First, make sure the following dependencies are installed by running this command:
 
 **$ pip install pandas numpy streamlit matplotlib litellm**

If that doesn't work, install each dependency on it's own command, and if you don't have the anaconda distribution we used in class, you'll have to **$ pip install requests** as well

2. Then, run this command to run the program

 $ streamlit run main.py

# Project Goal:
To collect information about all the Messier objects, filter it, and, depending on the input of the aperture and other info of the user (observer), such as the season of the year, display information to present the messier objects and take them on a tour through the objects. There are custom tours you can see of the objects that are generated based on the info you provide (such as your limiting magniture, calculated via info such as your telescope arperture, etc.).  
See requirements.txt for more information on class architecture and other file structure information.

# Data Sources:
-Please see the constants.py file to see the sources and where they are referenced. 
-The main sources we used were the following:
 - [fourmilab-hplanet/master/Messier.csv](https://github.com/7468696e6b/fourmilab-hplanet/blob/master/Messier.csv). -> This was our CSV source for the Messier Catalogue, compiled by Darrell W. Green, Compuserve
 - http://www.icq.eps.harvard.edu/MagScale.html  -> Source for visibility thresholds based on viewing magnitude
 - https://in-the-sky.org/data/ra_season.php?town=4509177 -> Source for RA ranges per season

## AI Usage in Project:
- Casey: 
 - I try to avoid overdependence on AI wherever possible. I only use LLMs and agentic coding to help with "busywork" boilerplate tasks. AI generated code is typically **significantly** more verbose than it needs to be, and that goes against my principles of having clean code. For example, I created the architecture and planned out the classes alongside how they would interact all on my own. Instead of typing out all the boilerplate setup skeleton code myself, I just prompted an LLM to do it. The actual development of the code was largely my own doing, especially with how the code was styled. I did use the class astronomer helper chatbot to help make sure my interpretation of the astronomical concepts was correct. Also, since I made sure the code was written clearly enough with descriptive variable names and aptly named functions, I had the LLM assist in writing out the tedious docstring documentation instead of doing it all myself. 

- Andrew:
- I used Ai to help me get the bare bones structure of the code that I was responsible for, however the specifics, such as the prompts for the LLM as well as the exact information given to the LLM for more clear responses. Specifically I used AI to help me with the exact syntax to get the llm to function as well as a few times where I was getting errors that I was struggling to fix. I made sure to check everything I recieved from AI as well as tried not to rely on it too heavily.

- Lauren:
 - I started off the project figuring out what I wanted the end goal to look like. Since my main portion was the streamlit code, it's pretty much all 'okay, what tools do I want there to be and how do I want it to be organized.' Before any code, I thought of a few bells and whistles that I wanted to see come through in our final streamlit app. Once I got a basic idea, I spent most of my time looking at my past project's work, the class notes and exercises, and googling functions for ideas I wanted implemented. I worked in cursor, so the agent was very useful when I wanted to use certain commands but couldn't figure out the exact syntax or preliminary steps needed. I knew a fuzzy idea of what I wanted before coding, I started throwing rough outlines down but I did have cursor's agent assist me in creating some code that would actually run using the functions I initially wanted. For documentation, I take quite a bit of joy in describing the code and what it does because it feels like journaling a bit. Any code that the agent produced that I didn't quite understand, I made sure to have it explain the block so that I could determine if it was actually useful. But in short, I had fun!  