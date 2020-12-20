#!/usr/bin/env python3
from pathlib import Path
import json
import pytz
from dateutil.parser import parse

for lin in open('lora-data/lora.txt'):
    if not Path('lora-data/gateways.tsv').exists():
        hdr = 'dev_id\tts\tts_day\tts_hour\tcounter\tgateway\tsnr\trssi\n'
        with open('lora-data/gateways.tsv', 'w') as fout:
            fout.write(hdr)
    rec = json.loads(lin)
    dev_id = rec['dev_id']
    ctr = rec['counter']
    ts_utc = parse(rec['metadata']['time'])
    tz_ak = pytz.timezone('US/Alaska')
    ts = ts_utc.astimezone(tz_ak).replace(tzinfo=None)
    ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
    ts_day = ts.strftime('%Y-%m-%d')
    ts_hr = ts.strftime('%Y-%m-%d %H:00')
    for gtw in rec['metadata']['gateways']:
        gtw_id = gtw['gtw_id']
        snr = gtw['snr']
        rssi = gtw['rssi']
        r = f'{dev_id}\t{ts_str}\t{ts_day}\t{ts_hr}\t{ctr}\t{gtw_id}\t{snr}\t{rssi}\n'
        with open('lora-data/gateways.tsv', 'a') as fout:
            fout.write(r)
