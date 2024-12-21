# Getting Started

__important notes__

- you MUST have a Nvidia GPU to run this. Please check the compatibility here: https://www.jetson-ai-lab.com/vit/tutorial_nanoowl.html
- this demo is to run on the Nvidia Jetson Orin .
- you can reference the docs, where this code is copied from: https://github.com/NVIDIA-AI-IOT/nanoowl

__docker set up__

```bash
git clone https://github.com/dusty-nv/jetson-containers
bash jetson-containers/install.sh
jetson-containers run --workdir /app --name inference -v `pwd`:/app $(autotag nanoowl) bash
```

# Run

- make sure you have a camera connected, and a browser installed on jetson

```bash
python3 demo.py
- open a web terminal (PRE-REQUISITE: `sudo apt-get update -yqq && sudo apt-get install -y chromium-browser`)
chromium http://0.0.0.0:7860
```

