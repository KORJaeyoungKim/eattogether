from ast import IsNot
from lib2to3.pgen2 import token
from jinja2 import Undefined
from pymongo import MongoClient

client = MongoClient('mongodb+srv://test:sparta@cluster0.0wupi.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.eattogether

from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

import jwt
import datetime
import hashlib
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    card_list = list(db.cards.find({}, {'_id': False}))

    if token_receive is None:
        status = 0
        user_id = None
        return render_template('index.html', status=status, user_id=user_id, cards=card_list)
    else:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['id']
        return render_template('index.html', status=1, user_id=user_id, cards=card_list)

@app.route('/signup')
def signup():
    return render_template('login.html')

@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'id': id_receive, 'pw': pw_hash}, {'_id': False})

    if result is not None:
        payload = {
            'id': id_receive,
            # 'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        # token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
        #ec2 서버에서 json이 안날아가는 오류 수정하기위해 decode['utf-8] 붙여야함

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

@app.route("/join", methods=["POST"])
def people_join():
    number_receive = request.form['number']
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    check = bool(db.join.find_one({"number": number_receive,'id':payload['id']}))
    card = db.cards.find_one({"index": int(number_receive)})
    if check:
        return jsonify({'msg': '이미 신청하셨습니다.'})
    elif card['leaderId'] == payload['id']:
        return jsonify({'msg': '주최자는 신청할수 없습니다.'})
    else:
        doc = {
            'number': number_receive,
            'id': payload['id']
        }
        current_count = card['count']
        db.cards.update_one({"index": int(number_receive)},{'$set':{'count': current_count+1}})
        db.join.insert_one(doc)
        return jsonify({'msg': '신청 완료!'})


# @app.route("/posts", methods=["get"])
# def render_cards():
#     card_list = list(db.cards.find({}, {'_id': False}))
#     return jsonify({'cards': card_list})


@app.route("/DataSend", methods=["get"])
def view_detail():
    token_receive = request.cookies.get('mytoken')
    index_receice = request.args.get("index_give")
    card_info = db.cards.find_one({'index': int(index_receice)}, {'_id': False})
    guest_count = list(db.join.find({'number':index_receice}, {'_id': False}))
    check = '';

    if token_receive is not None:
        id = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])['id']
        if id == card_info['leaderId']:
            check = 'true'
        else:
            check = 'false'
    else:
        check = 'false'
        
    guest_info = []
    for info in guest_count:
        guest_info.append(db.users.find_one({"id": info['id']},{'_id': False ,'pw': False}))
   
    return jsonify({'cards': card_info, 'guest':guest_info, 'check':check})


@app.route("/posts", methods=["POST"])
def card_post():
    #모임등록시 입력한 정보들을 받아오는 부분
    title_receive = request.form['title_give']
    place_receive = request.form['place_give']
    people_receive = request.form['people_give']
    time_receive = request.form['time_give']

    #모임 등록한 사람의 token값을 가져와서 ID를 꺼내오는 부분
    token_receive = request.cookies.get('mytoken')

    #로그인하지 않은 유저의 글쓰기를 막기위한 if
    if token_receive is not None:
        id = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])['id']

        #각 카드별 index저장을 위한 코드
        cardList_length = len(list(db.cards.find({}, {'_id': False})))
        card_index = cardList_length + 1

        #<--이미지 크롤링 코드 시작 -->
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("--disable-gpu")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
        # driver = webdriver.Chrome('chromedriver', options=options)
        driver = webdriver.Chrome(executable_path='/home/ubuntu/eattogether/chromedriver', options=options)
        #ec2에서 크롬드라이버 경로를 잡지 못해서 절대경로를 사용해서 chromedriver 잡아줘야함
        driver.get("https://www.google.co.kr/imghp?hl=ko&tab=wi&authuser=0&ogbl")
        elem = driver.find_element(By.NAME, "q")  # 구글 검색창 선택
        elem.send_keys(place_receive)  # 검색창에 검색할 내용(name)넣기
        elem.send_keys(Keys.RETURN)  # 검색할 내용을 넣고 enter를 치는것!
        driver.implicitly_wait(2)
        driver.find_element(By.XPATH,
                            '/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div[1]/div[1]/span/div[1]/div[1]/div[1]/a[1]/div[1]/img').click()
        time.sleep(1)
        imgUrl = driver.find_element(By.XPATH,
                                     '/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div/div/div[3]/div[2]/c-wiz/div/div[1]/div[1]/div[3]/div/a/img').get_attribute(
            "src")
        driver.quit()
        #<--이미지 크롤링 코드 끝-->

        obj = {
            'title': title_receive,
            'img': imgUrl,
            'place': place_receive,
            'people': people_receive,
            'time': time_receive,
            'index': card_index,
            'leaderId' : id,
            'count' : 0
        }
        db.cards.insert_one(obj);

        return jsonify({'msg': '로딩 성공!', 'status': 1})
    else:
        return jsonify({'msg': '로그인이 필요한 서비스입니다.', 'status': 0})

   

    

@app.route('/login', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    phone_receiver = request.form['phone_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "id": username_receive,                               # 아이디
        "pw": password_hash,                                  # 비밀번호
        "phone": phone_receiver                            # 프로필 이름 기본값은 아이디

    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/login/check', methods=['POST'])
def check_dup():
    findusername_receive = request.form['username_give']
    exists = bool(db.users.find_one({"id": findusername_receive}))
    return jsonify({'result': 'success', 'exists': exists})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
