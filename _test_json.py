import json
import time

while(True):
    with open('./guide_info.json', mode='r') as f:
        guide_info_json = json.load(f)
        guide_degree = guide_info_json.get('degree', 360)
        if guide_degree != 360:
            print('guide_degree = ' + str(guide_degree))
    time.sleep(0.1)
