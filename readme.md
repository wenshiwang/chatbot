# Install

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python install-helper.py

# Run

source venv/bin/activate
python fetch-dataset.py
python chatbot.py

# Note
 - Edit dataset/eva.txt to add more evaluation questions
 - See evaluation in dataset/eva-result.txt


