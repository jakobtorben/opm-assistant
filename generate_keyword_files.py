import os
import subprocess

# git clone git@github.com:OPM/opm-reference-manual.git

source_directory = "./opm-reference-manual/parts/chapters/subsections"
html_target_directory = "./opm-reference-manual/html_parts/chapters/subsections"
txt_target_directory = "./opm-reference-manual/txt_parts/chapters/subsections"

def convert_to_html(source_path, target_path):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to", "html",
        source_path,
        "--outdir", os.path.dirname(target_path)
    ])
    
def convert_to_txt(source_path, target_path):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to", "txt",
        source_path,
        "--outdir", os.path.dirname(target_path)
    ])

for root, dirs, files in os.walk(source_directory):
    for filename in files:
        if filename.endswith(".fodt"):
            source_path = os.path.join(root, filename)
            relative_path = os.path.relpath(source_path, source_directory)
            html_target_path = os.path.join(html_target_directory, relative_path)
            txt_target_path = os.path.join(txt_target_directory, relative_path)
            convert_to_html(source_path, html_target_path)
            convert_to_txt(source_path, txt_target_path)