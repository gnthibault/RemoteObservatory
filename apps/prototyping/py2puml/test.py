# Run with PYTHONPATH=. python ./apps/prototyping/py2puml/test.py
from py2puml.py2puml import py2puml

# outputs the PlantUML content in the terminal
print("".join(py2puml("./Camera", "Camera")))

# writes the PlantUML content in a file
with open('./apps/prototyping/py2puml/camera.puml', 'w') as puml_file:
    puml_file.writelines(py2puml('./Camera', 'Camera'))
