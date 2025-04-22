from flask import Flask
from flask import render_template
from flask import Response, request, jsonify, redirect
import random
import numpy as np

app = Flask(__name__)

# ROUTES

@app.route('/')
def welcome():
   return render_template('welcome.html') 
@app.route('/learn')
def learn():
    return render_template('learn.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

# AJAX FUNCTIONS

@app.route('/example', methods=['GET', 'POST'])
def example():

    json_data = request.get_json()   
    exampleTerm = json_data["example"] 
    return ()

if __name__ == '__main__':
    app.run(debug = True, port=5001)
    


