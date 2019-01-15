import glob
from os import path, mkdir

import shutil
import subprocess
from collections import namedtuple, defaultdict


FilmProperties = namedtuple("FilmProperties",  ['name', 'encoding', 'chapter', 'file_number'])


def run_merge(ffmpeg_path, files, output_folder, key, merge_suffix="M"):
    """ Runs command ffmpeg -f concat -i input.txt -c copy output.mp4"""
    output = path.join(output_folder, f"{key}{merge_suffix}.mp4")
    command = [ffmpeg_path, "-f", "concat", "-safe", "0", "-i", files, "-c", "copy", output]
    print("Running merge for ")
    print(files)
    with open(files) as f:
        print(f.read())
    print("Output:", output)
    print("Will run commnad", " ".join(command))
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE)
    except Exception as e:
        print("Failed to execute command", " ".join(command))
        print(e)
        return
    print(result.stdout)


def parse_filename(file_path):
    name = path.basename(file_path)
    if not name:
        print(f"Failed to parse name {file_path}")
        return None

    # Ignore looping files:
    try:
        int(name[2:4])
    except ValueError:
        print(f"Found looping file {file_path}, will be ignored.")
        return None

    return FilmProperties(name=name, encoding=name[:2], chapter=name[2:4], file_number=name[4:8])



def group_files(folder):
    """ For given folder, creates input files where it separates all the stuff belonging together. """
    grouping = defaultdict(list)
    for file_path in glob.glob(path.join(folder, "*.mp4")):
        properties = parse_filename(file_path)
        if not properties:
            continue
        grouping[f"{properties.encoding}01{properties.file_number}"].append(properties)

    # Remove empty or just one, and sort the list by chapter just in case
    grouping = {k: sorted(v, key=lambda x: x.chapter) for k, v in grouping.items() if len(v) > 1}

    # If input folder exists just clean it out
    if path.exists("input"):
        shutil.rmtree("input")
    mkdir("input")

    for key, files in grouping.items():
        with open(path.join("input", f"{key}.txt"), "w") as f:
            for props in files:
                f.write(f"file {path.join(folder, props.name)}\n")
    return "input", grouping


def merge_all(ffmpeg_path, input_folder, output_folder):
    """ Given a folder it will get all txt files inside and run merge on it. """
    grouped_folder, grouped_films = group_files(input_folder)
    for key, files in grouped_films.items():
        files = path.join(grouped_folder, f"{key}.txt")
        run_merge(ffmpeg_path, files, output_folder, key)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run merge on folder.')
    parser.add_argument('ffmpeg_path', help='The path to ffmpeg executable.')
    parser.add_argument('input_folder', help='The folder to merge from.')
    parser.add_argument('output_folder', help='The folder to put results in.')

    args = parser.parse_args()
    merge_all(args.ffmpeg_path, args.input_folder, args.output_folder)

