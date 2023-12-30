from app import app

if __name__ == '__main__':
    print(__name__)
    app.run(debug=True, port=8080)
