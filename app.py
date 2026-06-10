import os
import time
from flask import Flask, render_template, request, redirect, url_for
from pypdf import PdfReader
from google import genai

app = Flask(__name__)

if not os.path.exists('uploads'):
    os.makedirs('uploads')

# --- NEW: LOGIN PAGE ROUTE ---
@app.route('/')
def login_page():
    # This automatically shows your beautiful new split-screen login page first!
    return render_template('login.html')

# --- NEW: LOGIN SUBMISSION ROUTE ---
@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Simple, secure check for your enterprise portal
    if username == "admin" and password == "NYC_AI_2026":
        # If correct, send them to the document uploader workspace
        return redirect(url_for('workspace'))
    else:
        return "<h3>Access Denied:</h3><p>Invalid username or password. Please go back and try again.</p>", 401

# --- UPDATED: THE ACTUAL AUDIT WORKSPACE ---
@app.route('/workspace')
def workspace():
    # This renders your document upload screen (index.html)
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file selected", 400
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file", 400

    if file:
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        
        # 1. Read the user's uploaded document text
        try:
            reader = PdfReader(file_path)
            extracted_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text = extracted_text + text + "\n"
        except Exception as e:
            return f"Error reading file: {str(e)}", 400

        # 2. Read the Law Book Knowledge Base
        try:
            with open('nyc_r6_rules.txt', 'r') as law_file:
                zoning_laws = law_file.read()
        except Exception as e:
            return "<h3>Error loading Knowledge Base.</h3>", 500

        # 3. Call the Real AI Brain with Smart Retries
        prompt = f"""
        You are an expert NYC Zoning Auditor checking compliance for an R6 Quality Housing District.
        
        OFFICIAL ZONING LEGAL TEXT source of truth:
        \"\"\"{zoning_laws}\"\"\"
        
        Analyze the following document text:
        \"\"\"{extracted_text}\"\"\"
        
        Perform 3 precise audits based strictly on the provided legal text rules and exceptions:
        1. Maximum Building Height
        2. Maximum Lot Coverage
        3. Minimum Rear Yard Depth
        
        Return output strictly as a single clean HTML table snippet (no markdown block quotes like ```html):
        
        <tr style='border-bottom: 1px solid #e2e8f0;'>
            <td style='padding: 16px; font-weight: 600; color: #1e293b;'>Maximum Building Height</td>
            <td style='padding: 16px; color: #475569;'>60 Feet Max</td>
            <td style='padding: 16px;'>[Insert status badge like '<span style="background-color: #fee2e2; color: #991b1b; padding: 6px 12px; border-radius: 9999px; font-weight: bold; font-size: 14px;">🔴 FAILED</span>' or '<span style="background-color: #dcfce7; color: #166534; padding: 6px 12px; border-radius: 9999px; font-weight: bold; font-size: 14px;">🟢 PASSED</span>' followed by details quoting the law section used]</td>
        </tr>
        <tr style='border-bottom: 1px solid #e2e8f0;'>
            <td style='padding: 16px; font-weight: 600; color: #1e293b;'>Maximum Lot Coverage</td>
            <td style='padding: 16px; color: #475569;'>60% Max (Interior) / 80% Max (Corner)</td>
            <td style='padding: 16px;'>[Insert status badge and details quoting the law section used]</td>
        </tr>
        <tr>
            <td style='padding: 16px; font-weight: 600; color: #1e293b;'>Minimum Rear Yard Depth</td>
            <td style='padding: 16px; color: #475569;'>30 Feet Min (Exceptions apply)</td>
            <td style='padding: 16px;'>[Insert status badge and details quoting the law section used]</td>
        </tr>
        """

        client = genai.Client()
        ai_table_rows = ""
        
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                ai_table_rows = response.text
                break
            except Exception as e:
                if "503" in str(e) and attempt < 2:
                    print(f"Google server busy. Retrying in 2 seconds... (Attempt {attempt + 1}/3)")
                    time.sleep(2)
                else:
                    return f"<h3>AI Connection Error:</h3><p>{str(e)}</p>", 500

        # 4. Render the template cleanly
        return render_template('report.html', filename=file.filename, ai_rows=ai_table_rows)

if __name__ == '__main__':
    app.run(debug=True, port=5001)