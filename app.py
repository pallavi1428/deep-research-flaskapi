import asyncio
import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from typing import List, Dict, Optional, Callable, Tuple
from pydantic import BaseModel
import httpx
from fpdf import FPDF
import markdown2
from config import Config
from providers import get_model, trim_prompt
from prompt import system_prompt

app = Flask(__name__)
app.config.from_object(Config)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

class PDFReportGenerator:
    def generate_from_markdown(self, markdown: str, output_path: str) -> bool:
        try:
            html = markdown2.markdown(markdown)
            pdf = FPDF()
            pdf.add_page()
            try:
                pdf.add_font('DejaVu', '', Config.PDF_FONT_PATH, uni=True)
                pdf.set_font('DejaVu', size=12)
            except:
                pdf.set_font('Arial', size=12)
            pdf.multi_cell(0, 10, html)
            pdf.output(output_path)
            return True
        except Exception as e:
            print(f"PDF generation error: {str(e)}")
            return False

def get_model():
    class MockModel:
        def generate(self, messages):
            return "Mock response with some learnings\n- Learning 1\n- Learning 2"
    return MockModel()

def trim_prompt(text, max_length=25000):
    return text[:max_length]

def system_prompt():
    return "You are a helpful research assistant."

async def generate_serp_queries(prompt: str, learnings: Optional[List[str]] = None, num_queries: int = 3) -> List[Dict]:
    model = get_model()
    previous_learnings = ""
    if learnings:
        previous_learnings = "Previous learnings:\n" + "\n".join(learnings)

    user_prompt = f"""Given the user prompt below, generate up to {num_queries} unique SERP queries.
<query>{prompt}</query>

{previous_learnings}
"""
    messages = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": user_prompt},
    ]
    response = model.generate(messages)
    lines = [line.strip("- ").strip() for line in response.split("\n") if line.strip()]
    return [{"query": q, "researchGoal": ""} for q in lines[:num_queries]]

async def fetch_serp_results(query: str) -> List[Dict]:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.firecrawl.dev/v1/search",
                headers={"Authorization": f"Bearer {app.config['FIRECRAWL_KEY']}"},
                json={"query": query, "limit": 5, "scrapeOptions": {"formats": ["markdown"]}},
            )
            response.raise_for_status()
            return response.json().get("data", [])
    except Exception as e:
        print(f"Search failed for '{query}': {str(e)}")
        return []

async def process_serp(query: str, results: List[Dict]) -> Tuple[List[str], List[str]]:
    contents = [trim_prompt(r.get("markdown", ""), 25000) for r in results if r.get("markdown")]
    combined_content = "\n".join([f"<content>{c}</content>" for c in contents])

    model = get_model()
    prompt = f"""From the following SERP results, extract up to 3 key learnings and 3 follow-up questions to explore the topic further.

<query>{query}</query>
{combined_content}
"""
    messages = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": trim_prompt(prompt)},
    ]
    response = model.generate(messages)

    learnings = []
    questions = []
    for line in response.split("\n"):
        if "?" in line:
            questions.append(line.strip("- ").strip())
        elif line.strip():
            learnings.append(line.strip("- ").strip())
    return learnings[:3], questions[:3]

async def deep_research(
    query: str,
    depth: int,
    breadth: int,
    learnings: Optional[List[str]] = None,
    visited_urls: Optional[List[str]] = None,
) -> Dict[str, List[str]]:
    learnings = learnings or []
    visited_urls = visited_urls or []
    serp_queries = await generate_serp_queries(query, learnings, num_queries=breadth)

    semaphore = asyncio.Semaphore(5)
    all_learnings = list(learnings)
    all_urls = list(visited_urls)

    async def handle_query(q_obj: Dict):
        q = q_obj["query"]
        async with semaphore:
            try:
                results = await fetch_serp_results(q)
                urls = [r["url"] for r in results if r.get("url")]
                new_learnings, followups = await process_serp(q, results)

                all_learnings.extend(new_learnings)
                all_urls.extend(urls)

                if depth > 1:
                    followup_query = f"{q}\n" + "\n".join(followups)
                    result = await deep_research(
                        query=followup_query,
                        depth=depth - 1,
                        breadth=max(1, breadth // 2),
                        learnings=all_learnings,
                        visited_urls=all_urls,
                    )
                    all_learnings.extend(result["learnings"])
                    all_urls.extend(result["visited_urls"])
            except Exception as e:
                print(f"[error] {q}: {e}")

    await asyncio.gather(*[handle_query(q) for q in serp_queries])

    return {
        "learnings": list(set(all_learnings)),
        "visited_urls": list(set(all_urls)),
    }

def generate_feedback(query: str, num_questions: int = 3) -> list[str]:
    model = get_model()
    prompt = f"""Given the following user query, ask up to {num_questions} follow-up questions to clarify the research direction.

<query>{query}</query>
"""
    messages = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": prompt},
    ]
    raw_output = model.generate(messages)
    return [q.strip("- ").strip() for q in raw_output.split("\n") if q.strip()][:num_questions]

def write_final_report(prompt: str, learnings: list[str], visited_urls: list[str]) -> str:
    model = get_model()
    
    # Create structured prompt
    full_prompt = f"""Create a comprehensive technical report in markdown format about {prompt}.
    
    Follow this exact structure:
    
    # [Main Title] - [Subtitle if applicable]
    
    ## 1. Introduction
    [Context and significance]
    
    ## 2. Architectural Innovations
    - Key technological advancements
    - Design improvements
    - Technical specifications (use tables when appropriate)
    
    ## 3. Performance Benchmarks
    - Comparative performance data
    - Real-world metrics
    - Efficiency analysis
    
    ## 4. Market Analysis
    - Competitive landscape
    - Pricing strategy
    - Consumer reception
    
    ## 5. Conclusion
    - Summary of key findings
    - Future outlook
    
    Incorporate these specific learnings:
    {learnings}
    """
    
    messages = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": trim_prompt(full_prompt)},
    ]
    
    report = model.generate(messages)
    report += "\n\n## Sources\n" + "\n".join(f"- {url}" for url in visited_urls)
    return report

def write_final_answer(prompt: str, learnings: list[str]) -> str:
    model = get_model()
    formatted_learnings = "\n".join(f"<learning>\n{l}\n</learning>" for l in learnings)
    full_prompt = f"""Using the learnings below, write a short final answer to the user's original prompt. Be concise and respect the format of the original question if specified.

<prompt>{prompt}</prompt>

<learnings>
{formatted_learnings}
</learnings>
"""
    messages = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": trim_prompt(full_prompt)},
    ]
    return model.generate(messages).strip()

@app.route('/api/research/start', methods=['POST'])
def start_research():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        questions = generate_feedback(data['query'])
        return jsonify({
            'research_id': str(uuid.uuid4()),
            'query': data['query'],
            'follow_up_questions': questions,
            'depth': int(data.get('depth', 2)),
            'breadth': int(data.get('breadth', 4))
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'}), 500

@app.route('/api/research/complete', methods=['POST'])
async def complete_research():
    try:
        data = request.get_json()
        if not data or 'research_id' not in data or 'query' not in data:
            return jsonify({'error': 'Research ID and query are required'}), 400

        combined_query = data['query']
        if data.get('follow_up_answers'):
            questions = generate_feedback(data['query'])
            combined_query = f"Initial Query: {data['query']}\n\nFollow-up Questions and Answers:\n"
            combined_query += "\n".join(f"Q: {q}\nA: {a}" for q, a in zip(questions, data['follow_up_answers']))

        result = await deep_research(
            query=combined_query,
            depth=int(data.get('depth', 2)),
            breadth=int(data.get('breadth', 4)),
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_files = {}
        
        if data.get('mode', 'report') == "report":
            content = write_final_report(combined_query, result['learnings'], result['visited_urls'])
            filename = f"report_{timestamp}"
        else:
            content = write_final_answer(combined_query, result['learnings'])
            filename = f"answer_{timestamp}"

        md_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{filename}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        output_files['report_path'] = f"{filename}.md"

        pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{filename}.pdf")
        if PDFReportGenerator().generate_from_markdown(content, pdf_path):
            output_files['pdf_path'] = f"{filename}.pdf"

        return jsonify({
            'research_id': data['research_id'],
            'query': data['query'],
            'learnings': result['learnings'],
            'visited_urls': result['visited_urls'],
            'output_files': output_files,
            'status': 'completed'
        })

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'}), 500

@app.route('/api/research/download/<filename>', methods=['GET'])
def download_file(filename):
    safe_filename = secure_filename(filename)
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], safe_filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)