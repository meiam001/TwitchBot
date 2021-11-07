from flask import Flask, request

app = Flask(__name__)

@app.route("/users", methods=['GET', 'POST'])
def hello_world(name):
    return f"<p>Hello, {name}"

if __name__=='__main__':
    app.run(debug=True)
