from flask import Flask, render_template, request, send_file
from groq import Groq
import os
import pdfkit
import jinja2

app = Flask(__name__)
env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))

# Inicializa cliente Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def search_and_generate(topic, detailed=False):
    prompt = f"""
    Você é um pesquisador experiente que está buscando informações reais sobre: {topic}.
    
    Passo 1: Faça uma busca fictícia na internet, usando sites confiáveis como:
    - artigos científicos (Google Scholar)
    - teses e dissertações
    - livros acadêmicos
    - instituições sérias (ex: UNESCO, Fiocruz, INEP)

    Passo 2: Com base nessas fontes, escreva um trecho acadêmico com:
    - Introdução clara
    - Desenvolvimento objetivo
    - Conclusão breve
    - Duas ou três referências reais formatadas em ABNT
    
    Use linguagem didática, como se fosse escrito por um aluno.
    """
    if detailed:
        prompt += "\nInclua mais detalhes técnicos e exemplos reais."

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.7
    )
    return response.choices[0].message.content


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form["title"]
        theme = request.form["theme"]
        members = int(request.form["members"])
        raw_integrantes = request.form.get("integrantes", "")
        detailed = "detailed" in request.form

        integrantes = [nome.strip() for nome in raw_integrantes.split('\n') if nome.strip()]

        subtopics = []
        contents = []

        for i in range(members):
            subtopic = f"{theme} - Parte {i+1} (Aluno {i+1})"
            content = search_and_generate(subtopic, detailed=detailed)

            # Separa conteúdo e referências
            parts = content.split("Referências:")
            main_content = parts[0]
            references = parts[1] if len(parts) > 1 else ""

            contents.append({
                'text': main_content,
                'references': references.strip()
            })
            subtopics.append(subtopic)

        conclusion = search_and_generate(f"Conclusão geral sobre {theme}")

        # Gera referências finais consolidadas
        ref_prompt = f"""
        Com base no tema '{theme}', liste 5 referências acadêmicas reais e relevantes.
        Use o formato ABNT e cite apenas fontes confiáveis, como artigos científicos,
        teses, livros acadêmicos ou instituições sérias como UNESCO, Fiocruz, etc.
        """
        ref_response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": ref_prompt}],
            max_tokens=500,
            temperature=0.7
        )
        final_references = ref_response.choices[0].message.content

        return render_template("resultado.html",
                               title=title,
                               theme=theme,
                               integrantes=integrantes,
                               subtopics=subtopics,
                               contents=contents,
                               conclusion=conclusion,
                               final_references=final_references)

    return render_template("index.html")


@app.route("/download_pdf")
def download_pdf():
    rendered_html = request.args.get("html")
    options = {
        'page-size': 'A4',
        'margin-top': '25mm',
        'margin-right': '20mm',
        'margin-bottom': '25mm',
        'margin-left': '20mm',
        'encoding': "UTF-8"
    }
    pdf = pdfkit.from_string(rendered_html, False, options=options)
    return send_file(pdf, as_attachment=True, download_name="seminario.pdf", mimetype='application/pdf')


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
