import re
import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from datetime import datetime


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


info_status = {
    'work': 'Sending request',
    'done': 'Complete the request'
}


# 在外部定义组件
chat_history_store = dcc.Store(id='chat-history')
user_input_textarea = dcc.Textarea(id='user-input', style={'width': '100%', 'height': '150px'}, placeholder="Please Enter Message...")
send_button = html.Button("Summit", id="send-button", n_clicks=0, className="btn btn-primary mt-2")
loading = dcc.Loading(id='send-loading', children=[html.Div(id='send-info')])
input_div = html.Div([user_input_textarea, send_button, loading], 
                     style={'position': 'fixed', 'bottom': 0, 'left': 0, 'right': 0, 'padding': '10px', 'background': 'white'})
chat_box_div = html.Div(id='chat-box', style={'overflow': 'auto', 'max-height': '70vh', 'padding': '10px'})


# 使用外部定义的组件构建layout
app.layout = html.Div([chat_history_store, chat_box_div, input_div])


def generate_plot_response():
    # 创建散点图数据
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [2, 1, 4, 3, 5]
    })
    fig = px.scatter(df, x="x", y="y")
    plot_response = dcc.Graph(figure=fig)
    return plot_response


@app.callback(
    Output('send-info', 'children', allow_duplicate=True),
    Output('send-button', 'disabled', allow_duplicate=True),
    Input('send-button', 'n_clicks'),
    prevent_initial_call=True,
)
def trigger_request(n_clicks):
    if n_clicks > 0:
        return info_status['work'], True
    return dash.no_update



def format_xml_content(message):
    components = []  # 初始化一个空列表来存放组件
    last_end = 0  # 上一次匹配结束的位置

    # 正则表达式以匹配 XML 声明以及<ABC>...</ABC>
    pattern = re.compile(r'(<\?xml.*?\?>)?\s*(<ABC>.*?</ABC>)', re.DOTALL)
    for match in pattern.finditer(message):
        start = match.start()

        # 添加前一个匹配和当前匹配之间的原始文本
        if start > last_end:
            text_segment = message[last_end:start].strip()  # 移除前后空白
            if text_segment:  # 如果处理后的文本非空
                components.append(html.Pre(text_segment, style={'white-space': 'pre-wrap', 'margin': '0', 'padding': '0'}))

        # 对于 XML 部分
        xml_content = html.Div(
            html.Pre(match.group(0), style={'white-space': 'pre-wrap', 'margin': '0', 'padding': '10px'}),
            style={'background-color': 'rgba(211, 211, 211, 0.2)', 'padding': '2px', 'margin': '0', 'border-radius': '2px'}
        )
        components.append(xml_content)

        last_end = match.end()

    # 添加最后一个匹配后的剩余文本，移除前面的空行
    if last_end < len(message):
        final_text_segment = message[last_end:].strip()  # 同样移除前后空白
        if final_text_segment:  # 如果处理后的文本非空
            components.append(html.Pre(final_text_segment, style={'white-space': 'pre-wrap', 'margin': '0', 'padding': '0'}))
    
    return components



@app.callback(
    Output('chat-box', 'children'),
    Output('user-input', 'value'),
    Output('send-info', 'children'),
    Output('send-button', 'disabled'),
    Input('send-info', 'children'),
    State('user-input', 'value'),
    State('chat-history', 'data'),
)
def update_chat(info, user_input, chat_history):
    if info != info_status['work']:
        return dash.no_update
    
    if user_input is None or user_input == '':
        return '', user_input, 'Error: No Message', False

    time_beg = datetime.now().strftime('%Y-%m-%d %H:%M:%S')    

    if chat_history is None:
        chat_history = []

    # 将用户输入的内容添加到聊天历史中
    chat_history.append({'sender': 'User', 'message': user_input})

    # 简单地反转用户输入作为服务器响应
    server_response = user_input
    chat_history.append({'sender': 'Server', 'message': server_response})

    # 假设根据某些条件服务器决定发送一个散点图
    if "plot" in user_input:
        plot_response = generate_plot_response()
        chat_history.append({'sender': 'Server', 'type': 'plot', 'content': plot_response})
    
    # 将服务器的文字响应添加到聊天历史中
    
    user_input = ''  # 清空输入框
    chat_content = []

    # 遍历聊天历史并按照顺序构建聊天内容
    for msg in chat_history:
        chat_message_components = []  # 初始化一个空列表来存放每条消息的组件
        if msg.get('type') == 'plot':
            # 对于图表类型的消息，直接添加图表组件
            chat_message_components.append(msg['content'])
        else:
            # 对于文本消息，使用format_xml_content处理并保留原始格式
            chat_message_components.extend(format_xml_content(msg['message']))

        # 将消息的发送者和内容组合到一个Div中
        chat_content.append(html.Div([
            html.B(f"{msg['sender']}:", style={'color': '#007BFF' if msg['sender'] == 'User' else '#FF5733', 'font-size': '20px'}),
            *chat_message_components,  # 使用*解包来添加所有组件
        ], style={'margin-bottom': '15px'}))

    time_end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')    
    info_output = f"{info_status['work']} at {time_beg}   &   {info_status['done']} at {time_end}"
    return chat_content, user_input, info_output, False


if __name__ == '__main__':
    app.run_server(debug=True)
