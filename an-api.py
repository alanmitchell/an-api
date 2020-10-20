import time
import pprint
from pathlib import Path
from flask import Flask, request

app = Flask(__name__)

@app.route('/debug_store', methods=['POST'])
def store_debug_data():
    """Store POST data into log file.
    """
    post_data = request.get_json()
    new_data = time.asctime(time.gmtime()) + ' UTC\n' + pprint.pformat(post_data)
    if not Path('data/').exists():
        Path('data/').mkdir()

    try:
        old_data = open('data/debug.txt').read()
        if len(old_data) > 60000:
            old_data = old_data[:30000]   # save 30,000 bytes of the old
    except:
        old_data = ''
    open('data/debug.txt', 'w').write(new_data + '\n\n' + old_data)

    return 'OK'

@app.route('/debug', methods=['GET'])
def show_debug():
    """Retrieves log file of POST data.
    """
    try:
        return '<pre>' + open('data/debug.txt').read() + '</pre>'
    except:
        return "Error occurred or no data."

if __name__ == "__main__":
    app.run(host='0.0.0.0')
