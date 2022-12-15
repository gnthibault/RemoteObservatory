import os
import subprocess
from setuptools import Command

class GenReport(Command):
    """ Build latex reports
    """
    description = 'Build latex reports'

    user_options = [
            ('input-dir=', 'i', 'input directory'),
            ('output-dir=', 'o', 'output directory'),
        ]

    def initialize_options(self):
        self.input_dir = "documentation/papers/latex/"
        self.output_dir = "reports_build"

    def finalize_options(self):
        if self.input_dir is None:
            raise Exception("Parameter --input-dir is missing")
        if self.output_dir is None:
            raise Exception("Parameter --output-dir is missing")
        if not os.path.isdir(self.input_dir):
            raise Exception(f"Input directory does not exist: {self.input_dir}")
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except OSError as exc:
            raise Exception(f"Cannot create Output directory: {self.output_dir}")
        if not os.path.isdir(self.output_dir):
            raise Exception(f"Output directory does not exist: {self.output_dir}")

    def run(self):
        def _gen_report(directory):
            if self.verbose:  # verbose is provided "automagically"
                print(f"Generating report in {directory}")
                subprocess.call(["make", "pdf"],  cwd=directory)


        for directory in os.listdir(self.input_dir):
            _gen_report(os.path.join(self.input_dir, directory))


