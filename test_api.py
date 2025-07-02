# test_api.py
import requests
import json

BASE_URL = "http://localhost:5000"

def test_research_flow():
    # 1. Start research
    start_data = {
        "query": "Self Driving Cars",
        "depth": 4,
        "breadth": 7
    }
    start_resp = requests.post(f"{BASE_URL}/api/research/start", json=start_data)
    print("Start Status:", start_resp.status_code)
    print("Start Raw:", start_resp.text)
    start_json = start_resp.json()
    
    # 2. Complete research
    complete_data = {
        "research_id": start_json["research_id"],
        "query": start_json["query"],
        "follow_up_answers": [
            "Deep Learning Algorithm",
            "USA and India",
            "All aspects"
        ],
        "mode": "report"
    }
    complete_resp = requests.post(f"{BASE_URL}/api/research/complete", json=complete_data)
    print("\nComplete Status:", complete_resp.status_code)
    print("Complete Raw:", complete_resp.text)
    
    try:
        complete_json = complete_resp.json()
        print("Complete JSON:", json.dumps(complete_json, indent=2))
    except Exception as e:
        print("Failed to parse JSON:", str(e))
    
    # 3. Download report if available
    if complete_resp.ok:
        try:
            if complete_json.get("output_files", {}).get("report_path"):
                report = requests.get(f"{BASE_URL}/api/research/download/{complete_json['output_files']['report_path']}")
                with open("downloaded_report.md", "wb") as f:
                    f.write(report.content)
                print("\nReport saved to downloaded_report.md")
        except Exception as e:
            print("Download failed:", str(e))

if __name__ == "__main__":
    test_research_flow()