import sqlite3
import hashlib

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_usertable():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')
    conn.commit()
    conn.close()

def add_userdata(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, make_hashes(password)))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

def create_portfoliotable():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS user_portfolios(username TEXT, portfolio_name TEXT, tickers TEXT)')
    conn.commit()
    conn.close()

def add_portfolio(username, portfolio_name, tickers):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO user_portfolios(username, portfolio_name, tickers) VALUES (?,?,?)', (username, portfolio_name, tickers))
    conn.commit()
    conn.close()

def get_portfolios(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT portfolio_name, tickers FROM user_portfolios WHERE username =?', (username,))
    data = c.fetchall()
    conn.close()
    return data

def delete_portfolio(username, portfolio_name):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('DELETE FROM user_portfolios WHERE username=? AND portfolio_name=?', (username, portfolio_name))
    conn.commit()
    conn.close()