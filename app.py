import sqlite3
import secrets
from hashids import Hashids
from flask import Flask, render_template, request, flash, redirect, url_for


def connect_db():
    connection_variable = sqlite3.connect('database.db')
    connection_variable.row_factory = sqlite3.Row

    # you can have name-based access to columns ie the 
    # database connection will return rows that behave like regular 
    # dictionaries
    return connection_variable

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(20)

hashids = Hashids(min_length=4, salt=app.config['SECRET_KEY'])

@app.route('/', methods=('GET', 'POST'))
def index():
    connection_variable = connect_db()

    if request.method == 'POST':
        url = request.form['url']

        #Checking if empty field is submitted
        if not url:
            flash('The URL is required!')
            return redirect(url_for('index'))

        #Checking if the URL is already in database
        already = connection_variable.execute("SELECT id FROM urls WHERE original_url = ?", (url,)).fetchall()

        if len(already)!=0:
            flash('The URL has already been used!')
            return redirect(url_for('index'))

        url_data = connection_variable.execute('INSERT INTO urls (original_url) VALUES (?)',
                                (url,))
        connection_variable.commit()
        connection_variable.close()

        url_id = url_data.lastrowid
        hashid = hashids.encode(url_id)
        short_url = request.host_url + hashid

        return render_template('index.html', short_url=short_url)

    return render_template('index.html')

@app.route('/<id>')
def url_redirect(id):
    connection_variable = connect_db()

    original_decoded_id = hashids.decode(id)

    #Checking if the Short URL even exists in DB
    if original_decoded_id:
        original_decoded_id = original_decoded_id[0]
        url_data = connection_variable.execute('SELECT original_url, clicks FROM urls'
                                ' WHERE id = (?)', (original_decoded_id,)
                                ).fetchone()
        original_url = url_data['original_url']
        clicks = url_data['clicks']
        
        #Updating the number of clicks for that link
        connection_variable.execute('UPDATE urls SET clicks = ? WHERE id = ?',
                     (clicks+1, original_decoded_id))

        connection_variable.commit()
        connection_variable.close()
        return redirect(original_url)
    else:
        flash('Invalid URL')
        return redirect(url_for('index'))

@app.route('/stats')
def stats():
    connection_variable = connect_db()
    all_urls = connection_variable.execute('SELECT id, created, original_url, clicks FROM urls'
                           ).fetchall()
    connection_variable.close()

    urls = []
    for url in all_urls:
        url = dict(url)
        url['short_url'] = request.host_url + hashids.encode(url['id'])
        urls.append(url)

    return render_template('stats.html', urls=urls)

