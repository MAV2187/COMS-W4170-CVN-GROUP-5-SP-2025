from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production

# Ensure data files exist
if not os.path.exists('user_progress.json'):
    with open('user_progress.json', 'w') as f:
        json.dump({}, f)

# Load module data
with open(os.path.join(app.static_folder, 'js', 'modules.json')) as f:
    modules_data = json.load(f)

def calculate_total_score(username):
    with open('user_progress.json', 'r') as f:
        user_progress = json.load(f)
    
    if username not in user_progress or not user_progress[username]['quiz_scores']:
        return 0
    
    quiz_scores = user_progress[username]['quiz_scores']
    total_score = sum(score for score in quiz_scores.values()) / len(quiz_scores)
    return round(total_score, 2)

def save_user_progress(username, module_id, score=None):
    with open('user_progress.json', 'r') as f:
        user_progress = json.load(f)
    
    if username not in user_progress:
        user_progress[username] = {
            'current_module': 1,
            'quiz_scores': {},
            'last_accessed': datetime.now().isoformat()
        }
    
    if module_id <= 15:  # Learning modules
        user_progress[username]['current_module'] = module_id
    elif score is not None:  # Quiz modules
        user_progress[username]['quiz_scores'][str(module_id)] = score
    
    user_progress[username]['last_accessed'] = datetime.now().isoformat()
    
    with open('user_progress.json', 'w') as f:
        json.dump(user_progress, f, indent=4)

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    username = request.form.get('username')
    if not username:
        return redirect(url_for('index'))
    
    session['username'] = username
    save_user_progress(username, 1)
    return redirect(url_for('load_module', module_id=1))

@app.route('/module/<int:module_id>')
def load_module(module_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    
    username = session['username']
    
    if module_id < 1 or module_id > len(modules_data):
        return redirect(url_for('index'))
    
    save_user_progress(username, module_id)
    
    module = modules_data[str(module_id)]
    template = 'module.html' if module_id <= 15 else 'quiz.html'

    with open('user_progress.json', 'r') as f:
        user_progress = json.load(f)

    saved_answers = user_progress.get(username, {}).get('answers', {}).get(str(module_id)) or {}
    print(f"username: {username}")
    print(f"module_id: {module_id}")
    print(f"saved_answers: {saved_answers}")

    return render_template(template,
                         module=module,
                         module_id=module_id,
                         is_quiz=module_id > 15,
                         total_modules=len(modules_data),
                         saved_answers=saved_answers)

@app.route('/submit_quiz/<int:module_id>', methods=['POST'])
def submit_quiz(module_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    
    username = session['username']
    module = modules_data[str(module_id)]
    user_answers = request.form.to_dict()
    
    correct_answers = 0
    for question in module['questions']:
        q_id = question['id']
        user_answer = user_answers.get(q_id, '').strip().lower()
        
        if question.get('type') == 'drag-drop':
            # Check if all correct answers are selected
            user_selected = set(user_answer.split(','))
            correct_set = set(question['correct_answer'])
            if user_selected == correct_set:
                correct_answers += 1
        elif question.get('type') == 'number-input':
            # Check if all input boxes match the correct_answer structure
            is_correct = True
            for correct_input in question['correct_answer']:
                for key, value in correct_input.items():
                    user_input = int(user_answers.get(f"{q_id}_{key}", 0))
                    if user_input != value:
                        is_correct = False
                        break
                if not is_correct:
                    break
            if is_correct:
                correct_answers += 1
        elif question.get('type') == 'matching':
            # Handle matching questions with proper set comparison
            try:
                user_pairs = set(frozenset(pair.split(':')) for pair in user_answer.split(',') if pair)
                correct_pairs = set(frozenset(pair.split(':')) for pair in question['correct_answer'].split(','))
                if user_pairs == correct_pairs:
                    correct_answers += 1
            except:
                # If any error occurs in parsing, count as incorrect
                pass
        else:
            # Handle all other question types
            if user_answer == question['correct_answer'].lower():
                correct_answers += 1
    
    score = round((correct_answers / len(module['questions'])) * 100, 2)
    save_user_progress(username, module_id, score)
    
    if module_id == len(modules_data):
        return redirect(url_for('show_results'))
    else:
        return redirect(url_for('load_module', module_id=module_id+1))

@app.route('/results')
def show_results():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    username = session['username']
    total_score = calculate_total_score(username)

    with open('user_progress.json', 'r') as f:
        user_progress = json.load(f)

    if username in user_progress:
        if 'answers' in user_progress[username]:
            user_progress[username]['answers'] = {}

        # ✅ Save the cleared data back to the file
        with open('user_progress.json', 'w') as f:
            json.dump(user_progress, f, indent=4)

    with open('user_progress.json', 'r') as f:
        user_progress = json.load(f)
        quiz_scores = user_progress.get(username, {}).get('quiz_scores', {})
    
    return render_template('results.html',
                         total_score=total_score,
                         quiz_scores=quiz_scores,
                         total_quizzes=len(modules_data)-15)  # First 15 are learning modules

@app.route('/save_answer', methods=['POST'])
def save_answer():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    username = session['username']
    data = request.get_json()

    question_id = data.get('question_id')
    selected_answer = data.get('selected_answer')
    module_id = data.get('module_id')

    if not question_id or selected_answer is None or module_id is None:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    with open('user_progress.json', 'r') as f:
        user_progress = json.load(f)

    if username not in user_progress:
        user_progress[username] = {
            'current_module': module_id,
            'quiz_scores': {},
            'answers': {},
            'last_accessed': datetime.now().isoformat()
        }

    if 'answers' not in user_progress[username]:
        user_progress[username]['answers'] = {}

    # Save the answer
    user_progress[username]['answers'][str(module_id)] = user_progress[username]['answers'].get(str(module_id), {})
    user_progress[username]['answers'][str(module_id)][question_id] = selected_answer
    user_progress[username]['last_accessed'] = datetime.now().isoformat()

    with open('user_progress.json', 'w') as f:
        json.dump(user_progress, f, indent=4)

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
