from dotenv import load_dotenv
from anthropic import Anthropic

import json
import csv

load_dotenv()
client = Anthropic()

def load_json_data():
    with open("test_files/Capstone.json", "r") as file:
        data = json.load(file)
    return data

json_data = load_json_data()

def write_csv_file():
    with open("bug_reports.csv", "w", newline='', encoding='utf-8') as file:
        headers = json_data[0].keys()

        writer = csv.DictWriter(file, fieldnames = headers)

        writer.writeheader()
        writer.writerows(json_data)

def get_dict_row():
    with open("bug_reports.csv", "r", newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))

rows = get_dict_row()

def summary(row_dict):
    message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=300,
    system = "You are a dev lead triaging a bug, read it and write a summary. The summary should always include : main issue and the subject should be the program or the build, not the component that's being tested, the repro rate based on attempts and seen where Attempts are deliverate QA repro tries; Seen is the total times the bug as occurred, including hits by users without deliberate attempts, so don't call Seen successful attempts, the severity letter and the status. If the build fixed in field is empty refer to the Status, for all bugs with the Closed(No Repro) status no fix build is expected, if the status is Closed(Fixed) then explicitly name the fix build. Use only facts present in the bug data, don't assume causes and don't recommend anything either. Name the status exactly as written. Severity status 'A' is the highest and it goes below to 'D', don't add your own words such as 'Critical', 'Emergency' or anything else you deem fit. always write the repro rate as X of Y attempts (Z%) .Limit to 2-3 sentences max in plain text only, begin directly with the first word of the summary. NEVER START WITH A LABEL LIKE 'SUMMARY' OR ANY OTHER HIGHLIGHTS",
    messages=[{"role": "user", "content": f"""Description : {row_dict['Description']} , Severity : {row_dict['Severity']} , Status : {row_dict['Status']}, Attempts : {row_dict['Verification Attempts']}, 
               Seen : {row_dict['Verification Seen']}, Build found in : {row_dict['Build Seen In']}, Build Fixed in : {row_dict['Build Fixed In']}, Platform : {row_dict['Platform']}"""}],
    )
    return(message.content[0].text)
    
def save_results(filename, data):
    with open(filename, "w", encoding='utf-8') as file:
        json.dump(data, file, indent=2)

def generate_summaries():
    summaries = {}
    for bug in rows:
        api_response = summary(bug)
        if api_response.lower().startswith("summary") or "**" in api_response:
            print(f"Warning : {bug['Bug ID']} starts with a label")
        summaries[bug['Bug ID']] = api_response
        print(bug['Bug ID'], ":", api_response)
    save_results("summaries.json", summaries)

def load_results(filename):
    with open(filename, "r") as file:
        try:
            result_data = json.load(file)
            return result_data
        except json.JSONDecodeError:
            print("Incorrect input!")
            return None
        except FileNotFoundError:
            print("File not found!")
            return None

final_data = load_results("summaries.json")

sev_counts = {}
status_counts = {}
for row in rows:
    sev = row['Severity']
    status = row['Status']
    sev_counts[sev] = sev_counts.get(sev, 0) + 1
    status_counts[status] = status_counts.get(status, 0) + 1

lines = []

sorted_rows = sorted(rows, key=lambda p: p["Severity"])

lines.append("")
lines.append("Summaries : ")
for row in sorted_rows:
    bug_id = row['Bug ID']
    lines.append(f"{bug_id} : {final_data[bug_id]}")

report_input = "\n".join(lines)

def generate_report(text):
    message2 = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system="""You are a QA Lead writing a status report overview for a dev lead. The report should highlight
        the highest severity bugs from A to D, every bug, each new line starts with the ID, the severity written as "Severity A" with the corresponding letter and the status. 
        Then if a bug has a fix build, write "fixed in" directly before that build number,
        keep build numbers unchanged, write a short description of the issue, then the repro figures
        written as "X of Y attempts"
        Don't modify any values whatsoever.Don't add severity words such as 'Critical'.
        Don't invent any new information yourself, keep it simple with no headings, plain text only, no markdowns and no '**'. Use only the information in the input
        and don't recommend or prioritize anything, only write one line per bug, do NOT write any severity or status count summary lines. """,
        messages=[{"role": "user", "content": text}],
    )
    return message2.content[0].text

sev_line = []
for sev, count in sorted(sev_counts.items()):
    sev_string = (f"{sev} : {count}")
    sev_line.append(sev_string)
sev_text = ", ".join(sev_line)
print(sev_text)

status_line = []
for status, count in sorted(status_counts.items()):
    status_string = (f"{status} : {count}")
    status_line.append(status_string)
status_text = ", ".join(status_line)

def check_report(report):
    bug_id_flag = True
    count_check_flag = True
    stat_count_flag = True
    for bug_id in final_data:
        if bug_id in report:
            print("PASS", bug_id)
        else:
            print("FAIL : Expected", bug_id, "not found in report")
            bug_id_flag = False

    print("Status Counts Check : \n")
    for status, count in sorted(status_counts.items()):
        stat_str = f"{status} : {count}"
        if stat_str in report:
            print("PASS", stat_str)
        else:
            print("FAIL", stat_str)
            stat_count_flag = False

    print("Severity Counts Check : \n")
    for sev, count in sorted(sev_counts.items()):
        my_str = f"{sev} : {count}"
        if my_str in report:
            print("PASS", my_str)
        else:
            print("FAIL : Expected", my_str, "not found in report")
            count_check_flag = False

    print("Order Check : \n")
    previous = -1
    order_ok = True
    for row in sorted_rows:
        pos = report.find(row["Bug ID"])
        if pos < previous:
           print("FAIL ", row["Bug ID"])
           order_ok = False
        else:
            print("PASS ", row['Bug ID'])
        previous = pos

    test_text = report.split("\n")
    line_flag = True
    for row in sorted_rows:
        for text in test_text:
            if text.startswith(f"{row['Bug ID']}"):
                if f"Severity {row['Severity']}" not in text:
                    print(f"FAIL : {row['Bug ID']}, Severity Missing")
                    line_flag = False
                if row['Build Fixed In']:
                    if "fixed in" not in text.lower():
                        print(f"FAIL : {row['Bug ID']}, Fixed In not mentioned")
                        line_flag = False
                    if row['Build Fixed In'] not in text:
                        print(f"FAIL : {row['Bug ID']}, Build No. Fixed in not mentioned")
                        line_flag = False
                if f"{row['Verification Seen']} of {row['Verification Attempts']}" not in text:
                    print(f"FAIL : {row['Bug ID']}, Repro Figure Missing")
                    line_flag = False

    return {"Bug IDs" : bug_id_flag, "Severity" : count_check_flag, "Status" : stat_count_flag, "Order" : order_ok, "Lines" : line_flag}


def save_report(report_text, check_results, filename):
    res_dict = {"Report" :report_text, "Results" : check_results}
    with open(filename, "w", encoding='utf-8') as file:
        json.dump(res_dict, file, indent=2, ensure_ascii=False)

passed = 0
for i in range(4):
    print(f"Run {i + 1}")
    loop_report = generate_report(report_input)
    full_report = "\n".join([sev_text, status_text, "", loop_report])
    results = check_report(full_report)
    save_report(full_report, results, f"report_results_{i}.json")
    if all(results.values()):
        passed += 1
print(f"Total Passed : {passed}")
