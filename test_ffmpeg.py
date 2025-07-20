import subprocess
import shlex
import logging
import os

 # Logger setup for console output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_ffmpeg_conversion(input_file):
    """
    Tests conversion of a single file using ffmpeg.
    """
    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        return

    output_file = f"{os.path.splitext(input_file)[0]}.wav"
    logging.info(f"Starting conversion '{input_file}' to '{output_file}'")

    # Uses the same method as in the application
    command = (
        f"ffmpeg -nostdin -i {shlex.quote(input_file)} "
        f"-ac 1 -ar 16000 "
        f"{shlex.quote(output_file)} -y"
    )
    logging.info(f"Running command: {command}")

    try:
        process = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True, # Output is captured for analysis
            text=True
        )
        logging.info("Command executed successfully!")
        if process.stdout:
            logging.info(f"STDOUT:\n{process.stdout}")
        if process.stderr:
            # ffmpeg often writes progress to stderr, so this is not always an error
            logging.warning(f"STDERR:\n{process.stderr}")
        
        if os.path.exists(output_file):
            logging.info(f"Success! Output file '{output_file}' created.")
        else:
            logging.error("Error! File was not created, although the command did not return an error.")

    except subprocess.CalledProcessError as e:
        logging.error(f"Command finished with error! Return code: {e.returncode}")
        logging.error(f"STDOUT:\n{e.stdout}")
        logging.error(f"STDERR:\n{e.stderr}")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")

if __name__ == "__main__":
    # Test file
    test_file = "1180170c-35cb-47e4-9189-17686986eb7a---Upwork Meeting Jul 11 2025 Recording.mp4"
    test_ffmpeg_conversion(test_file)
