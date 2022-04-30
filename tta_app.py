import streamlit as st
import numpy as np
import hashlib
# import hydralit_components as hc
import datetime
from datetime import timezone
import pytz
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import altair as alt
import base64
import mysql.connector
import re

st.set_page_config(page_title='贞德的水晶球', page_icon='./assets/favicon.png', initial_sidebar_state='auto', )


# @st.cache(allow_output_mutation=True)
# def get_base64_of_bin_file(bin_file):
#     with open(bin_file, 'rb') as f:
#         data = f.read()
#     return base64.b64encode(data).decode()

# def set_png_as_page_bg(png_file):
#     bin_str = get_base64_of_bin_file(png_file)
#     page_bg_img = '''
#     <style>
#     body {
#     background-image: url("data:image/png;base64,%s");
#     background-size: cover;
#     }
#     </style>
#     ''' % bin_str
    
#     st.markdown(page_bg_img, unsafe_allow_html=True)
#     return

# set_png_as_page_bg('./assets/bg.png')

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">', unsafe_allow_html=True)


def icon(icon_name):
    st.markdown(f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)

@st.experimental_singleton
def init_connection():
    return mysql.connector.connect(**st.secrets["mysql"])

conn = init_connection()


@st.experimental_memo(ttl=600)
def run_query(query):
    conn.reconnect()
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

@st.experimental_memo(ttl=600)
def read_query(query):
    conn.reconnect()
    return pd.read_sql_query(query, con=conn)
# f = open('./count.txt')
# count = f.read()
# f.close()
# f = open('./count.txt', 'w')
# add = str(int(count) + 1)
# f.write(add)
# f.close()
# CSS to inject contained in a string
# hide_dataframe_row_index = """
#             <style>
#             .row_heading.level0 {display:none}
#             .blank {display:none}
#             </style>
#             """
# # Inject CSS with Markdown
# st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)

hide_table_row_index = """
            <style>
            tbody th {display:none}
            .blank {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">', unsafe_allow_html=True)


def icon(icon_name):
    st.markdown(f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)


page = st.sidebar.selectbox("选择类别", ['卡牌查询', '玩家查询', '观战查询', '网站介绍'], index=3)


if page == '玩家查询':
    player_list = list((pd.read_sql_query("SELECT distinct cgeUsername as player from tta_pulse_data;", con=conn))['player'].unique())
    names = st.multiselect('用户名', player_list)
    if len(names) > 0:
        player_games = pd.read_sql_query("SELECT *,'胜' as flag, coalesce(code, '无代码') as code_add from tta_pulse_flat_data where cgeUsername in ({name_list}) union all SELECT *,'负' as flag, coalesce(code, '无代码') as code_add from tta_pulse_flat_data where cgeUsername_2 in ({name_list});".format(name_list=', '.join(["'"+_+"'" for _ in names])), con=conn)
        cross_detect = pd.read_sql_query("select a.code from (SELECT *,isWin as flag from tta_pulse_flat_data where cgeUsername in ({name_list})) as a inner join (SELECT *,isWin_2 as flag from tta_pulse_flat_data where cgeUsername_2 in ({name_list})) as b on a.code = b.code;".format(name_list=', '.join(["'"+_+"'" for _ in names])), con=conn)
        print('1')
        print(cross_detect.shape[0])
        if cross_detect.shape[0] > 0: st.warning('所选择的玩家参与过同一场对局')
        player_games['startDate'] = (pd.to_datetime(player_games['startDate'])).dt.tz_localize(timezone.utc)
        player_games['startDate'] = player_games['startDate'].dt.tz_convert(pytz.timezone('Asia/Shanghai'))
        # player_games['小时'] = (pd.to_datetime(player_games['startDate'])).dt.hour
        player_games['小时'] = player_games['startDate'].dt.hour
        player_time = player_games.groupby(player_games.小时).agg(
            局数=('cgeUsername', 'count')
        ).dropna().sort_index()
        with st.expander('活跃时间'):
            st.bar_chart(player_time)

        code_df_1 = player_games.loc[(pd.isna(player_games['code_add']) == False) & (player_games['position'] == 0),['code_add', 'flag', 'cgeUsername', 'cgeUsername_2','inc_day']]
        code_df_2 = player_games.loc[(pd.isna(player_games['code_add']) == False) & (player_games['position'] == 1),['code_add', 'flag', 'cgeUsername_2', 'cgeUsername', 'inc_day']]
        code_df_2.columns = code_df_1.columns
        code_df = pd.concat( \
                    [code_df_1, code_df_2],
                    axis = 0,
                    ignore_index=True
                    ).sort_values('inc_day', ascending=False).reset_index(drop=True)
        # code_df['isWin'] = np.select(
        #     [
        #         code_df['isWin'] == 1,
        #         code_df['isWin'] == 0,
        #     ],
        #     [
        #         '胜',
        #         '负'
        #     ],
        #     default=''
        # )
        code_df.columns = ['观战代码', '对局情况', '先手玩家', '后手玩家', '对局日期']
        with st.expander('对局记录'):
            st.table(code_df)
        with st.expander('交战情况'):
            st.warning('请确保所选用户名均为同一位玩家')
            win_check = pd.read_sql_query("""
                            select cgeUsername_2 as "对手", sum(flag) as "胜场", count(flag) as "总数", round(sum(flag)/count(flag),2) as "胜率"
                            from
                            (
                                select cgeUsername, cgeUsername_2, 1 as flag from tta_pulse_flat_data where cgeUsername in ({name_list}) union all SELECT cgeUsername_2, cgeUsername, 0 as flag from tta_pulse_flat_data where cgeUsername_2 in ({name_list})
                            ) as a group by cgeUsername_2 order by 总数 desc;
                        """.format(name_list=', '.join(["'"+_+"'" for _ in names])), con=conn)
            
            st.table(win_check.style.format(
                    {'胜场': '{:.0f}', '总数': '{:.0f}', '胜率': '{:.0%}'}))


if page == '观战查询':
    # c1, c2 = st.columns([3,1])
    local_css("./assets/style.css")
    remote_css('https://fonts.googleapis.com/icon?family=Material+Icons')
    ori_df = read_query("select *, case when position=0 then '先手' else '后手' end as pos from tta_pulse_flat_data order by inc_day desc")
    # text = st.text_area('快速查询 (输入所需关键字，以空格或者换行符分割)')
    # text_list = (text.replace('\n', ' ')).split(' ')
    # if '' in text_list: text_list.remove('')
    # print(text_list)
    sql1 = """
    select name_cn as name, name_cn, age from tta_card_main where type = 'leader'
    order by age, name_cn
    """
    # sql1 = """
    # select * from (select a.别名 as name, b.name_cn, b.age from tta_card_alias as a
    # left join
    # (select * from tta_card_main) as b
    # on a.主名 = b.name_cn
    # where b.type = 'leader') as a
    # union
    # select name_cn, name_cn, age from tta_card_main where type = 'leader'
    # order by age, name_cn
    # """
    leader_df = pd.read_sql_query(sql1, con=conn)
    leader_list = list(leader_df['name'].unique())
    leader_names = st.multiselect('领袖名称', leader_list)
    leader_actual_names = list(leader_df.loc[leader_df['name'].isin(leader_names),'name_cn'].unique())
    if len(leader_names) > 0:
        leader_code = read_query('select distinct code from tta_pulse_leader_detail where leader_name in ({leader})'.format(leader=', '.join(["'"+_+"'" for _ in leader_actual_names])))
        ori_df = ori_df.merge(leader_code, on='code', how='inner', suffixes=['', '_drop'])
        
    # sql2 = """
    # select * from (select a.别名 as name, b.name_cn, b.age from tta_card_alias as a
    # left join
    # (select * from tta_card_main) as b
    # on a.主名 = b.name_cn
    # where b.type = 'wonder') as a
    # union
    # select name_cn, name_cn, age from tta_card_main where type = 'wonder'
    # order by age, name_cn
    # """
    sql2 = """
    select name_cn as name, name_cn, age from tta_card_main where type = 'wonder'
    order by age, name_cn
    """
    wonder_df = pd.read_sql_query(sql2, con=conn)
    wonder_list = list(wonder_df['name'].unique())    
    wonder_names = st.multiselect('奇迹名称', wonder_list)
    wonder_actual_names = list(wonder_df.loc[wonder_df['name'].isin(wonder_names),'name_cn'].unique())
    if len(wonder_names) > 0:
        wonder_code = read_query('select distinct code from tta_pulse_wonder_detail where wonder_name in ({wonder})'.format(wonder=', '.join(["'"+_+"'" for _ in wonder_actual_names])))
        ori_df = ori_df.merge(wonder_code, on='code', how='inner', suffixes=['', '_drop'])

    if len(leader_names) > 0 or len(wonder_names) > 0: st.warning('领袖奇迹筛选为测试功能，仅包含玩家手工统计的对局。')

    with st.expander('日期筛选'):
        start_date = st.date_input('输入起始日期', datetime.date(2021, 1, 1))
        end_date = st.date_input('输入终止日期', datetime.date.today())
    
        
   
    button_clicked = st.button("OK")
    player_list = list((pd.read_sql_query("SELECT * from tta_pulse_player;", con=conn))['player'].unique())
    names = st.multiselect('用户名', player_list)
    ori_df = ori_df.loc[:,['code', 'cgeUsername', 'cgeUsername_2', 'pos', 'inc_day']]
    
    # ori_df_group = ori_df \
    # .groupby(['cn', 'name']) \
    # .agg(
    # position=('sum_position', 'sum'),
    # playerScore=('sum_playerScore', 'sum'),
    # generations=('sum_generations', 'sum'),
    # total=('total', 'sum')
    # ori_df.columns = ['观战代码', '胜方', '败方', '获胜顺位', '对局日期']
    st.dataframe(ori_df)
#         # @st.cache
#         def getPlayersCard(name_list):
#             df = pd.read_csv('./playersCardRank.csv')
#             res = df.loc[df['player'].isin(name_list)]
#             res_group = res \
#                 .groupby(['cn', 'name']) \
#                 .agg(
#                 position=('sum_position', 'sum'),
#                 playerScore=('sum_playerScore', 'sum'),
#                 generations=('sum_generations', 'sum'),
#                 total=('total', 'sum')
#             ) \
#                 .dropna()
#             res_group['position'] = res_group['position'] / res_group['total']
#             res_group['playerScore'] = res_group['playerScore'] / res_group['total']
#             res_group['generations'] = res_group['generations'] / res_group['total']
#             res_group = res_group.sort_values(['total', 'position'], ascending=[False, True]).reset_index()
#             res_group.columns = ['卡牌中文', '卡牌英文', '位次', '得分', '时代', '打出次数']

#             return res_group.drop('卡牌英文', axis=1).head(20).round(2)


#         # @st.cache
#         def getPlayerNumPlayerResult(df, name_list, player_num=4):
#             """
#             主键: game_id, player
#             """
#             # df = df.loc[(df['players'] == player_num) & (df['player'].isin(name_list))].reset_index(drop=True)
#             df = df.loc[(df['players'] == player_num)].reset_index(drop=True)
#             for i in range(1, player_num + 1):
#                 player_idx = 'player' + str(i)
#                 # print(df[player_idx].head())
#                 # player_df_pre = df[player_idx].apply(lambda x:eval(x))
#                 # print(player_idx)
#                 # player_df = pd.json_normalize(player_df_pre).reset_index(drop=True)
#                 player_df = pd.json_normalize(df[player_idx].apply(lambda x: eval(x))).reset_index(drop=True)
#                 if i == 1:
#                     res = pd.concat([df, player_df.reindex(df.index)], axis=1)
#                 else:
#                     mid = pd.concat([df, player_df.reindex(df.index)], axis=1)
#                     res = pd.concat([res, mid], axis=0, ignore_index=True)
#                     # print((mid.loc[pd.isna(mid['player']) == False]).shape[0])
#                 # df = pd.concat([df, pd.json_normalize(df[player_idx])],axis=1)
#             res.drop(['player' + str(i) for i in range(1, 7)], axis=1, inplace=True)
#             res['count'] = 1
#             res = res[res['player'].isin(name_list)].reset_index(drop=True)

#             print(res.columns)
#             return res


#         player_df = getPlayerNumPlayerResult(player_ori, names, playerNum)
#         player_df_group = player_df.groupby('count').agg(
#             平均顺位=('position', 'mean'),
#             平均分数=('playerScore', 'mean'),
#             平均时代=('generations', 'mean'),
#             总数=('count', 'sum')
#         ).dropna().sort_values('平均顺位').reset_index(drop=True)

#         # TODO 时间序列，全局和按天数聚合的结果
#         player_df['小时'] = (pd.to_datetime(player_df['createtime'])).dt.hour
#         player_time = player_df.groupby(player_df.小时).agg(
#             局数=('count', 'sum')
#         ).dropna().sort_index()
#         st.markdown('### 对局统计')

#         st.table((player_df_group.assign(用户名=name) \
#                   .set_index('用户名')) \
#                  .style.format({'平均顺位': '{:.2f}', '平均分数': '{:.3f}', '平均时代': '{:.3f}'}))

#         playersCardRank = getPlayersCard(names)
#         with st.expander('你最喜欢的卡牌'):

#             st.table(playersCardRank.style.format({'位次': '{:.2f}', '得分': '{:.4f}', '时代': '{:.2f}'}))


#         # 根据玩家的game_id join, 取位次高于该玩家的用户，按名称聚合
#         @st.cache
#         def getPlayersPlayWith(df, name_list, player_num=4):
#             """
#             主键: game_id, player
#             """
#             # df = df.loc[(df['players'] == player_num) & (df['player'].isin(name_list))].reset_index(drop=True)
#             df = df.loc[(df['players'] == player_num)].reset_index(drop=True)
#             for i in range(1, player_num + 1):
#                 player_idx = 'player' + str(i)
#                 # print(df[player_idx].head())
#                 # player_df_pre = df[player_idx].apply(lambda x:eval(x))
#                 # print(player_idx)
#                 # player_df = pd.json_normalize(player_df_pre).reset_index(drop=True)
#                 player_df = pd.json_normalize(df[player_idx].apply(lambda x: eval(x))).reset_index(drop=True)
#                 if i == 1:
#                     res = pd.concat([df, player_df.reindex(df.index)], axis=1)
#                 else:
#                     mid = pd.concat([df, player_df.reindex(df.index)], axis=1)
#                     res = pd.concat([res, mid], axis=0, ignore_index=True)
#                     # print((mid.loc[pd.isna(mid['player']) == False]).shape[0])
#                 # df = pd.concat([df, pd.json_normalize(df[player_idx])],axis=1)
#             res.drop(['player' + str(i) for i in range(1, 7)], axis=1, inplace=True)
#             res['count'] = 1

#             res_player = res[res['player'].isin(name_list)].reset_index(drop=True)
#             res_other = res[~(res['player'].isin(name_list))].reset_index(drop=True)
#             res_final = res_other.merge(res_player, on='game_id', how='inner', suffixes=['', '_drop'],
#                                         indicator=True).query('position.notna()', engine="python")
#             res_final.loc[res_final['position'] > res_final['position_drop'], 'win'] = 1
#             res_final.loc[res_final['position'] <= res_final['position_drop'], 'win'] = 0
#             res_final_group = res_final.groupby('player').agg(
#                 总共遇到次数=('win', 'count'),
#                 被你击败=('win', 'sum')
#             ).dropna().sort_values('总共遇到次数', ascending=False)
#             res_final_group['被你击败'] = res_final_group['被你击败'].astype(int)
#             return res_final_group


#         with st.expander('你最喜欢的公司'):
#             try:
#                 fav_corps = corp_df.loc[corp_df['player'].isin(names)]
#                 fav_corps_group = fav_corps.groupby(['cn']).agg(
#                     平均顺位=('position', 'mean'),
#                     平均分数=('playerScore', 'mean'),
#                     平均时代=('generations', 'mean'),
#                     总数=('count', 'count')
#                 ).dropna().sort_values('总数', ascending=False).head(15)
#                 st.table(fav_corps_group.style.format(
#                     {'平均顺位': '{:.1f}', '平均分数': '{:.2f}', '平均时代': '{:.1f}', '总数': '{:.0f}'}))
#             except:
#                 st.warning('该选项组合没有数据')
#         with st.expander('和你游戏的玩家'):
#             try:
#                 player_with_you = getPlayersPlayWith(player_ori, names, playerNum)
#                 st.table(player_with_you.head(15))
#             except:
#                 st.warning('该选项组合没有数据')
#         with st.expander('活跃时间'):
#             st.bar_chart(player_time)

#         challenge = pd.read_csv('./成就.csv')
#         all_challenge = (pd.unique(challenge['title'])).shape[0]
#         challenge = challenge.loc[challenge['player'].isin(names)].sort_values('index')
#         challenge.drop_duplicates(subset=['title'], keep='first', inplace=True)
#         challenge = challenge.loc[:, ['title', 'reason', 'createtime']].set_index('title')
#         challenge.columns = ['成就', '达成时间']
#         your_challenge = challenge.shape[0]
#         with st.expander('火星成就 (%d/%d)' % (your_challenge, all_challenge)):
#             if challenge.shape[0] == 0:
#                 challenge = challenge.append({'成就': '达成成就数量 (%d/%d)' % (your_challenge, all_challenge), '达成时间': '直到此刻'},
#                                              ignore_index=True)
#                 challenge.rename(index={0: '火星打工人'}, inplace=True)
#             st.table(challenge)

# elif page == '卡牌数据':
#     local_css("style.css")
#     remote_css('https://fonts.googleapis.com/icon?family=Material+Icons')

#     icon("search")
#     card_key = st.text_input("")
#     card_clicked = st.button("OK")
#     allCardsRank = pd.read_csv('./allCardsRank.csv')
#     allCardsRank.columns = ['卡牌中文', '卡牌英文', '位次', '得分', '时代', '打出次数']
#     if card_key == '':
#         allCardsRank = allCardsRank
#     else:
#         allCardsRank = allCardsRank[(allCardsRank['卡牌英文'].str.contains('(?i)' + card_key)) | (
#             allCardsRank['卡牌中文'].str.contains('(?i)' + card_key))]
#     st.dataframe(allCardsRank.style.format({'位次': '{:.2f}', '得分': '{:.1f}', '时代': '{:.1f}', '打出次数': '{:.0f}'}))

#     st.text('注：卡牌的数据统计根据打出该卡牌的玩家最终位次和得分计算。')

# elif page == '网站介绍':
#     st.markdown("""
#     ## 数据来源
#     本网站数据来自[殖民火星国服](http://jaing.me/)的后台数据库，有超过14000局游戏的记录，本数据站主要针对2P和4P进行统计。
    
#     ## FAQ
    
#     * **Q: 登陆账号是哪个账号?**
    
#         A: 火星游戏网站的注册账号。
    
#     * **Q: 我的常用游戏名和登陆账号不符怎么办?**
    
#         A: 联系*QQ: 209926937*, 将个人常用id发给我即可。
    
#     * **Q: 我想看更多的数据, 或者有优化界面的建议, 如何提出呢?**
    
#         A: 联系上方的QQ号就行了捏。
        
#     ## 当前点击量
#     目前已被访问%s次。
#     """ % (add)
#                 )
