from flask import Flask, request, render_template_string
from flask_socketio import SocketIO
import os
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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
    <title>copy paste</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
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
        .submission { margin: 10px 0; padding: 10px; border: 1px solid #ccc; position: relative; }
        .icon-button { background: none; border: none; cursor: pointer; padding: 5px; font-size: 1.2rem; color: inherit; }
        .icon-button.copy { position: absolute; top: 10px; right: 40px; }
        .icon-button.delete { position: absolute; top: 10px; right: 10px; }
        .submission pre { margin-top: 30px; }
        .icon-button:hover { background-color: transparent; }
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
                <form method="POST" action="/" class="delete-form" style="margin:0;">
                    <input type="hidden" name="delete_index" value="{{ idx }}">
                    <button type="submit" class="icon-button delete" title="Delete">&#128465;</button>
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

        function attachCopyButtonFunctionality(parentElement) {
            var codeBlock = parentElement.querySelector('pre > code');
            if (codeBlock) {
                var button = document.createElement('button');
                button.className = 'icon-button copy';
                button.title = 'Copy';
                button.innerHTML = '&#128203;'; // Copy icon
                button.addEventListener('click', function() {
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(codeBlock.innerText).then(function() {
                            button.innerHTML = '&#10003;'; // Checkmark icon
                            setTimeout(function() { button.innerHTML = '&#128203;'; }, 2000);
                        }).catch(function(err) {
                            console.error('Failed to copy text: ', err);
                            // Attempt fallback for specific errors or if clipboard API is not fully supported
                            fallbackCopyTextToClipboard(codeBlock.innerText);
                            button.innerHTML = '&#10003;'; // Checkmark icon
                            setTimeout(function() { button.innerHTML = '&#128203;'; }, 2000);
                        });
                    } else {
                        fallbackCopyTextToClipboard(codeBlock.innerText);
                        button.innerHTML = '&#10003;'; // Checkmark icon
                        setTimeout(function() { button.innerHTML = '&#128203;'; }, 2000);
                    }
                });
                var preElement = codeBlock.parentNode; // This is the <pre> element
                // Insert the button as a sibling of the <pre> element, effectively placing it next to it.
                // More precisely, to achieve the visual effect of the button being "on" the submission div
                // and aligned like the delete button, it should be a direct child of `newSubmissionDiv` (or `parentElement`).
                // The existing structure has it as `pre.parentNode.insertBefore(button, pre);`
                // which means it's added to the parent of `pre`. If `pre` is a direct child of `submission`,
                // then `pre.parentNode` is `submission`.
                if (preElement.parentNode === parentElement) {
                     parentElement.insertBefore(button, preElement); // Places button before the <pre> element
                } else {
                    // Fallback or error if structure is not as expected
                    // For now, let's assume preElement.parentNode is the submission div
                    preElement.parentNode.insertBefore(button, preElement);
                }
                 // To position it like the original (top right of the submission div, next to delete)
                // it should be added directly to parentElement and styled with position:absolute.
                // The CSS already handles .icon-button.copy { position: absolute; top: 10px; right: 40px; }
                // So, it just needs to be a child of parentElement (the submission div).
                parentElement.appendChild(button); // Appending as child, CSS will position it
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('#submissions .submission').forEach(function(submissionElement) {
                attachCopyButtonFunctionality(submissionElement);
            });

            var socket = io();
            socket.on('new_message', function(data) {
                var submissionsDiv = document.getElementById('submissions');
                var newSubmissionDiv = document.createElement('div');
                newSubmissionDiv.className = 'submission';

                // Add message content
                var pre = document.createElement('pre');
                var code = document.createElement('code');
                code.textContent = data.message;
                pre.appendChild(code);
                newSubmissionDiv.appendChild(pre);

                // Add delete form and button
                var deleteForm = document.createElement('form');
                deleteForm.method = 'POST';
                deleteForm.action = '/';
                deleteForm.className = 'delete-form';
                deleteForm.style.margin = '0';

                var deleteIndexInput = document.createElement('input');
                deleteIndexInput.type = 'hidden';
                deleteIndexInput.name = 'delete_index';
                deleteIndexInput.value = data.id; // Use the id from the socket event
                deleteForm.appendChild(deleteIndexInput);

                var deleteButton = document.createElement('button');
                deleteButton.type = 'submit';
                deleteButton.className = 'icon-button delete';
                deleteButton.title = 'Delete';
                deleteButton.innerHTML = '&#128465;'; // Trash can icon
                deleteForm.appendChild(deleteButton);
                newSubmissionDiv.appendChild(deleteForm);

                // Add copy button functionality
                attachCopyButtonFunctionality(newSubmissionDiv);

                submissionsDiv.insertBefore(newSubmissionDiv, submissionsDiv.firstChild);
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
                socketio.emit('new_message', {'message': message, 'id': len(submissions) -1})
    return render_template_string(HTML_TEMPLATE, submissions=submissions)

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=8800)
