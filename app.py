import pandas as pd  # pip install pandas openpyxl
import plotly.express as px  # pip install plotly-express
import streamlit as st  # pip install streamlit
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
import database as db

# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="Sales Dashboard", page_icon=":bar_chart:", layout="wide")

# --- USER AUTHENTICATION  ---
def recupera_credenciais() -> None:
    """Recupera os dados do banco de dados"""

    users = db.fetch_all_users() # le todos os registro do banco

    usernames = [user["key"] for user in users] # recupera o username em um lista
    names = [user["name"] for user in users] # recupera o nome em um lista
    hashed_passwords = [user["password"] for user in users] # recupera o  hashed password em um lista

    # iniciliza e popula o dicionário usado como prametro streamlit_authenticator
    credentials = {"usernames": {}} 
    for un, name, pw in zip(usernames, names, hashed_passwords):
        user_dict = {"name": name, "password": pw}
        credentials["usernames"].update({un: user_dict})
    return credentials

def handle_click_register():
    """Callback funtion para o botão registre-se"""
    st.session_state['togle_login_register'] = "Register"

def handle_click_jaregistrado():
    """Callback funtion para o botão já registrado"""
    st.session_state['togle_login_register'] = "Login"

credentials = recupera_credenciais()

if 'togle_login_register' not in st.session_state:
    st.session_state['togle_login_register'] = "Login"

authenticator = stauth.Authenticate(
        credentials=credentials, cookie_name="sales_dashboard", key="abcdef", cookie_expiry_days=0
    )

# Polula o formulário de login do streamlit_authenticator
if st.session_state['togle_login_register'] == "Login": 
    buff_left_login, col_login, buff_rigth_login = st.columns([3,3,3])
    with col_login:
        st.markdown("""
            <style>
                div.stButton {
                    text-align: center;
                }
            </style>
            """, unsafe_allow_html=True
        )
        name, authentication_status, username = authenticator.login("Login", "main")

        if st.session_state['authentication_status'] == False:
            st.error("Username/password is incorrect")

        #if st.session_state['authentication_status'] == None:
            #st.warning("Please enter your username and password")


        registro = st.button("Registre-se", on_click=handle_click_register)
        
        # caso o login tenha sucesso reseta a variável de estado que popula o formulário de login e registro
        if st.session_state['authentication_status']:
            st.session_state['togle_login_register'] = None
            st.experimental_rerun()
        
# Popula o formulário de registro escondendo o de login
if st.session_state['togle_login_register'] == "Register":
    buff_left_register, col_register, buff_rigth_register = st.columns([2,3,2])
    with col_register:
        st.markdown("""
            <style>
                div.stButton {
                    text-align: center;
                }
            </style>
            """, unsafe_allow_html=True
        )
        try:
            if authenticator.register_user('Register user', preauthorization=False):
                #popula o banco de dados com o usuário registrado
                new_user = list(authenticator.credentials['usernames'].keys())[-1]
                new_name = authenticator.credentials['usernames'][new_user]['name']
                new_password = authenticator.credentials['usernames'][new_user]['password']
                db.insert_user(username=new_user, name=new_name, password=new_password)
                st.success('User registered successfully')
    
        except Exception as e:
            st.error(e)
     
        ja_registrado = st.button("Já sou Registrado", on_click=handle_click_jaregistrado)

if st.session_state['authentication_status']:

    # ---- READ EXCEL ----
    @st.cache_data
    def get_data_from_excel():
        df = pd.read_excel(
            io="supermarkt_sales.xlsx",
            engine="openpyxl",
            sheet_name="Sales",
            skiprows=3,
            usecols="B:R",
            nrows=1000,
        )
        # Add 'hour' column to dataframe
        df["hour"] = pd.to_datetime(df["Time"], format="%H:%M:%S").dt.hour
        return df

    df = get_data_from_excel()

    # ---- SIDEBAR ----
    authenticator.logout("Logout", "sidebar")

    if not st.session_state['authentication_status']:
        st.session_state['togle_login_register'] = "Login"
        st.experimental_rerun()
        

    st.sidebar.title(f"Welcome {st.session_state['name']}")
    st.sidebar.header("Please Filter Here:")
    city = st.sidebar.multiselect(
        "Select the City:", options=df["City"].unique(), default=df["City"].unique()
    )

    customer_type = st.sidebar.multiselect(
        "Select the Customer Type:",
        options=df["Customer_type"].unique(),
        default=df["Customer_type"].unique(),
    )

    gender = st.sidebar.multiselect(
        "Select the Gender:",
        options=df["Gender"].unique(),
        default=df["Gender"].unique(),
    )

    df_selection = df.query(
        "City == @city & Customer_type ==@customer_type & Gender == @gender"
    )

    # ---- MAINPAGE ----
    st.title(":bar_chart: Sales Dashboard")
    st.markdown("##")

    # TOP KPI's
    total_sales = int(df_selection["Total"].sum())
    average_rating = round(df_selection["Rating"].mean(), 1)
    star_rating = ":star:" * int(round(average_rating, 0))
    average_sale_by_transaction = round(df_selection["Total"].mean(), 2)

    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        st.subheader("Total Sales:")
        st.subheader(f"US $ {total_sales:,}")
    with middle_column:
        st.subheader("Average Rating:")
        st.subheader(f"{average_rating} {star_rating}")
    with right_column:
        st.subheader("Average Sales Per Transaction:")
        st.subheader(f"US $ {average_sale_by_transaction}")

    st.markdown("""---""")

    # SALES BY PRODUCT LINE [BAR CHART]
    sales_by_product_line = (
        df_selection.groupby(by=["Product line"])
        .sum()[["Total"]]
        .sort_values(by="Total")
    )
    fig_product_sales = px.bar(
        sales_by_product_line,
        x="Total",
        y=sales_by_product_line.index,
        orientation="h",
        title="<b>Sales by Product Line</b>",
        color_discrete_sequence=["#0083B8"] * len(sales_by_product_line),
        template="plotly_white",
    )
    fig_product_sales.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", xaxis=(dict(showgrid=False))
    )

    # SALES BY HOUR [BAR CHART]
    sales_by_hour = df_selection.groupby(by=["hour"]).sum()[["Total"]]
    fig_hourly_sales = px.bar(
        sales_by_hour,
        x=sales_by_hour.index,
        y="Total",
        title="<b>Sales by hour</b>",
        color_discrete_sequence=["#0083B8"] * len(sales_by_hour),
        template="plotly_white",
    )
    fig_hourly_sales.update_layout(
        xaxis=dict(tickmode="linear"),
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=(dict(showgrid=False)),
    )

    left_column, right_column = st.columns(2)
    left_column.plotly_chart(fig_hourly_sales, use_container_width=True)
    right_column.plotly_chart(fig_product_sales, use_container_width=True)

    # ---- HIDE STREAMLIT STYLE ----
    hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
    st.markdown(hide_st_style, unsafe_allow_html=True)
    
