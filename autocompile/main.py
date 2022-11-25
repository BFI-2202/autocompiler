import os
import tempfile
import subprocess
from github import Github
from fastapi import FastAPI, Body


app = FastAPI()
ORGANIZATION_NAME = os.getenv("ORGANIZATION_NAME")
RENDERS_DIRECTORY = os.getenv("RENDERS_DIRECTORY")

g = Github(os.getenv("ACCESS_TOKEN"))


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
	return output_directory, output_filename


def materialize_file(repo, filepath: str):
	file = tempfile.NamedTemporaryFile()
	file.write(repo.get_contents(filepath).decoded_content)
	yield file


def get_render_contents(repo, filepath: str, output_directory: str):
	with materialize_file(repo, filepath) as file:
		pdf_directory, pdf_filename = generate_pdf(file.name, output_directory)
	with open(f"{pdf_directory}/{pdf_filename}") as f:
		contents = f.read()
	return pdf_filename, contents


def upload_render(path: str, filename: str, message: str, contents: str, ref: str):
	repo.create_file(f"{path}/{RENDERS_DIRECTORY}/{filename}", message, contents, ref)


@app.post("/{repository}")
def push_hook(repository: str, payload: dict = Body(...)):	
	files = payload["commits"]["added"]
	repo = g.get_repo(f"{ORGANIZATION_NAME}/{repository}")
	ref = payload["ref"].split("/")[-1]

	with tempfile.TemporaryDirectory() as tmpdirname:
		new_contents = [extract_contents(filename) for filename in files]
		for filename in files:
			pdf_filename, contents = get_render_contents(repo, filename, tmpdirname)
			upload_render(
				"/".join(filename.split("/")[:-1]), pdf_filname, "Upload lecture render", contents, ref
			)

		month_directory = files[0].split("/")[:-1] # BE AWARE OF EMPTY LIST
		month = month_directory.split("/")[-1]

		with materialize_file(repo, f"{month_directory}/{month}.tex") as file:
			old_contents = file.read()
			pdf_filename, pdf_contents = get_render_contents(repo, f"{month_directory}/{month}.tex", tmpdirname)
		end_of_document = old_contents.find("\\end{document}")
		overall_contents = old_contents[:end_of_document] + "\n".join(new_contents) + old_contents[end_of_document:]

		repo.update_file(f"{month_directory}/{month}.tex", "Update overall month notes file", overall_contents, ref)
		upload_render(
			month_directory, pdf_filename, "Upload overall month render", pdf_contents, ref
		)
