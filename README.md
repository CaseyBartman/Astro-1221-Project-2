# Astro-1221-Project-2

# Installation and Run Instructions:
1. First, make sure the following dependencies are installed by running this command:
 
 $ pip install pandas numpy streamlit matplotlib

2. Then, run this command to run the program

 $ streamlit run main.py

# Project Goal:
To collect information about all the Messier objects, filter it, and, depending on the input of the aperture and other info of the user (observer), such as the season of the year, display information to present the messier objects and take them on a tour through the objects.
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
