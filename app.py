from flask import Flask, render_template, request, send_file
from groq import Groq
import os
import requests
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

app = Flask(__name__)
env = Environment(loader=jinja2.FileSystemLoader("templates"))

# Inicializa cliente Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def google_search(query):
    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")

    url = "https://www.googleapis.com/customsearch/v1" 
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": 3
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []
    if "items" in data:
        for item in data["items"]:
            results.append({
                "title": item["title"],
                "link": item["link"],
                "snippet": item["snippet"]
            })
    return results


def search_image(topic):
    url = "https://api.unsplash.com/search/photos" 
    headers = {
        "Authorization": f"Client-ID {os.getenv('UNSPLASH_ACCESS_KEY')}"
    }
    params = {"query": topic, "orientation": "landscape", "per_page": 1}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data["results"]:
        photo = data["results"][0]
        return {
            "url": photo["urls"]["regular"],
            "credit": f"Foto por <a href='{photo['user']['links']['html']}'>{photo['user']['name']}</a> no Unsplash"
        }
    return None


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
            search_results = google_search(subtopic)

            context = "\n".join([f"{r['title']}: {r['snippet']} ({r['link']})" for r in search_results])
            prompt = f"""
            Escreva um trecho acadêmico sobre: {subtopic}
            
            Use as seguintes fontes:
            {context}
            
            Explique o tema com suas próprias palavras.
            Não use frases genéricas como 'claro, aqui estão as informações'.
            Formato: Introdução, desenvolvimento, conclusão breve.
            Tamanho: {'Detalhado' if detailed else 'Resumido'}
            """

            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.7
            )
            content = response.choices[0].message.content

            image = search_image(subtopic)

            contents.append({
                "text": content,
                "references": [(r["title"], r["link"]) for r in search_results],
                "image": image
            })
            subtopics.append(subtopic)

        # Conclusão
        conclusion_prompt = f"Escreva uma conclusão geral sobre {theme}, baseada nos tópicos acima."
        conclusion_response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": conclusion_prompt}],
            max_tokens=400,
            temperature=0.7
        )
        conclusion = conclusion_response.choices[0].message.content

        # Referências finais
        final_ref_prompt = f"Com base no tema '{theme}', liste 5 referências acadêmicas reais e relevantes. Use ABNT."
        final_ref_response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": final_ref_prompt}],
            max_tokens=500,
            temperature=0.7
        )
        final_references = final_ref_response.choices[0].message.content

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
    pdf = HTML(string=rendered_html).write_pdf()
    return send_file(pdf, as_attachment=True, download_name="seminario.pdf", mimetype='application/pdf')


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
