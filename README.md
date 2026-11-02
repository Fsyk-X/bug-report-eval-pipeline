# Bug Report Evaluation Pipeline

- Read list of bugs
- Summarize with Haiku
- Builds a text report
- Run the checks 
- Saves the results as a report + flags saved to a JSON file

## The checks
- Bug IDs present - Every bug ID appears in the report accurately
- Severity Counts - The count lines (A:3, B:2,etc) match the real data
- Status Counts - The status lines (PASS Closed(Fixed) : 2) match the real data
- Ordering - Bugs appear sorted by severity, from A -> D (Using .find() positions)
- Lines - Each bug's line contains the accurate details such as "Severity X", "Fixed In", "Build Number" and the repro figure as well ("X of Y attempts")

 ## Results
 - 4/4 runs passed, and each check was broken by feeding it a report with wrong count, status or order to confirm it fails.

## What I learned 
- Prompt for the AI is to be very specific to get desired results, vague words causes defects, and can sometimes cause the AI to add their own assumptions. 
 - Do exact work like counting and sorting in code instead of relying on the LLM. 
 - My checks only catch what they're aimed at, so a defect nothing looks for passes silently.
 - One run isn't enough proof the prompt is accurate enough.

## How to run : 
```
pip install -r requirements.txt
```
Create a .env with ANTHROPIC_API_KEY, and note that the summaries are cached in summaries.json

## Limitations : 
- Tested with 8 mock bugs, 4 runs.