import time
import json
import pprint
from pathlib import Path
import pytz
from dateutil.parser import parse
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
    json_file = 'lora-data/lora.json'
    gateway_file = 'lora-data/gateways.tsv'
    values_file = 'lora-data/values.tsv'

    post_data = request.get_data(as_text=True)
    if not Path('lora-data/').exists():
        Path('lora-data/').mkdir()

    open(json_file, 'a').write(f'{post_data}\n')

    try:
        if not Path(gateway_file).exists():
            hdr = 'dev_id\tts\tts_day\tts_hour\tcounter\tgateway\tsnr\trssi\tdata_rate\n'
            with open(gateway_file, 'w') as fout:
                fout.write(hdr)
        if not Path(values_file).exists():
            hdr = 'dev_id\tts\tpayload\n'
            with open(values_file, 'w') as fout:
                fout.write(hdr)
        rec = json.loads(post_data)
        dev_id = rec['dev_id']
        ctr = rec['counter']
        ts_utc = parse(rec['metadata']['time'])
        tz_ak = pytz.timezone('US/Alaska')
        ts = ts_utc.astimezone(tz_ak).replace(tzinfo=None)
        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
        ts_day = ts.strftime('%Y-%m-%d')
        ts_hr = ts.strftime('%Y-%m-%d %H:00')
        data_rate = rec['metadata']['data_rate']
        with open(gateway_file, 'a') as fout:
            for gtw in rec['metadata']['gateways']:
                gtw_id = gtw['gtw_id']
                snr = gtw['snr']
                rssi = gtw['rssi']
                r = f'{dev_id}\t{ts_str}\t{ts_day}\t{ts_hr}\t{ctr}\t{gtw_id}\t{snr}\t{rssi}\t{data_rate}\n'
                fout.write(r)
        with open(values_file, 'a') as fout:
            r = f"{dev_id}\t{ts_str}\t{rec['payload_raw']}\n"
            fout.write(r)
    except:
        pass

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

