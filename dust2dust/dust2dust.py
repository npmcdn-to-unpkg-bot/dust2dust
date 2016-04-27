from flask import Flask
import pika

app = Flask(__name__)

@app.route('/')
def main():
    return 'automatic dust reporting service'


if __name__ == '__main__':
    app.run(port=21000, debug=True)
