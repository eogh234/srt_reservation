import os
from datetime import datetime
import requests
import discord
import yaml

from main import SRT

from exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
from validation import station_list

login_id = ""
login_psw = ""
dpt_stn = ""
arr_stn = ""
dpt_dt = 0
dpt_tm = ""
num_trains_to_check = 0
want_reserve = 0
webhook_url = ""

hj_author = ""
dh_author = ""
hj_login_id = ""
dh_login_id = ""
hj_login_psw = ""
dh_login_psw = ""
hj_username = ""
dh_username = ""

with open('/Users/Daeho/Projects/srt_reservation/srt_reservation/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
    login_id = _cfg['LOGIN_ID']
    login_psw = _cfg['LOGIN_PASSWORD']
    dpt_stn = _cfg['DEPART_STATION']
    arr_stn = _cfg['ARRIVE_STATION']
    dpt_dt = _cfg['DEPART_DATE']
    dpt_tm = _cfg['DEPART_TIME']
    num_trains_to_check = _cfg['TRAIN_NUMBER']
    want_reserve = _cfg['IS_RESERVE']

    hj_author = _cfg['HJ']['AUTHOR']
    dh_author = _cfg['DH']['AUTHOR']
    hj_login_id = _cfg['HJ']['LOGIN_ID']
    dh_login_id = _cfg['DH']['LOGIN_ID']
    hj_login_psw = _cfg['HJ']['LOGIN_PASSWORD']
    dh_login_psw = _cfg['DH']['LOGIN_PASSWORD']
    hj_username = _cfg['HJ']['USERNAME']
    dh_username = _cfg['DH']['USERNAME']

    webhook_url = _cfg['DISCORD_WEBHOOK_URL']
    token = _cfg['DISCORD_TOKEN']

    intents=discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    srt_channel = client.get_channel(_cfg['SRT_CHANNEL'])
    ktx_channel = client.get_channel(_cfg['KTX_CHANNEL'])

steps = ["wait", "init", "dpt_stn", "arr_stn", "dpt_dt", "dpt_tm", "num_trains_to_check", "want_reserve"]
current_step = "wait"

def send_message(msg):
        """디스코드 메세지 전송"""
        now = datetime.now()
        message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
        requests.post(webhook_url, data=message)
        print(message)

async def set_step(step):
    global current_step
    current_step = step

def check_input(dpt, arr, dt, tm, num):
    if dpt and arr and dt and tm and num > 0:
        return True
    else:
        return False

@client.event
async def on_ready():
    print("discord on_ready called..")
    print(f"USER: {client.user.name}")
    print(f"USER: {client.user.id}")
    send_message("======================================")
    send_message("서버가 시작되었습니다")
    send_message("'예약하기'를 입력해주세요🐻‍❄️")

@client.event
async def on_message(message):
    global current_step

    global login_id
    global login_psw

    global hj_author
    global dh_author
    global hj_login_id
    global dh_login_id
    global hj_login_psw
    global dh_login_psw

    global dpt_stn
    global arr_stn
    global dpt_dt
    global dpt_tm
    global num_trains_to_check
    global want_reserve
    global webhook_url

    print("discord on_message called..")
    if not current_step:
        await set_step("wait")

    if message.content == "예약하기" and current_step == "wait":
        if str(message.author) == hj_author:
            login_id = hj_login_id
            login_psw = hj_login_psw
            print(f"Hello {hj_username}")
            await message.channel.send(f"Hello {hj_username}")
        else:
            login_id = dh_login_id
            login_psw = dh_login_psw
            print(f"Hello {dh_username}")
            await message.channel.send(f"Hello {dh_username}")
        print("🚉출발역을 입력하세요")
        print("현재 가능한 역👇")
        print(f"{station_list}")
        await message.channel.send("🚉출발역을 입력하세요")
        await message.channel.send("현재 가능한 역👇")
        await message.channel.send(f"{station_list}")
        await set_step("init")
    elif (current_step == "init" or current_step == "dpt_stn") and (message.content in station_list):
        if current_step == "init":
            for station in station_list:
                if message.content == station:
                    dpt_stn = station
                    print(f"🚉출발역 입력 완료 {dpt_stn}역")
                    await message.channel.send(f"🚉출발역 입력 완료 {dpt_stn}역")

                    print("🚉도착역을 입력하세요")
                    print("현재 가능한 역👇")
                    print(f"{station_list}")
                    await message.channel.send("🚉도착역을 입력하세요")
                    await message.channel.send("현재 가능한 역👇")
                    await message.channel.send(f"{station_list}")
                    await set_step("dpt_stn")
                    break
        elif current_step == "dpt_stn":
            for station in station_list:
                if message.content == station:
                    arr_stn = station
                    print(f"🚉도착역 입력 완료 {arr_stn}역")
                    await message.channel.send(f"🚉도착역 입력 완료 {arr_stn}역")

                    print("📆조회할 날짜를 입력하세요 ex) 20240101")
                    await message.channel.send("📆조회할 날짜를 입력하세요 ex) 20240101")
                    await set_step("arr_stn")
                    break
    elif (len(message.content) < 9) and (current_step == "arr_stn"):
        try:
            print(message.content)
            print(len(message.content))
            print(f"날짜 숫자 여부: {str(message.content).isnumeric()}")
            datetime.strptime(message.content, '%Y%m%d')
            dpt_dt = message.content
            await set_step("dpt_dt")
            print(f"📆출발 일자 입력 완료 {dpt_dt}")
            await message.channel.send(f"📆출발 일자 입력 완료 {dpt_dt}")

            print("⏰조회할 시간을 입력하세요 (짝수 시간만) ex) 08, 18, 22..")
            await message.channel.send("⏰조회할 시간을 입력하세요 (짝수 시간만) ex) 08, 18, 22..")
        except ValueError:
            raise InvalidDateError("⚠️날짜가 잘못 되었습니다. YYYYMMDD 형식으로 입력해주세요.")
            return False
        
    elif len(message.content) == 2 and current_step == "dpt_dt":
        try:
            print(f"시간 숫자 여부: {str(message.content).isnumeric()}")
            if int(message.content) % 2 == 0:
                dpt_tm = str(message.content)

                print(f"⏰조회 시간 입력 완료 {dpt_tm}")
                await message.channel.send(f"⏰조회 시간 입력 완료 {dpt_tm}")
                await set_step("dpt_tm")

                print("🚅조회할 열차 숫자를 입력하세요 ex) 1, 4, 8, 10..")
                await message.channel.send("🚅조회할 열차 숫자를 입력하세요 ex) 1, 4, 8, 10..")
            else:
                print("⚠️짝수 시간만 입력해주세요 ex) 08, 18, 22..")
                await message.channel.send("⚠️짝수 시간만 입력해주세요 ex) 08, 18, 22..")

        except ValueError:
            raise InvalidTimeFormatError("⚠️시간이 잘못 되었습니다. 짝수 시간으로 입력해주세요. 00, 07, 17, 23")
            return False
        
    elif len(message.content) < 3 and current_step == "dpt_tm":
        if not str(message.content).isnumeric():
            print("⚠️숫자만 입력해주세요 ex) 1, 2, 10..")
            await message.channel.send("⚠️숫자만 입력해주세요 ex) 1, 2, 10..")
        else:
            num_trains_to_check = int(message.content)

            print(f"🚅조회할 열차 수 입력 완료 {num_trains_to_check}")
            await message.channel.send(f"🚅조회할 열차 수 입력 완료 {num_trains_to_check}")
            await set_step("num_trains_to_check")

            print("😙예약 대기 여부를 입력하세요 1: 예약 대기, 2: 예약 대기 안함")
            await message.channel.send("😙예약 대기 여부를 입력하세요 1: 예약 대기, 2: 예약 대기 안함")
    elif len(message.content) < 2 and current_step == "num_trains_to_check":
        if not str(message.content).isnumeric():
            print("⚠️숫자만 입력해주세요 ex) 1 - 예약대기, 2 - 예약대기 안함")
            await message.channel.send("⚠️숫자만 입력해주세요 ex) 1 - 예약대기, 2 - 예약대기 안함")
        else:
            if message.content == "2":
                want_reserve = 0
            else:
                want_reserve = 1
            print(f"😙예약 대기: {want_reserve}")
            await message.channel.send(f"😙예약 대기: {want_reserve}")
            await set_step("want_reserve")
        if check_input(dpt_stn, arr_stn, dpt_dt, dpt_tm, num_trains_to_check):
            await message.channel.send("======SRT 예약을 시작합니다======")
            await message.channel.send("🚅🚃🚃🚃🚃🚃🚃🚃🚃🚃🚃🚃🚃🚃🚃🚃🚃")
            pid = os.fork()

            if pid == 0:
                print(f"Child Process: {os.getpid()}")
                srt = SRT(dpt_stn, arr_stn, dpt_dt, dpt_tm, num_trains_to_check, want_reserve, webhook_url=webhook_url)
                srt.run(login_id, login_psw)
            else:
                print(f"Parrent Process: {os.getpid()}")
                await set_step("wait")
                pass
    elif message.content == "종료하기":
        print("👋프로그램을 종료합니다. 처음부터 진행해주세요")
        await message.channel.send("👋프로그램을 종료합니다. 처음부터 진행해주세요")
        await set_step("wait")
        return False
    else:
        pass

def run():
    client.run(token)

if __name__ == "__main__":
    run()