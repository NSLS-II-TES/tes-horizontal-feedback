import subprocess


def test_cli_help():
    "Test that the CLI starts up without errors."
    # This raises CalledProcessError if it exits with a nonzero exit code.
    subprocess.check_call(['python', 'horizontal_feedback.py', '-h'])
