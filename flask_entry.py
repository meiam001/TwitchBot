from flask import Flask

app = Flask(__name__)

@app.route("/name/<name>")
def hello_world(name):
    print(name)
    return "<p>Hello, World!</p>"

if __name__=='__main__':
    app.run(debug=True)
