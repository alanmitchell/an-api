import time
import json
import pprint
from pathlib import Path
import pytz
from dateutil.parser import parse
from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/debug_store', methods=['POST', 'GET'])
def store_debug_data():
    """Store POST and GET data into log file.
    """

    # Get Request data
    if request.method == 'POST':
        request_data = request.get_json(force=True)
    elif request.method == 'GET':
        request_data = request.args

    # Block this repetitive poster
    if '256_uptime' in str(request_data):
        return 'OK'

    new_data = time.asctime(time.gmtime()) + ' UTC\n' + pprint.pformat(request_data)

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

@app.route('/store-oauth-code', methods=['GET'])
def store_oauth_code():
    """Store OAuth code into file. Used as a callback endpoint in the
    OAuth process.
    """

    # Get Request data
    request_data = request.args

    if not Path('data/').exists():
        Path('data/').mkdir()

    open('data/oauth.txt', 'w').write(request_data['code'])

    return 'OK'

@app.route('/get-oauth-code', methods=['GET'])
def get_oauth_code():
    """Return OAuth code from file
    """
    return open('data/oauth.txt', 'r').read()


@app.route('/lora-store', methods=['POST'])
def store_lora_data():
    """Store POST data into a cumulative LoRaWAN log file, and also into a file that
    holds the last post received.
    """
    gateway_file = 'lora-data/gateways.tsv'
    values_file = 'lora-data/values.tsv'

    post_data = request.get_data(as_text=True)
    if not Path('lora-data/').exists():
        Path('lora-data/').mkdir()

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
        gtw_recs = []        # holds gateway records

        if 'correlation_ids' in rec:
            # Things V3 message
            dev_id = rec['end_device_ids']['device_id']
            ctr = rec['uplink_message']['f_cnt']
            ts_utc = parse(rec['received_at'])
            dr = rec['uplink_message']['settings']['data_rate']['lora']
            data_rate = f"SF{dr['spreading_factor']}BW{dr['bandwidth']/1000}"
            payload = rec['uplink_message']['frm_payload']

            # add to list of gateway records
            for gtw in rec['uplink_message']['rx_metadata']:
                r = {}
                r['gtw_id'] = gtw['gateway_ids']['gateway_id']
                r['snr'] = gtw['snr']
                r['rssi'] = gtw['rssi']
                gtw_recs.append(r)

        else:
            # Things V2 message
            dev_id = rec['dev_id']
            ctr = rec['counter']
            ts_utc = parse(rec['metadata']['time'])
            data_rate = rec['metadata']['data_rate']
            payload = rec['payload_raw']
            
            # add to list of gateway records
            for gtw in rec['metadata']['gateways']:
                r = {}
                r['gtw_id'] = gtw['gtw_id']
                r['snr'] = gtw['snr']
                r['rssi'] = gtw['rssi']
                gtw_recs.append(r)

        # make some more time fields
        tz_ak = pytz.timezone('US/Alaska')
        ts = ts_utc.astimezone(tz_ak).replace(tzinfo=None)
        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
        ts_day = ts.strftime('%Y-%m-%d')
        ts_hr = ts.strftime('%Y-%m-%d %H:00')

        with open(gateway_file, 'a') as fout:
            for gtw in gtw_recs:
                r = f"{dev_id}\t{ts_str}\t{ts_day}\t{ts_hr}\t{ctr}\t{gtw['gtw_id']}\t{gtw['snr']}\t{gtw['rssi']}\t{data_rate}\n"
                fout.write(r)

        with open(values_file, 'a') as fout:
            r = f"{dev_id}\t{ts_str}\t{payload}\n"
            fout.write(r)

    except:
        pass

    return 'OK'

@app.route('/lora-debug', methods=['POST'])
def store_lora_debug_data():
    """Store POST data into a cumulative LoRaWAN log file.
    """
    post_data = request.get_data(as_text=True)
    if not Path('lora-data/').exists():
        Path('lora-data/').mkdir()

    open('lora-data/lora-debug.txt', 'a').write(f'{post_data}\n')

    return 'OK'

@app.route('/readingdb/reading/store-things/', methods=['POST'])
def relay_bmon():
    data = request.data
    store_key = request.headers.get('store-key')

    # Prepare headers for the relayed request
    headers = {
        'store-key': store_key
    }    
    response = requests.post(
        'https://bms.ahfc.us/readingdb/reading/store-things/', 
        data=data,
        headers=headers
        )
    return response.content, response.status_code    


if __name__ == "__main__":
    app.run(host='0.0.0.0')
    # To test: curl -H "Content-Type: application/json" --data @test.json http://0.0.0.0:5000/lora-store
    # where test.json has a JSON LoRaWAN record.
