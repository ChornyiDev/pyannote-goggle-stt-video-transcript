# Practical Guide: Integrating FFMPEG into Python Scripts

This document summarizes the experience gained while debugging `ffmpeg` calls from a background process (RQ worker). It describes common issues and a reliable solution.

---

## 1. Problem: FFMPEG "Hangs" When Launched from a Script

The main issue was that `ffmpeg` worked successfully when run manually from the terminal, but would hang or silently fail when launched from a Python script, especially from a background worker.

**Symptoms:**
-   The Python process calling `ffmpeg` would not finish and would not show errors.
-   The output file was not created or was incomplete.
-   No significant CPU or memory usage, indicating that `ffmpeg` was not actively working.

**Root Cause:**
The problem lies in process interaction. By default, `ffmpeg` is an interactive program. When launched, it may check the standard input stream (`stdin`), waiting for possible commands (e.g., `q` to quit).

When `ffmpeg` is launched from a background process (such as an RQ worker), this process does not have a connected terminal, and its `stdin` is in an undefined state. This leads to hanging: `ffmpeg` waits for `stdin`, which will never be ready.

---

## 2. Incorrect Approaches and Their Drawbacks

Several methods were tried during diagnostics, but none gave the desired result:

1.  **Simple `subprocess.run` call:** Did not work due to the `stdin` issue and potential problems with passing filenames containing spaces.
2.  **Call with `shell=True`:** While this method mimics manual launch and can solve filename issues, it does not solve the `stdin` waiting problem and is considered less secure.
3.  **Using the `ffmpeg-python` library without parameters:** This is the cleanest approach, but it also hangs by default, as it does not solve the `stdin` issue.

---

## 3. Reliable Solution: `ffmpeg-python` with the `-nostdin` Flag

The final, reliable, and stable method combines the convenience of the `ffmpeg-python` library with a key command-line flag.

**Key solution components:**

1.  **Using the `ffmpeg-python` library:** It provides a convenient and "pythonic" interface for building complex `ffmpeg` commands.
2.  **The `-nostdin` flag:** This is the most important part. This flag explicitly tells `ffmpeg` **not to attempt** reading from the standard input stream. This eliminates the root cause of hanging in non-interactive environments.
3.  **Correct syntax:** It is important to correctly pass this global flag to the library.

### Example Working Code

Here is the final, tested code from `src/core/media_processor.py`:

```python
import ffmpeg
# ... other imports

# ...

try:
    # 1. Build the operation chain using ffmpeg-python
    # 2. Add the global -nostdin flag via the `cmd` parameter in the .run() function
    # 3. Use .overwrite_output() for proper file overwriting
    (
        ffmpeg
        .input(original_file_name)
        .output(wav_file_name, ac=1, ar=16000) # ac=mono, ar=sample rate
        .overwrite_output()
        .run(cmd=['ffmpeg', '-nostdin'], capture_stdout=True, capture_stderr=True)
    )
    logger.info(f"[{firestore_ref}] Conversion successful")

except ffmpeg.Error as e:
    # If ffmpeg returns an error, it will be caught and logged
    logger.error(f"[{firestore_ref}] FFMPEG Error: {e.stderr.decode()}", exc_info=True)
    raise
```

**Explanation of `.run(cmd=['ffmpeg', '-nostdin'])` syntax:**
The `cmd` parameter in the `.run()` function allows you to override the launch command. By specifying `['ffmpeg', '-nostdin']`, you force the library to put the `-nostdin` flag at the very beginning of the command, making it global and solving the problem.

This approach is reliable, safe, and recommended for using `ffmpeg` in any automated Python scripts, especially in background tasks and queues.
