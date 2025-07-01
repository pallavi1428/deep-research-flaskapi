import asyncio
from datetime import datetime
from pathlib import Path
from feedback import generate_feedback
from research import deep_research
from report import write_final_answer, write_final_report
from pdf_generator import PDFReportGenerator

class ResearchEngine:
    async def process_request(self, data):
        research_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if data['mode'] == 'report':
            questions = generate_feedback(data['query'])
            if 'answers' not in data:
                return {
                    "status": "needs_followup",
                    "questions": questions,
                    "research_id": research_id
                }
            combined_query = self._build_query(data['query'], questions, data['answers'])
        else:
            combined_query = data['query']

        # Conduct research (same as CLI version)
        result = await deep_research(
            query=combined_query,
            depth=data['depth'],
            breadth=data['breadth']
        )

        # Generate outputs
        if data['mode'] == 'report':
            content = write_final_report(combined_query, result['learnings'], result['visited_urls'])
            base_name = f"report_{timestamp}_{research_id}"
        else:
            content = write_final_answer(combined_query, result['learnings'])
            base_name = f"answer_{timestamp}_{research_id}"

        # Save files
        md_path = f"storage/reports/{base_name}.md"
        pdf_path = f"storage/reports/{base_name}.pdf"
        
        Path(md_path).write_text(content, encoding='utf-8')
        
        pdf_gen = PDFReportGenerator()
        pdf_gen.generate_from_markdown(content, pdf_path)

        return {
            "status": "complete",
            "research_id": research_id,
            "markdown_file": f"{base_name}.md",
            "pdf_file": f"{base_name}.pdf",
            "summary": {
                "learnings": result['learnings'][:5],
                "sources": result['visited_urls'][:3]
            }
        }

    def _build_query(self, query, questions, answers):
        return f"Initial Query: {query}\n\nFollow-up Q&A:\n" + \
               "\n".join(f"Q: {q}\nA: {a}" for q, a in zip(questions, answers))