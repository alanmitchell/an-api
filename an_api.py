import time
import pprint
from pathlib import Path
from flask import Flask, request

app = Flask(__name__)

@app.route('/debug_store', methods=['POST', 'GET'])
def store_debug_data():
    """Store POST data into log file.
    """
    #post_data = request.get_data(as_text=True)
    post_data = request.get_json(force=True)
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

@app.route('/lora-store', methods=['POST'])
def store_lora_data():
    """Store POST data into a cumulative LoRaWAN log file, and also into a file that
    holds the last post received.
    """
    post_data = request.get_data(as_text=True)
    if not Path('lora-data/').exists():
        Path('lora-data/').mkdir()

    open('lora-data/lora.txt', 'a').write(f'{post_data}\n')
    open('lora-data/lora-last.txt', 'w').write(f'{post_data}')

    return 'OK'

@app.route('/get-last-lora', methods=['GET'])
def get_last_lora():
    if Path('lora-data/lora-last.txt').exists():
        return open('lora-data/lora-last.txt').read()
    else:
        return ''

@app.route('/lora-debug', methods=['POST'])
def store_lora_debug_data():
    """Store POST data into a cumulative LoRaWAN log file.
    """
    post_data = request.get_data(as_text=True)
    if not Path('lora-data/').exists():
        Path('lora-data/').mkdir()

    open('lora-data/lora-debug.txt', 'a').write(f'{post_data}\n')

    return 'OK'



if __name__ == "__main__":
    app.run(host='0.0.0.0')

