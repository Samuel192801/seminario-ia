from flask import Flask, render_template, request, send_file
from groq import Groq
import os
import pdfkit
import jinja2

app = Flask(__name__)
env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))

# Inicializa cliente Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_content(topic):
    prompt = f"Escreva um conteúdo claro e objetivo sobre: {topic}. Inclua introdução, desenvolvimento e conclusão. Máximo 300 palavras."
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7
    )
    return response.choices[0].message.content


def generate_image(topic):
    # Simula busca de imagem (você pode substituir por uma API real depois)
    images = {
        "redes sociais": "https://via.placeholder.com/600x300?text=Redes+Sociais",
        "educação": "https://via.placeholder.com/600x300?text=Educação",
        "tecnologia": "https://via.placeholder.com/600x300?text=Tecnologia",
        "saúde": "https://via.placeholder.com/600x300?text=Saúde"
    }
    for key in images:
        if key.lower() in topic.lower():
            return images[key]
    return "https://via.placeholder.com/600x300?text=Imagem+Genérica"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form["title"]
        theme = request.form["theme"]
        members = int(request.form["members"])
        raw_integrantes = request.form.get("integrantes", "")

        integrantes = [nome.strip() for nome in raw_integrantes.split('\n') if nome.strip()]

        subtopics = []
        contents = []
        images = []

        for i in range(members):
            subtopic = f"{theme} - Parte {i+1} (Aluno {i+1})"
            content = generate_content(subtopic)
            image = generate_image(subtopic)

            subtopics.append(subtopic)
            contents.append(content)
            images.append(image)

        conclusion = generate_content(f"Conclusão geral sobre {theme}")

        return render_template("resultado.html",
                               title=title,
                               theme=theme,
                               integrantes=integrantes,
                               subtopics=subtopics,
                               contents=contents,
                               images=images,
                               conclusion=conclusion)

    return render_template("index.html")


@app.route("/download_pdf")
def download_pdf():
    rendered_html = request.args.get("html")
    pdf = pdfkit.from_string(rendered_html, False)
    return send_file(pdf, as_attachment=True, download_name="seminario.pdf", mimetype='application/pdf')


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
