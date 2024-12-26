#!/bin/bash
#python3 -m venv myenv
source myenv/bin/activate
# Activate the virtual environment
#source myenv/bin/activate

# Install librosa in the virtual environment
pip install --upgrade pip
pip install librosa
pip install schedule
pip install pydub
pip install matplotlib
python3 app.py
