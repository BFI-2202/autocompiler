import os
import subprocess


def extract_contents(filename: str):
	with open(filename) as f:
		contents = f.read()

	start_of_contents = contents.find("\\section")
	end_of_contents = contents.find("\\end{document}")
	contents = contents[start_of_contents:end_of_contents]

	return contents.replace("\\pagebreak", "")


def generate_pdf(filename: str, output_directory: str = "render"):
	subprocess.run(["pdflatex", f"{filename}"])
	subprocess.run(["pdflatex", f"{filename}"])
	subprocess.run(["latexmk", "-c"])

	if not os.path.exists(output_directory):
		os.mkdir(output_directory)

	output_filename = filename[:-3] + "pdf"
	os.rename(
		f"{output_filename}", f"{output_directory}/{output_filename}"
	)
