import streamlit as st
from streamlit_option_menu import option_menu
from app_pages import page_main, page_data, page_params, page_grid, page_identify, page_fit, page_run_models


def main():
    with st.sidebar:
        choose = option_menu("Меню",
                             ["Главная", "Данные", "Параметры", "Прогноз" ,"Карта среды", "Обучение модели", "Идентификация"],
                             icons=['book', 'database', 'gear', 'box-fill' ,'grid', 'cpu', 'cursor'],
                             menu_icon="app-indicator", default_index=0,
                             styles={
                                 "container": {"padding": "5!important", "background-color": "#fafafa"},
                                 "icon": {"color": "orange", "font-size": "25px"},
                                 "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px",
                                              "--hover-color": "#eee"},
                                 "nav-link-selected": {"background-color": "#D3D3D3"},
                             }
                             )
    if choose == "Данные":
        page_data.get_page()
    elif choose == "Параметры":
        page_params.get_page()
    elif choose == "Прогноз":
        page_run_models.get_page()
    elif choose == "Карта среды":
        page_grid.get_page()
    elif choose == "Обучение модели":
        page_fit.get_page()
    elif choose == "Идентификация":
        page_identify.get_page()
    elif choose == "Главная":
        page_main.get_page()


st.set_page_config(page_title="Идентификация источника выбросов", page_icon="chart_with_upwards_trend", layout="wide")

if __name__ == "__main__":
    main()