from flask import Flask, render_template, request, send_file
from groq import Groq
import os
import pdfkit
import jinja2

app = Flask(__name__)
env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_content(topic):
    prompt = f"Escreva um conteúdo detalhado e acadêmico sobre: {topic}. Inclua introdução, desenvolvimento e conclusão."
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7
    )
    return response.choices[0].message.content

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form["title"]
        theme = request.form["theme"]
        members = int(request.form["members"])

        subtopics = []
        contents = []

        for i in range(members):
            subtopic = f"{theme} - Parte {i+1} (Aluno {i+1})"
            content = generate_content(subtopic)
            subtopics.append(subtopic)
            contents.append(content)

        conclusion = generate_content(f"Conclusão geral sobre {theme}")

        return render_template("resultado.html", title=title, theme=theme,
                               subtopics=subtopics, contents=contents,
                               conclusion=conclusion)
    return render_template("index.html")

@app.route("/download_pdf")
def download_pdf():
    rendered_html = request.args.get("html")
    pdf = pdfkit.from_string(rendered_html, False)
    return send_file(pdf, as_attachment=True, download_name="seminario.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(debug=True)
