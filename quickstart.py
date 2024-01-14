""" Quickstart script for InstaPy usage """

# imports
from srt_reservation.main import SRT
from srt_reservation.util import parse_cli_args

import yaml

if __name__ == "__main__":
    cli_args = parse_cli_args()

    login_id = ""
    login_psw = ""
    dpt_stn = ""
    arr_stn = ""
    dpt_dt = ""
    dpt_tm = ""
    num_trains_to_check = 10
    want_reserve = 1

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

        webhook_url = _cfg['DISCORD_WEBHOOK_URL']

    if cli_args.user:
        login_id = cli_args.user
    if cli_args.psw:
        login_psw = cli_args.psw
    if cli_args.dpt:
        dpt_stn = cli_args.dpt
    if cli_args.arr:
        arr_stn = cli_args.arr
    if cli_args.dt:
        dpt_dt = cli_args.dt
    if cli_args.tm:
        dpt_tm = cli_args.tm

    if cli_args.num:
        num_trains_to_check = cli_args.num
    if cli_args.reserve:
        want_reserve = cli_args.reserve

    srt = SRT(dpt_stn, arr_stn, dpt_dt, dpt_tm, num_trains_to_check, want_reserve, webhook_url=webhook_url)
    srt.run(login_id, login_psw)