
from pymongo import MongoClient
client = MongoClient('mongodb+srv://rad572985:497056@cluster0.zzh6w.mongodb.net/?retryWrites=true&w=majority')
db = client.dbsparta

from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


@app.route('/')
def home():
    return render_template('index.html')

@app.route("/posts", methods=["POST"])
def movie_post():
    place_receive = request.form['place_give']

    # headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    # data = requests.get(f'google.com/search?q={url_receive}&source=lnms&tbm=isch&sa=X&ved=2ahUKEwid54CM4vD4AhWEN94KHe4wBe4Q_AUoAnoECAIQBA',headers=headers)
    driver = webdriver.Firefox()
    time.sleep(1)
    driver.get("https://www.google.co.kr/imghp?hl=ko&tab=wi&authuser=0&ogbl")
    elem = driver.find_element(By.NAME,"q") #구글 검색창 선택
    elem.send_keys(place_receive) # 검색창에 검색할 내용(name)넣기
    elem.send_keys(Keys.RETURN) # 검색할 내용을 넣고 enter를 치는것!
    time.sleep(1)
    driver.find_element(By.XPATH,'/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div[1]/div[1]/span/div[1]/div[1]/div[1]/a[1]/div[1]/img').click()            
    time.sleep(1)
    imgUrl = driver.find_element(By.XPATH,
                '/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div/div/div[3]/div[2]/c-wiz/div/div[1]/div[1]/div[3]/div/a/img').get_attribute(
                "src")
    print(imgUrl)

    return jsonify({'msg':'sucess'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)