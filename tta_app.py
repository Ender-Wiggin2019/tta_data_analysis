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
import plotly.graph_objs as go
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
from sqlalchemy import create_engine
from streamlit.components.v1 import html
from bokeh.plotting import figure
st.set_page_config(page_title='贞德的水晶球', page_icon='./assets/favicon.png', initial_sidebar_state='auto', )

baidu_statistics = """
<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?d5b74d509d95af6e641d6f3fbd51d734";
  var s = document.getElementsByTagName("script")[0]; 
  s.parentNode.insertBefore(hm, s);
})();
</script>
"""

html(baidu_statistics)

# f = open('./count.txt')
# count = f.read()
# f.close()
# f = open('./count.txt', 'w')
# add = str(int(count) + 1)
# f.write(add)
# f.close()
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

def space(num_lines=1):
    """Adds empty lines to the Streamlit app."""
    for _ in range(num_lines):
        st.write("")

@st.cache
def convert_df(df):
     # IMPORTANT: Cache the conversion to prevent computation on every rerun
     return df.to_csv().encode('utf-8')
 
@st.experimental_singleton
def init_connection():
    return mysql.connector.connect(**st.secrets["mysql"])

@st.experimental_singleton
def init_engine(host, database, user, password):
    return create_engine("mysql+mysqlconnector://{user}:{pw}@{host}/{db}"
				.format(host=host, db=database, user=user, pw=password))

conn = init_connection()
engine = init_engine(st.secrets["mysql"]['host'], st.secrets["mysql"]['database'], st.secrets["mysql"]['user'], st.secrets["mysql"]['password'])

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

@st.experimental_memo(ttl=600)
def read_cache_query(query):
    conn.reconnect()
    return pd.read_sql_query(query, con=conn)


@st.experimental_memo(ttl=600)
def write_query(df, table_name):
    return df.to_sql(table_name, con=engine, if_exists='append', index=False)

@st.experimental_memo(ttl=600)
def rewrite_query(df, table_name):
    return df.to_sql(table_name, con=engine, if_exists='replace', index=False)
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


page = st.sidebar.selectbox("选择类别", ['玩家查询', '观战查询', '卡牌查询', '提交对局', '网站介绍'], index=4)


if page == '玩家查询':
    player_list = list((pd.read_sql_query("SELECT distinct cgeUsername as player from tta_pulse_data;", con=conn))['player'].unique())
    names = st.multiselect('用户名', player_list)
    if len(names) > 0:
        player_games = pd.read_sql_query("SELECT *,'胜' as flag, coalesce(code, '无代码') as code_add from tta_pulse_flat_data where cgeUsername in ({name_list}) union all SELECT *,'负' as flag, coalesce(code, '无代码') as code_add from tta_pulse_flat_data where cgeUsername_2 in ({name_list});".format(name_list=', '.join(["'"+_+"'" for _ in names])), con=conn)
        cross_detect = pd.read_sql_query("select a.code from (SELECT *,isWin as flag from tta_pulse_flat_data where cgeUsername in ({name_list})) as a inner join (SELECT *,isWin_2 as flag from tta_pulse_flat_data where cgeUsername_2 in ({name_list})) as b on a.code = b.code;".format(name_list=', '.join(["'"+_+"'" for _ in names])), con=conn)
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
            code_df_build = GridOptionsBuilder.from_dataframe(code_df)
            code_df_build.configure_selection('single')
            code_df_build.configure_pagination()
            # ori_df_build.configure_selection('single', use_checkbox=True, groupSelectsChildren=True, groupSelectsFiltered=True)
            ori_df_builder = code_df_build.build()
            AgGrid(
                code_df, 
                width='100%',
                allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
                fit_columns_on_grid_load=True,
                gridOptions=ori_df_builder,
                theme='streamlit'
                )
                # st.
        with st.expander('交战情况'):
            st.warning('请确保所选用户名均为同一位玩家')
            win_check = pd.read_sql_query("""
                            select cgeUsername_2 as "对手", sum(flag) as "胜场", count(flag) as "总数", round(sum(flag)/count(flag),2) as "胜率"
                            from
                            (
                                select cgeUsername, cgeUsername_2, 1 as flag from tta_pulse_flat_data where cgeUsername in ({name_list}) union all SELECT cgeUsername_2, cgeUsername, 0 as flag from tta_pulse_flat_data where cgeUsername_2 in ({name_list})
                            ) as a group by cgeUsername_2 order by 总数 desc;
                        """.format(name_list=', '.join(["'"+_+"'" for _ in names])), con=conn)
            win_check_build = GridOptionsBuilder.from_dataframe(win_check)
            win_check_build.configure_selection('single')
            win_check_build.configure_column("胜率", header_name='己方胜率', type=["numericColumn","numberColumnFilter"], valueFormatter="(data.胜率*100).toFixed(1)+'%'", aggFunc='sum')
            win_check_build.configure_pagination()
            # ori_df_build.configure_selection('single', use_checkbox=True, groupSelectsChildren=True, groupSelectsFiltered=True)
            ori_df_builder = win_check_build.build()
            AgGrid(
                win_check, 
                width='100%',
                allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
                fit_columns_on_grid_load=True,
                gridOptions=ori_df_builder,
                theme='streamlit'
                )
            # st.table(win_check.style.format(
            #         {'胜场': '{:.0f}', '总数': '{:.0f}', '胜率': '{:.0%}'}))


if page == '观战查询':
    # c1, c2 = st.columns([3,1])
    local_css("./assets/style.css")
    remote_css('https://fonts.googleapis.com/icon?family=Material+Icons')
    with st.spinner(text="正在获取对局数据..."):
        ori_df = read_query("select *, case when position=0 then '先手' else '后手' end as pos, coalesce(code, '无代码') as code_add from tta_pulse_flat_data order by inc_day desc")
    
    ori_df['startDate'] = (pd.to_datetime(ori_df['startDate'])).dt.date
    # text = st.text_area('快速查询 (输入所需关键字，以空格或者换行符分割)')
    # text_list = (text.replace('\n', ' ')).split(' ')
    # if '' in text_list: text_list.remove('')
    # print(text_list)

        
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


    with st.expander('日期筛选'):
        start_date = st.date_input('输入开始日期', datetime.date(2022, 3, 4))
        end_date = st.date_input('输入结束日期', datetime.date.today())
        
        ori_df = ori_df.loc[(ori_df['startDate'] >= start_date) & (ori_df['startDate'] <= end_date)]
        
   
    player_list = list((pd.read_sql_query("SELECT distinct cgeUsername as player from tta_pulse_data;", con=conn))['player'].unique())
    with st.expander('玩家筛选'):
        inner_names = st.multiselect('选择玩家的用户名', player_list)
        if len(inner_names) >= 2:
            ori_df = ori_df[(ori_df['cgeUsername'].isin(inner_names)) & (ori_df['cgeUsername_2'].isin(inner_names))]
        elif len(inner_names) == 1:
            ori_df = ori_df[(ori_df['cgeUsername'].isin(inner_names)) | (ori_df['cgeUsername_2'].isin(inner_names))]
            st.warning('只选择一名玩家，将会展示所有仅包含该玩家的对局。')
        else: st.warning('该选项将会选择所有对局中仅包含所选用户的对局.')
 
 
    with st.expander('领袖奇迹筛选'):
        st.warning('启用此功能后，将仅剩下玩家手工统计的对局。')
        sql1 = """
        select name_cn as name, name_cn, age from tta_card_main where type = 'leader'
        order by age, name_cn
        """
        sql2 = """
        select name_cn as name, name_cn, age from tta_card_main where type = 'wonder'
        order by age, name_cn
        """
        leader_df = pd.read_sql_query(sql1, con=conn)
        leader_list = list(leader_df['name'].unique())
        leader_names = st.multiselect('领袖名称', leader_list)
        leader_actual_names = list(leader_df.loc[leader_df['name'].isin(leader_names),'name_cn'].unique())
        if len(leader_names) > 0:
            leader_code = read_query('select distinct code from tta_pulse_leader_detail where leader_name in ({leader})'.format(leader=', '.join(["'"+_+"'" for _ in leader_actual_names])))
            ori_df = ori_df.merge(leader_code, on='code', how='inner', suffixes=['', '_drop'])
        wonder_df = pd.read_sql_query(sql2, con=conn)
        wonder_list = list(wonder_df['name'].unique())    
        wonder_names = st.multiselect('奇迹名称', wonder_list)
        wonder_actual_names = list(wonder_df.loc[wonder_df['name'].isin(wonder_names),'name_cn'].unique())
        if len(wonder_names) > 0:
            wonder_code = read_query('select distinct code from tta_pulse_wonder_detail where wonder_name in ({wonder})'.format(wonder=', '.join(["'"+_+"'" for _ in wonder_actual_names])))
            ori_df = ori_df.merge(wonder_code, on='code', how='inner', suffixes=['', '_drop'])

        if len(leader_names) > 0 or len(wonder_names) > 0: st.warning('领袖奇迹筛选仅包含玩家手工统计的对局，请谨慎使用这个筛选条件。')
        button_clicked = st.button("OK")
                   
    lose_df = ori_df.loc[:,['cgeUsername_2', 'isWin_2']]
    lose_df.columns = ['cgeUsername', 'isWin']
    player_win_rate_df = pd.concat([ori_df.loc[:,['cgeUsername', 'isWin']], lose_df], axis=0)
    # st.text(str(player_win_rate_df.columns))
    player_win_rate_df_group = player_win_rate_df \
        .groupby('cgeUsername') \
        .agg(
            win_times=('isWin', 'sum'),
            total_times=('isWin', 'count')
        ).reset_index()
    player_win_rate_df_group['win_rate'] = player_win_rate_df_group['win_times'] / player_win_rate_df_group['total_times']
    player_win_rate_df_group = player_win_rate_df_group.sort_values(['win_times', 'win_rate'], ascending=[False, False])
    player_win_rate_df_group.columns = ['用户名', '胜场', '局数', '胜率']

    ori_df = ori_df.loc[:,['code_add', 'cgeUsername', 'cgeUsername_2', 'pos', 'inc_day']]
    
    ori_df.columns = ['观战代码', '胜方', '败方', '胜方顺位', '游戏日期']
    
    # ori_df_group = ori_df \
    # .groupby(['cn', 'name']) \
    # .agg(
    # position=('sum_position', 'sum'),
    # playerScore=('sum_playerScore', 'sum'),
    # generations=('sum_generations', 'sum'),
    # total=('total', 'sum')
    # ori_df.columns = ['观战代码', '胜方', '败方', '获胜顺位', '对局日期']
    if ori_df.shape[0] == 0:
        st.error('所选筛选组合没有数据')
    else:
        ori_df_build = GridOptionsBuilder.from_dataframe(ori_df)
        ori_df_build.configure_selection('single')
        ori_df_build.configure_pagination()
        # ori_df_build.configure_selection('single', use_checkbox=True, groupSelectsChildren=True, groupSelectsFiltered=True)
        ori_df_builder = ori_df_build.build()
        AgGrid(
            ori_df.head(100), 
            width='100%',
            allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
            fit_columns_on_grid_load=True,
            gridOptions=ori_df_builder,
            theme='streamlit'
            )
        with st.expander('玩家胜率'):
            mini_num = st.slider('选择入选所需要的最小局数',1,100, value=3)
            mini_rate = st.slider('选择入选所需要的最低胜率',0,100, value=10)
            player_win_rate_df_group = player_win_rate_df_group.loc[player_win_rate_df_group['胜率'] >= mini_rate/100] 
            # player_win_rate_df_group['胜率'] = player_win_rate_df_group['胜率'].mul(100).round(1).astype(str).add(' %')
            player_win_rate_df_group = player_win_rate_df_group.loc[player_win_rate_df_group['局数'] >= mini_num].sort_values(['胜率', '局数'], ascending=[False, False]).reset_index(drop=True)
            # st.dataframe(player_win_rate_df_group.style.format(
            #     {'胜场': '{:.0f}', '局数': '{:.0f}', '胜率': '{:.0%}'}))
            # player_win_rate_df_group = player_win_rate_df_group.style.format({'胜场': '{:.0f}', '局数': '{:.0f}', '胜率': '{:.0%}'})
 #builds a gridOptions dictionary using a GridOptionsBuilder instance.
            player_win_rate_df_group_build = GridOptionsBuilder.from_dataframe(player_win_rate_df_group)
            player_win_rate_df_group_build.configure_pagination(True, False, 30)
            player_win_rate_df_group_build.configure_column("胜率", header_name='胜率', type=["numericColumn","numberColumnFilter"], valueFormatter="(data.胜率*100).toFixed(1)+'%'", aggFunc='sum')
            player_win_rate_df_group_builder = player_win_rate_df_group_build.build()
            AgGrid(
                player_win_rate_df_group, 
                width=None,
                allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
                theme='streamlit',
                fit_columns_on_grid_load=True,
                gridOptions=player_win_rate_df_group_builder
                )
    
    
    
elif page == '卡牌查询':
    st.info('温馨提示：手机用户请横屏以获得更好的体验。')
    c1, c2, c3 = st.columns([1,6,2])
    w_logic = c1.selectbox('胜方判断',['>=', '>', '<','<='])
    w_rate = c2.slider('胜方胜率',0,100,0,step=5)
    w_game = c3.number_input('胜方局数', 1,1000,1,step=10)
    l_logic = c1.selectbox('败方判断',['>=', '>', '<','<='])
    l_rate = c2.slider('败方胜率',0,100,0,step=5)
    l_game = c3.number_input('败方局数', 1,1000,1,step=10)
    sql = """
        with t1 as
                (select a.leader_no, a.leader_name, a.is_win
                from tta_pulse_leader_detail as a
                        inner join
                    (select code
                        from tta_pulse_code_detail as a
                                inner join tta_pulse_win_rate as b
                                            on a.player_win = b.player and b.win_rate {w_logic} {w_rate}/100 and b.total >= {w_game}
                                inner join tta_pulse_win_rate as c
                                            on a.player_lose = c.player and c.win_rate {l_logic} {l_rate}/100 and c.total >= {l_game}) as b on a.code = b.code
                                where leader_name <> '无') -- TODO 针对体退情况暂时删去
        select leader_name                                             as "领袖名称",
            sum(is_win)                                             as "胜场",
            count(is_win)                                           as "总数",
            sum(is_win) / count(is_win)                             as "胜率",
            concat('Age ', case
                                when leader_no = 'a' then 'A'
                                when leader_no = '1' then 'I'
                                when leader_no = '2' then 'II'
                                when leader_no = '3' then 'III' end) as "时代"
        from t1
        group by leader_no, leader_name
        order by FIELD(leader_no, 'a', '1', '2', '3'), sum(is_win) / count(is_win) desc;
    """.format(w_logic=w_logic, w_rate=w_rate, l_logic=l_logic, l_rate=l_rate, w_game=w_game, l_game=l_game)
    
    sql2 = """
        with t1 as
                (select a.wonder_no, a.wonder_name, a.is_win
                from tta_pulse_wonder_detail as a
                        inner join
                    (select code
                        from tta_pulse_code_detail as a
                                inner join tta_pulse_win_rate as b
                                            on a.player_win = b.player and b.win_rate {w_logic} {w_rate}/100 and b.total >= {w_game}
                                inner join tta_pulse_win_rate as c
                                            on a.player_lose = c.player and c.win_rate {l_logic} {l_rate}/100 and c.total >= {l_game}) as b on a.code = b.code
                                )
        select a.wonder_name         as "奇迹名称",
            a.win_num             as "胜场",
            a.total               as "总数",
            a.win_rate            as "胜率",
            concat('Age ', b.age) as "时代"
        from (select wonder_name,
                    sum(is_win)                 as win_num,
                    count(is_win)               as total,
                    sum(is_win) / count(is_win) as win_rate,
                    avg(wonder_no)              as wonder_no
            from t1
            group by wonder_name) as a
                left join tta_card_main as b
                        on a.wonder_name = b.name_cn
        order by b.age, win_rate desc
    """.format(w_logic=w_logic, w_rate=w_rate, l_logic=l_logic, l_rate=l_rate, w_game=w_game, l_game=l_game)
    with st.expander('所有领袖胜率'):
        leader_df = read_query(sql)
        leader_df_build = GridOptionsBuilder.from_dataframe(leader_df)
        leader_df_build.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
        leader_df_build.configure_pagination(True, False, 12)
        leader_df_build.configure_column("胜率", header_name='胜率', type=["numericColumn","numberColumnFilter"], valueFormatter="(data.胜率*100).toFixed(1)+'%'", aggFunc='sum')
        leader_df_builder = leader_df_build.build()
        # jscode = JsCode("""
        #     function(params) {
        #         if (params.data.时代 === 'Age A') {
        #             return {
        #                 'color': 'black',
        #                 'backgroundColor': 'red'
        #             }
        #         }
        #     };
        #     """)
        # leader_df_builder['getRowStyle'] = jscode
        AgGrid(
            leader_df, 
            height=410,
            width=None,
            allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
            theme='streamlit',
            fit_columns_on_grid_load=True,
            gridOptions=leader_df_builder
            )

    with st.expander('所有奇迹胜率'):
        wonder_df = read_query(sql2)
        wonder_df_build = GridOptionsBuilder.from_dataframe(wonder_df)
        wonder_df_build.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
        wonder_df_build.configure_pagination(True, False, 16)
        wonder_df_build.configure_column("胜率", header_name='胜率', type=["numericColumn","numberColumnFilter"], valueFormatter="(data.胜率*100).toFixed(1)+'%'", aggFunc='sum')
        wonder_df_builder = wonder_df_build.build()
        AgGrid(
            wonder_df, 
            width=None,
            allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
            theme='streamlit',
            fit_columns_on_grid_load=True,
            gridOptions=wonder_df_builder
            )

    with st.expander('单一领袖分析'):
        sql1 = """
        select name_cn as name, name_cn, age from tta_card_main where type = 'leader'
        order by age, name_cn
        """
        leader_df = pd.read_sql_query(sql1, con=conn)
        leader_list = list(leader_df['name'].unique())
        leader_name = st.selectbox('领袖选择', leader_list)
        sql = """
        
            select win_range as "胜率区间", win_rate as "该领袖胜率", win_rate / win_range as "该领袖胜率/胜率区间", total as "总数"
            from (select round(b.win_rate, 1)        as win_range,
                        count(is_win)               as total,
                        sum(is_win)                 as win_time,
                        sum(is_win) / count(is_win) as win_rate
                from (select * from tta_pulse_leader_detail where leader_name = '{leader_name}') as a
                        inner join (select * from tta_pulse_win_rate where win_rate >= 0.2 and win_rate <= 0.9) as b
                                    on a.player = b.player
                group by round(b.win_rate, 1)
                order by round(b.win_rate, 1)) as a
        """.format(leader_name=leader_name)
        win_rate_by_leader_df = (pd.read_sql_query(sql, con=conn))
        track1 = go.Bar(x=win_rate_by_leader_df['胜率区间'], y=win_rate_by_leader_df['总数'],name='总数', marker=dict(color='#869ed7'))
        track2 = go.Scatter(x=win_rate_by_leader_df['胜率区间'], y=win_rate_by_leader_df['该领袖胜率'],name='该领袖胜率', xaxis='x', yaxis='y2', line=dict(color='#324162'))
        track3 = go.Scatter(x=win_rate_by_leader_df['胜率区间'], y=win_rate_by_leader_df['该领袖胜率/胜率区间'],name='该领袖胜率/胜率区间', xaxis='x', yaxis='y2', line=dict(color='#da9ce4'))
        data = [track1, track2,track3]
        layout = go.Layout(title='领袖胜率分布(不受上方胜率筛选影响)', \
            xaxis=dict(title="胜率区间"), \
            yaxis=dict(title="总对局数"), \
            yaxis2=dict(title="该领袖胜率", overlaying='y', side='right'))
        fig = go.Figure(data=data, layout=layout)
        
        # fig = px.line(win_rate_by_leader_df, x="胜率区间", y="该领袖胜率", title='领袖胜率分布')
        st.plotly_chart(fig, use_container_width=True)
        
        sql3="""
            select a.*, total, 总数 / total as "选取率"
            from (
                    with t1 as
                            (select a.leader_no, a.leader_name, a.is_win, substr(inc_day, 1, 6) as inc_day
                            from (select * from tta_pulse_leader_detail where leader_name = '{leader_name}') as a
                                        inner join
                                                        (select code
                        from tta_pulse_code_detail as a
                                inner join tta_pulse_win_rate as b
                                            on a.player_win = b.player and b.win_rate {w_logic} {w_rate}/100 and b.total >= {w_game}
                                inner join tta_pulse_win_rate as c
                                            on a.player_lose = c.player and c.win_rate {l_logic} {l_rate}/100 and c.total >= {l_game}) as b on a.code = b.code
                                inner join
                                    tta_pulse_flat_data as d on a.code = d.code)

                    select inc_day                                                 as "月份",
                            leader_name                                             as "领袖名称",
                            sum(is_win)                                             as "胜场",
                            count(is_win)                                           as "总数",
                            sum(is_win) / count(is_win)                             as "该领袖胜率",
                            concat('Age ', case
                                            when leader_no = 'a' then 'A'
                                            when leader_no = '1' then 'I'
                                            when leader_no = '2' then 'II'
                                            when leader_no = '3' then 'III' end) as "时代"
                    from t1
                    group by leader_no, leader_name, inc_day
                    order by FIELD(leader_no, 'a', '1', '2', '3'), leader_name, inc_day, sum(is_win) / count(is_win) desc)
                    as a
                    left join
                (select substr(inc_day, 1, 6) as inc_day, count(*) as total
                from tta_pulse_code_detail as a
                        inner join
                    tta_pulse_flat_data as b
                    on a.code = b.code
                group by substr(inc_day, 1, 6)) as b
                on a.月份 = b.inc_day
        """.format(leader_name=leader_name, w_logic=w_logic, w_rate=w_rate, l_logic=l_logic, l_rate=l_rate, w_game=w_game, l_game=l_game)
        date_by_leader_df = (pd.read_sql_query(sql3, con=conn))
        # date_track1 = go.Bar(x=date_by_leader_df['月份'], y=date_by_leader_df['总数'],name='总数', marker=dict(color='#869ed7'))
        date_track2 = go.Scatter(x=date_by_leader_df['月份'], y=date_by_leader_df['该领袖胜率'],name='该领袖胜率', line=dict(color='#324162'))
        date_track3 = go.Scatter(x=date_by_leader_df['月份'], y=date_by_leader_df['选取率'],name='选取率', xaxis='x', yaxis='y2', line=dict(color='#da9ce4'))
        date_data = [date_track2, date_track3]
        date_layout = go.Layout(title='领袖时间序列(受上方胜率筛选影响)', \
            xaxis=dict(title="月份"), \
            yaxis=dict(title="该领袖胜率"), \
            yaxis2=dict(title="选取率", overlaying='y', side='right'))
        date_fig = go.Figure(data=date_data, layout=date_layout)
        st.plotly_chart(date_fig, use_container_width=True)
        
    with st.expander('单一奇迹分析'):
        sql2 = """
        select name_cn as name, name_cn, age from tta_card_main where type = 'wonder'
        order by age, name_cn
        """
        wonder_df = pd.read_sql_query(sql2, con=conn)
        wonder_list = list(wonder_df['name'].unique())
        wonder_name = st.selectbox('奇迹选择', wonder_list)
        sql = """
        
            select win_range as "胜率区间", win_rate as "该奇迹胜率", win_rate / win_range as "该奇迹胜率/胜率区间", total as "总数"
            from (select round(b.win_rate, 1)        as win_range,
                        count(is_win)               as total,
                        sum(is_win)                 as win_time,
                        sum(is_win) / count(is_win) as win_rate
                from (select * from tta_pulse_wonder_detail where wonder_name = '{wonder_name}') as a
                        inner join (select * from tta_pulse_win_rate where win_rate >= 0.2 and win_rate <= 0.9) as b
                                    on a.player = b.player
                group by round(b.win_rate, 1)
                order by round(b.win_rate, 1)) as a
        """.format(wonder_name=wonder_name)
        win_rate_by_leader_df = (pd.read_sql_query(sql, con=conn))
        track1 = go.Bar(x=win_rate_by_leader_df['胜率区间'], y=win_rate_by_leader_df['总数'],name='总数', marker=dict(color='#869ed7'))
        track2 = go.Scatter(x=win_rate_by_leader_df['胜率区间'], y=win_rate_by_leader_df['该奇迹胜率'],name='该奇迹胜率', xaxis='x', yaxis='y2', line=dict(color='#324162'))
        track3 = go.Scatter(x=win_rate_by_leader_df['胜率区间'], y=win_rate_by_leader_df['该奇迹胜率/胜率区间'],name='该奇迹胜率/胜率区间', xaxis='x', yaxis='y2', line=dict(color='#da9ce4'))
        data = [track1, track2,track3]
        layout = go.Layout(title='奇迹胜率分布(不受上方胜率筛选影响)', \
            xaxis=dict(title="胜率区间"), \
            yaxis=dict(title="总对局数"), \
            yaxis2=dict(title="该奇迹胜率", overlaying='y', side='right'))
        fig = go.Figure(data=data, layout=layout)
        
        # fig = px.line(win_rate_by_leader_df, x="胜率区间", y="该领袖胜率", title='领袖胜率分布')
        st.plotly_chart(fig, use_container_width=True)
        
        sql3="""
            select a.*, total, 总数 / total as "选取率"
            from (
                    with t1 as
                            (select a.wonder_no, a.wonder_name, a.is_win, substr(inc_day, 1, 6) as inc_day
                            from (select * from tta_pulse_wonder_detail where wonder_name = '{wonder_name}') as a
                                        inner join
                                                        (select code
                        from tta_pulse_code_detail as a
                                inner join tta_pulse_win_rate as b
                                            on a.player_win = b.player and b.win_rate {w_logic} {w_rate}/100 and b.total >= {w_game}
                                inner join tta_pulse_win_rate as c
                                            on a.player_lose = c.player and c.win_rate {l_logic} {l_rate}/100 and c.total >= {l_game}) as b on a.code = b.code
                                inner join
                                    tta_pulse_flat_data as d on a.code = d.code)

                    select inc_day                                                 as "月份",
                            wonder_name                                             as "奇迹名称",
                            sum(is_win)                                             as "胜场",
                            count(is_win)                                           as "总数",
                            sum(is_win) / count(is_win)                             as "该奇迹胜率"
                    from t1
                    group by wonder_name, inc_day
                    order by wonder_name, inc_day, sum(is_win) / count(is_win) desc)
                    as a
                    left join
                (select substr(inc_day, 1, 6) as inc_day, count(*) as total
                from tta_pulse_code_detail as a
                        inner join
                    tta_pulse_flat_data as b
                    on a.code = b.code
                group by substr(inc_day, 1, 6)) as b
                on a.月份 = b.inc_day
        """.format(wonder_name=wonder_name, w_logic=w_logic, w_rate=w_rate, l_logic=l_logic, l_rate=l_rate, w_game=w_game, l_game=l_game)
        date_by_leader_df = (pd.read_sql_query(sql3, con=conn))
        # date_track1 = go.Bar(x=date_by_leader_df['月份'], y=date_by_leader_df['总数'],name='总数', marker=dict(color='#869ed7'))
        date_track2 = go.Scatter(x=date_by_leader_df['月份'], y=date_by_leader_df['该奇迹胜率'],name='该奇迹胜率', line=dict(color='#324162'))
        date_track3 = go.Scatter(x=date_by_leader_df['月份'], y=date_by_leader_df['选取率'],name='选取率', xaxis='x', yaxis='y2', line=dict(color='#da9ce4'))
        date_data = [date_track2, date_track3]
        date_layout = go.Layout(title='奇迹时间序列(受上方胜率筛选影响)', \
            xaxis=dict(title="月份"), \
            yaxis=dict(title="该奇迹胜率"), \
            yaxis2=dict(title="选取率", overlaying='y', side='right'))
        date_fig = go.Figure(data=date_data, layout=date_layout)
        st.plotly_chart(date_fig, use_container_width=True)
    
    with st.expander('组合分析'):
        sql2 = """
        select name_cn as name, name_cn, age from tta_card_main
        order by age,field(type,'领袖','奇迹'),name_cn
        """
        card_df = pd.read_sql_query(sql2, con=conn)
        card_list = list(card_df['name'].unique())
        c1, c2 = st.columns([1,1])
        combo1 = c1.multiselect('选择己方卡牌（组合）',card_list)
        combo2 = c2.multiselect('选择对方卡牌（组合）',card_list)
        where1, where2, where3, where4 = '', '', '', ''
        if len(combo1) >= 1:
            where1 = combo1[0]
            if len(combo1) >= 2:
                where2 = """
                    inner join
                    (select * from t1 where card_name = '{}') as b
                    on a.code = b.code and a.player = b.player
                """.format(combo1[1])
            else:
                where2 = ''
        if len(combo2) >= 1:
            where3 = """
                inner join
                (select * from t1 where card_name = '{}') as c
                on a.code = c.code and a.player <> c.player
            """.format(combo2[0])
            if len(combo2) >= 2:
                where4 = """
                    inner join
                    (select * from t1 where card_name = '{}') as d
                    on a.code = d.code and a.player <> d.player
                """.format(combo2[1])
            else:
                where4 = ''
        else:
            where3, where4 = '', ''
        if len(combo1) > 2 or len(combo2) > 2:
            st.warning('目前只支持两张卡牌的组合！')
        sql = """
            with t1 as (select code, player, leader_name as card_name, is_win
                        from tta_pulse_leader_detail
                        union all
                        select code, player, wonder_name as card_name, is_win
                        from tta_pulse_wonder_detail)
            select sum(is_win) as win_time, count(is_win) as total, sum(is_win) / count(is_win) as win_rate
            from (
                    select a.*
                    from (select *
                        from t1
                        where card_name = '{}') as a
                            {}
                            {}
                            {}
                ) as a
        """.format(where1, where2, where3, where4)
        find_win_rate = st.button('查询胜率')
        if find_win_rate:
            if len(combo1) < 1:
                st.error('至少选择一张己方卡牌')
            else:
                win_result = read_query(sql)
                if win_result.iloc[0,1] == 0: st.warning('无数据')
                else: st.success('所选组合胜率为'+str(round(win_result.iloc[0,2]*100, 2))+'%, '+'总局数为'+str(win_result.iloc[0,1]))
            
    st.markdown('还没做完，欢迎到[评论区](http://42.192.86.165:8501/)提建议')
elif page == '提交对局':
    with st.form("game_submit"):
        st.write("请按照相应规则提交对局")
        
        player_list = list((pd.read_sql_query("SELECT distinct cgeUsername as player from tta_pulse_data;", con=conn))['player'].unique())
        is_valid = True
        code = st.text_input('请输入对局代码', max_chars=8)
        if len(code) != 0 and len(code) != 8:
            st.warning('代码必须是8位字符')
            is_valid = False
        elif len(code) == 0:
            is_valid = False   
        first_player = st.multiselect('先手玩家', player_list)
        second_player = st.multiselect('后手玩家', player_list)
        if first_player == second_player and len(first_player) > 0:
            st.error('玩家名称必须不同')
            is_valid = False
        
        if len(first_player) == 0 or len(second_player) == 0:
            is_valid = False
        elif len(first_player) != 1 or len(second_player) != 1:
            is_valid = False
            st.error('没有选择正确数量的玩家')
        win_player = st.selectbox('选择获胜方', ['先手', '后手'])
        
        sql1 = """
        select name_cn as name, name_cn, age from tta_card_main where type = 'leader'
        order by age, name_cn
        """
        sql2 = """
        select name_cn as name, name_cn, age from tta_card_main where type = 'wonder'
        order by age, name_cn
        """
        leader_df = pd.read_sql_query(sql1, con=conn)
        leader_list = list(leader_df['name'].unique())
        wonder_df = pd.read_sql_query(sql2, con=conn)
        wonder_list = list(wonder_df['name'].unique())    
        first_leader_names = st.multiselect('先手领袖', leader_list)
        first_wonder_names = st.multiselect('先手奇迹', wonder_list)
        second_leader_names = st.multiselect('后手领袖', leader_list)
        second_wonder_names = st.multiselect('后手奇迹', wonder_list)
        
        src = st.selectbox('选择对局来源', ['Pulse', '官方锦标赛', '日常对局'])
        if len(src) == 0:
            is_valid = False
        # Every form must have a submit button.
        submitted = st.form_submit_button("提交")
        if submitted and is_valid == True:
            final_list = [code, first_player[0], second_player[0], win_player]
            for i in range(4):
                if i < len(first_leader_names):
                    final_list.append(first_leader_names[i])
                else:
                    final_list.append('无')
                
            for i in range(4):
                if i < len(second_leader_names):
                    final_list.append(second_leader_names[i])
                else:
                    final_list.append('无')

            for i in range(8):
                if i < len(first_wonder_names):
                    final_list.append(first_wonder_names[i])
                else:
                    final_list.append('无')

            for i in range(8):
                if i < len(second_wonder_names):
                    final_list.append(second_wonder_names[i])
                else:
                    final_list.append('无')
            final_list.append(src)
            final_list.append(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            final_str = ''
            for i in final_list:
                if i != '无':
                    final_str += i
                    final_str += ' '
            st.info(final_str)
            final_header = ['code', 'first_player', 'second_player', 'win_pos', 'w_l_1', 'w_l_2', 'w_l_3', 'w_l_4', 'l_l_1', 'l_l_2', 'l_l_3', 'l_l_4', 'w_w_1', 'w_w_2', 'w_w_3', 'w_w_4', 'w_w_5', 'w_w_6', 'w_w_7', 'w_w_8', 'l_w_1', 'l_w_2', 'l_w_3', 'l_w_4', 'l_w_5', 'l_w_6', 'l_w_7', 'l_w_8', 'src', 'create_time']
            df = pd.DataFrame([final_list], columns=final_header)
            rewrite_query(df, 'tta_game_result')
            # st.table(df)
            st.success("提交成功")
        elif submitted and is_valid == False:
            st.error("填写有误，请检查")
    
    
elif page == '网站介绍':
    st.image('./assets/joan.png')
    st.markdown("""
   
    *时间旅行者贞德发现自己不但可以看到未来的事件，还可以...*
    
    *看到过去发生的所有对局！*
    &nbsp;
    
    &nbsp;
    
    &nbsp;
    
    本项目由国内历史巨轮爱好者创建，主要通过[历史巨轮天梯平台](https://ttapulse.com/)获取数据，玩家可以查看个人胜率、领袖奇迹胜率以及自己所感兴趣的对局。
    目前属于开发测试阶段，建议使用电脑访问，手机访问可能存在样式问题。如果有想法和建议欢迎提出。
    
    """)

    with st.expander("💬 Open comments", expanded=False):

    # # Show comments

        st.write("**Comments:**")
        COMMENT_TEMPLATE_MD = """{} - {}
        
        > {}"""
        comment_df = read_query("select * from tta_app_comments order by create_time desc limit 20")
        if comment_df.shape[0] == 0: st.text('NO DATA')
        for i, v in comment_df.iterrows():
            st.markdown(COMMENT_TEMPLATE_MD.format(v['name'], v['create_time'], v['content']))

            is_last = i == comment_df.shape[0]
            is_new = "just_posted" in st.session_state and is_last
            if is_new:
                st.success("☝️ Your comment was successfully posted.")

        space(2)

        # Insert comment

        st.write("**提交你的评论:**")
        form = st.form("评论")
        name = form.text_input("你的昵称")
        comment = form.text_area("评论")
        submit = form.form_submit_button("提交评论")

        if submit:
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_comment = pd.DataFrame([{"name": name, "create_time": date, "content": comment}])
            write_query(new_comment, 'tta_app_comments')
            if "just_posted" not in st.session_state:
                st.session_state["just_posted"] = True
            st.experimental_rerun()