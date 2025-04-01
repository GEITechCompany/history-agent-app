from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return '<h1>Hello, World!</h1>'

if __name__ == '__main__':
    print("Starting simple Flask app on port 8000...")
    print("Visit http://localhost:8000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=8000) 