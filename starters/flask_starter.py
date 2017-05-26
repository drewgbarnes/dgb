from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)


@app.route('/')
def show_all():
    total = list(range(10))
    return render_template('list.html', total=total)

@app.route('/search')
def show_search():
    query = request.args.get('query', '').split()
    total = list(range(query))

    return render_template('list.html', total=total)

if __name__ == '__main__':
    app.debug = True
    app.run()
