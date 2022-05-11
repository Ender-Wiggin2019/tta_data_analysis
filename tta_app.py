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
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
from sqlalchemy import create_engine
from streamlit.components.v1 import html

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

        if len(leader_names) > 0 or len(wonder_names) > 0: st.warning('领袖奇迹筛选为测试功能，仅包含玩家手工统计的对局。')
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
        # ori_df_build.configure_selection('single', use_checkbox=True, groupSelectsChildren=True, groupSelectsFiltered=True)
        ori_df_builder = ori_df_build.build()
        AgGrid(
            ori_df, 
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
    st.markdown('还没做')
    
    
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

    with st.expander("💬 Open comments", expanded=True):

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