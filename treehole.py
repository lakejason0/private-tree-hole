from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template("default.html")

@app.route('/thread/<id>')
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

if __name__ == '__main__':
    app.run(debug = True)