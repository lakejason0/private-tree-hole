from flask import Flask, render_template, request
import json
app = Flask(__name__)

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template("default.html")

@app.route('/thread/<id>')
@app.route('/thread/<id>.html')
def thread(id):
    return ""

@app.route('/public')
@app.route('/public.html')
def public():
    return ""

@app.route('/login')
@app.route('/login.html')
def logging():
    return ""

@app.route('/api')
def api():
    recv_data = json.loads(request.get_data('data'))

@app.route('/api/thread/', method=['POST'])
def thread():
    recv_data = json.loads(request.get_data('data'))

@app.route('/api/thread/<id>', method=['GET'])
def getThread(id):
    recv_data = json.loads(request.get_data('data'))

if __name__ == '__main__':
    app.run(debug = True)