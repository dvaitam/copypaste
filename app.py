from flask import Flask, request, render_template_string
import os
import json

app = Flask(__name__)

# File to store submissions persistently
DATA_FILE = "submissions.json"

# Load existing submissions from file (persistent storage)
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f:
            submissions = json.load(f)
        if not isinstance(submissions, list):
            submissions = []
    except (json.JSONDecodeError, IOError):
        submissions = []
else:
    submissions = []

def save_submissions():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(submissions, f)
    except IOError:
        pass

# HTML template as a string
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Submission App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        textarea {
            width: 100%;
            box-sizing: border-box;
            font-size: 1rem;
            padding: 10px;
            margin-top: 10px;
        }
        button {
            background-color: #007BFF;
            color: #fff;
            border: none;
            padding: 10px 20px;
            font-size: 1rem;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background-color: #0056b3;
        }
        .submission { margin: 10px 0; padding: 10px; border: 1px solid #ccc; }
    </style>
</head>
<body>
    <h1>Submit Your Message</h1>
    <form method="POST" action="/">
        <textarea name="message" placeholder="Enter your message" required rows="5"></textarea>
        <button type="submit">Submit</button>
    </form>
    <form method="POST" action="/">
        <button type="submit" name="clear" value="true">Clear Messages</button>
    </form>
    <h2>Messages</h2>
    <div id="submissions">
        {% for submission in submissions|reverse %}
            {# Compute original index of submission for deletion #}
            {% set idx = submissions|length - loop.index0 - 1 %}
            <div class="submission">
                <pre><code>{{ submission }}</code></pre>
                <form method="POST" action="/">
                    <input type="hidden" name="delete_index" value="{{ idx }}">
                    <button type="submit">Delete</button>
                </form>
            </div>
        {% endfor %}
    </div>
    <script>
        function fallbackCopyTextToClipboard(text) {
            var textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand('copy');
            } catch (err) {
                console.error('Fallback: Oops, unable to copy', err);
            }
            document.body.removeChild(textArea);
        }

        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('pre > code').forEach(function(codeBlock) {
                var button = document.createElement('button');
                button.innerText = 'Copy';
                button.style.margin = '5px';
                button.addEventListener('click', function() {
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(codeBlock.innerText).then(function() {
                            button.innerText = 'Copied!';
                            setTimeout(function() { button.innerText = 'Copy'; }, 2000);
                        }).catch(function(err) {
                            console.error('Failed to copy text: ', err);
                        });
                    } else {
                        fallbackCopyTextToClipboard(codeBlock.innerText);
                        button.innerText = 'Copied!';
                        setTimeout(function() { button.innerText = 'Copy'; }, 2000);
                    }
                });
                var pre = codeBlock.parentNode;
                pre.parentNode.insertBefore(button, pre);
            });
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # If clear button pressed, clear all submissions
        if request.form.get("clear"):
            submissions.clear()
            save_submissions()
        # If delete button pressed, delete individual message
        elif request.form.get("delete_index") is not None:
            try:
                idx = int(request.form.get("delete_index"))
                if 0 <= idx < len(submissions):
                    submissions.pop(idx)
                    save_submissions()
            except (ValueError, TypeError):
                pass
        else:
            # Otherwise, handle new message submission
            message = request.form.get("message")
            if message:
                submissions.append(message)
                save_submissions()
    return render_template_string(HTML_TEMPLATE, submissions=submissions)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8800)
