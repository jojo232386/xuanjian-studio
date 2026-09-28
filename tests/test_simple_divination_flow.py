"""Regression checks for the actual one-click path and shared reading contract."""
import itertools
import json
import threading
import urllib.request
from http.server import HTTPServer
from unittest.mock import patch
import pytest
from backend.server import XuanJianAPIHandler
from scripts.iching import calculate_hexagram, YAOCI_SPECIAL
from xuanjian.divination_reading import enrich_calculation
from xuanjian.export_service import export_divination_markdown

@pytest.fixture
def api():
    server=HTTPServer(('127.0.0.1',0),XuanJianAPIHandler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def post(path,data):
        req=urllib.request.Request(f'http://127.0.0.1:{server.server_port}'+path,
            data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
        with opener.open(req,timeout=3) as response:return json.load(response)
    yield post
    server.shutdown();server.server_close();thread.join()

def test_coins_and_manual_share_populated_reading(api):
    values=[8,8,7,8,8,7]
    flips=[[2,3,3],[2,3,3],[2,2,3],[2,3,3],[2,3,3],[2,2,3]]
    with patch('backend.server.cast_coins',return_value=(values,flips)):
        direct=api('/api/iching/coins',{'topic':'今天抽皮肤'})
    manual=api('/api/iching/calculate',{'lines':values,'topic':'今天抽皮肤'})
    assert direct['layered_interpretation']==manual['layered_interpretation']
    assert all(direct['layered_interpretation'].values())
    assert direct['reading']==manual['reading']
    assert direct['coin_flips']==flips
    assert direct['topic']=='今天抽皮肤'
    assert direct['lines'][0]['yaoci']=='初六：艮其趾，无咎，利永贞。'

def test_single_draw_is_three_coins_not_a_hidden_full_cast(api):
    with patch('backend.server.secrets.randbelow',side_effect=[0,1,1]) as rng:
        r=api('/api/iching/coin',{})
        assert r=={'coins':[2,3,3],'value':8}
        assert rng.call_count==3

def test_no_filler_in_any_of_384_lines():
    seen=set()
    for values in itertools.product((7,8),repeat=6):
        calc=calculate_hexagram(list(values));seen.add(calc['original_hexagram']['number'])
        for l in calc['lines']:
            assert '守正以持' not in l['yaoci']
            assert '尚未收录' not in l['yaoci']
            assert l['yaoci'].startswith(l['yao_name']+'：')
            assert '未逐条' in l['yaoci_status']
    assert len(seen)==64
    assert len([key for key in YAOCI_SPECIAL if 1<=key[1]<=6])==384

def test_topic_changes_context_not_the_cast_or_original_text():
    a=enrich_calculation(calculate_hexagram([8,8,7,8,8,7]),'今天抽皮肤')
    b=enrich_calculation(calculate_hexagram([8,8,7,8,8,7]),'是否换工作')
    assert a['reading']['context']!=b['reading']['context']
    assert a['original_hexagram']==b['original_hexagram']
    assert a['reading']['basis']==b['reading']['basis']

def test_export_keeps_cast_time_and_throw_trace():
    c=enrich_calculation(calculate_hexagram([8,8,7,8,8,7]),'原始问题','guided_three_coins')
    c['coin_flips']=[[2,3,3],[2,3,3],[2,2,3],[2,3,3],[2,3,3],[2,2,3]]
    text=export_divination_markdown({'topic':c['topic'],'calculation':c,'interpretation':c['layered_interpretation']})
    assert c['cast_at'] in text and '原始问题' in text and 'guided_three_coins' in text
    assert '第6次：2 + 2 + 3 = 7' in text
    assert '未逐条独立校订' in text

def test_review_edit_does_not_change_saved_reading(tmp_path):
    from xuanjian.storage import XuanJianStorage
    store=XuanJianStorage(str(tmp_path/'review.db'))
    calc=enrich_calculation(calculate_hexagram([8,8,7,8,8,7]),'原问题','guided_three_coins')
    calc['coin_flips']=[[2,3,3],[2,3,3],[2,2,3],[2,3,3],[2,3,3],[2,2,3]]
    rec=store.create_record({'title':'测试','record_type':'divination','topic':calc['topic'],'calculation_result':calc})
    store.update_review(rec['id'],{'actual_outcome':'后来结果','notes':'另作观察'})
    assert store.get_record(rec['id'])['calculation_result']==calc
    md=store.export_records_as_markdown([rec['id']])
    assert '【艮】' in md and calc['reading']['headline'] in md and '第6次：2 + 2 + 3 = 7' in md

def test_purchase_is_not_automatically_treated_as_a_lottery():
    result=enrich_calculation(calculate_hexagram([8]*6),'购买一件东西前怎样考虑？')
    assert '随机抽取' not in result['reading']['action']
    assert '售后' in result['reading']['action']
    assert '顺势' in result['reading']['headline']
