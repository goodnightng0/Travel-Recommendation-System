from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import time, random
import pandas as pd
import numpy as np
from selenium import webdriver
from urllib.request import urlretrieve

ratings=dict()
count=0
recc_num=7
g_data = pd.read_excel('tour\점수표3.xlsx')
tmap = pd.read_csv('tour\Tmap.csv')
tmap = tmap.dropna(axis=0)
g_data_real = g_data.set_index('지역(시군구)')
g_local = list(g_data['지역(시군구)'].unique())
location_list = random.sample(g_local, recc_num)

def index(request):
    return render(request,'tour/index.html')

@csrf_exempt
def move(request):
    time.sleep(2)
    global location_list, count, ratings
    location=location_list[count]
    return render(request, 'tour/question.html', {'location': location, 'ans':'no'})

@csrf_exempt
def q1(request):
    global location_list, count, ratings, recc_num
    location = location_list[count]
    if request.POST['submit_button'] == '네':
        ans = 'yes'
        return render(request, 'tour/question.html', {'location': location, 'ans': ans})
    elif request.POST['submit_button'] == '아니오':
        ratings[location] = 0
        count += 1
        if count == recc_num:
            return loading(request)
        else:
            location = location_list[count]
            return render(request, 'tour/question.html', {'location': location, 'ans': 'no'})
@csrf_exempt
def q2(request):
    global location_list, count, ratings, recc_num
    location = location_list[count]
    ratings[location] = request.POST['ratings_button']
    count += 1
    if count == recc_num:
        return loading(request)
    else:
        location = location_list[count]
        return render(request, 'tour/question.html', {'location': location, 'ans': 'no'})

def recommendation():
    global g_data, g_data_real, g_local, ratings, location_list
    data=g_data;data_real=g_data_real; local=g_local; travel=location_list
    my_list = list(ratings.values())
    my_score = pd.DataFrame(my_list, index=travel, columns=['점수'])

    total_list = []
    for i in range(len(my_score)):
        if int(my_score.iloc[i, 0]) > 0:
            data_new = data_real[data_real.index == my_score.index[i]]
            data_real = data_real.drop([my_score.index[i]])
            local.remove(my_score.index[i])
            new_list = []
            for j in range(len(data_new.columns)):
                new_list.append(my_score.iloc[i, 0] * data_new.iloc[0, j])
            total_list.append(new_list)

    new_list2 = []
    for i in range(9):
        n = 0
        for local_list in total_list:
            n = n + int(local_list[i])
        n = n / len(total_list)
        new_list2.append(n)
    new_list2 = np.array(new_list2)

    predict = np.dot(new_list2, data_real.values.T)
    predict_new = pd.DataFrame(predict.T, columns=['점수'])
    predict_new.index = local
    my_predict = predict_new.sort_values(by=['점수'], axis=0, ascending=False, inplace=False)

    my_tourist = my_predict.head(3)
    Scene = ['자연경관', '관광명소기타', '폭포/계곡', '유원지', '자연휴양림', '관광단지', '전망대', '저수지', '호수', '동굴', '자연부락', '탐방코스','산과바다', '명산', '해수욕장', '포구', '항구', '섬', '등대', '산장', '방파제']
    Food = ['맛집', '종합시장', '농수축산물시장', '재래시장', '시장기타', '한식', '일식', '중식', '세계요리', '치킨', '분식', '전문음식점', '패스트푸드', '제과점',
            '패밀리레스토랑', '부페']
    Activity = ['액티비티', '골프장', '테마파크', '여행/레저기타', '놀이시설', '스키장', '캠프장', '스케이트장', '레저/스포츠기타', '경마장', '종합위락시설', '카레이싱장',
                '수상해양스포츠', '양궁장', '눈썰매장', '번지점프', '카지노', '경륜장', '승마장', '사격장', '패러글라이딩', '래프팅']
    Healing = ['휴양지', '온천', '공원', '국/도립공원', '목장', '드라이브코스', '농장/농원', '관광농원', '산림욕장', '이색카페', '테마카페', '낚시', '데이트코스',
               '음악카페', '체험농가', '촬영지']
    History = ['역사유적', '절', '문화유적지', '성', '기념비', '고택/생가/민속마을', '전통찻집', '고궁', '탑']
    Culture = ['문화체험', '축제', '박물관/기념관', '자동차극장', '동/식물원', '미술관', '극장', '화랑/전시관', '공연장', '과학관', '수족관', '전시장', '문화원']
    concept = [Scene, Food, Activity, Healing, History, Culture]
    global tmap
    total_themes=[]
    for loc in my_tourist.index:
        theme_name = []
        place = data.loc[data['지역(시군구)'] == loc]
        place = place.drop(['지역(시군구)'], axis=1)
        theme_name.append(place.idxmax(axis=1).values)
        place = place.drop(theme_name[0], axis=1)
        theme_name.append(place.idxmax(axis=1).values)
        place = place.drop(theme_name[1], axis=1)
        theme_name.append(place.idxmax(axis=1).values)
        total_themes.append(theme_name)
    rec_names=[]
    for j in concept:
        for i in my_tourist.index:
            tourist = tmap[(tmap['지역(시군구)'] == i) & (tmap['검색지유형3'].isin(j))]
            try:
                local = tourist['검색지명'].value_counts().index[0]
            except:
                print("error here: ");print(j);print(i)
            rec_names.append(local)
    return my_tourist.index, total_themes, rec_names

@csrf_exempt
def result(request):
    threelocs, theme_names, loc_names=recommendation()
    search_selenium(threelocs,loc_names)
    return render(request, 'tour/result.html', {'first':threelocs[0],'second':threelocs[1],'third':threelocs[2],
            'l1r1':theme_names[0][0][0], 'l1r2':theme_names[0][1][0],'l1r3':theme_names[0][2][0],
            'l2r1':theme_names[1][0][0], 'l2r2':theme_names[1][1][0],'l2r3':theme_names[1][2][0],
            'l3r1':theme_names[2][0][0],'l3r2':theme_names[2][1][0],'l3r3':theme_names[2][2][0],
            'a1': loc_names[0],'a2': loc_names[1],'a3': loc_names[2],'a4': loc_names[3],'a5': loc_names[4],
            'a6': loc_names[5],'a7': loc_names[6],'a8': loc_names[7],'a9': loc_names[8],'a10': loc_names[9],
            'a11': loc_names[10],'a12': loc_names[11],'a13': loc_names[12],'a14': loc_names[13],
            'a15': loc_names[14],'a16': loc_names[15],'a17': loc_names[16],'a18': loc_names[17],})

@csrf_exempt
def loading(request):
    return render(request, 'tour/loading.html')

def search_selenium(threelocs,loc_names):
    all_names=list(threelocs)+loc_names
    browser = webdriver.Chrome(r'C:\Users\yurik\Desktop\chromedriver.exe')
    for i, search_name in enumerate(all_names):
        search_url = "https://www.google.com/search?q=" + str(search_name) + "&hl=ko&tbm=isch"
        browser.get(search_url)

        #browser.implicitly_wait(2)

        image = browser.find_elements_by_tag_name("img.rg_i.Q4LuWd")[1]
        url = image.get_attribute('src')
        name="tour/static/tour/"+str(i)+".png"
        urlretrieve(url, name)
    browser.close()