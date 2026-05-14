import os
import re

# Parse forms.py
with open("academia/forms.py", "r") as f:
    content = f.read()

forms = {}
current_form = None
for line in content.split("\n"):
    m = re.match(r"class (\w+Form)\(forms\.ModelForm\):", line)
    if m:
        current_form = m.group(1)
        forms[current_form] = []
    
    if current_form and "fields =" in line:
        pass # we'll extract fields manually
