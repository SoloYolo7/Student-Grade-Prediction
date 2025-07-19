import streamlit as st
import pandas as pd
import requests
import io
import os

st.set_page_config(
    page_title="Предсказание оценок",
    page_icon="🔮",
    layout="wide"
)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/predict-single")

def convert_df_to_csv(df):
    """Конвертирует DataFrame в CSV для скачивания."""
    return df.to_csv(index=False).encode('utf-8')

def convert_df_to_excel(df):
    """Конвертирует DataFrame в Excel (в памяти) для скачивания."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Predictions')
    processed_data = output.getvalue()
    return processed_data


st.title("🔮 Сервис предсказания оценок студентов")
st.markdown("Загрузите CSV файл с данными студентов, чтобы получить предсказания их итоговых оценок от модели.")

uploaded_file = st.sidebar.file_uploader(
    "Выберите CSV файл",
    type=['csv'],
    help="Файл должен содержать колонки, совместимые с моделью."
)

if uploaded_file is not None:
    try:
        df_original = pd.read_csv(uploaded_file)
        st.subheader("Предпросмотр загруженных данных")
        st.dataframe(df_original.head())

        with st.spinner("Отправка данных на API и получение предсказаний..."):
            
            records_for_api = df_original.to_dict(orient='records')
            payload = {"features": records_for_api}

            try:
                response = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
                response.raise_for_status()
                
                predictions = response.json().get('predictions')
                
                if predictions:
                    st.success("🎉 Предсказания успешно получены!")
                    df_with_predictions = df_original.copy()
                    df_with_predictions['Predicted_Grade'] = predictions
                    
                    st.subheader("Результаты с предсказаниями")
                    st.dataframe(df_with_predictions)

                    st.sidebar.subheader("Скачать результаты")
                    
                    csv_data = convert_df_to_csv(df_with_predictions)
                    excel_data = convert_df_to_excel(df_with_predictions)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.sidebar.download_button(
                            label="📥 Скачать как CSV",
                            data=csv_data,
                            file_name=f"predictions_{uploaded_file.name}",
                            mime='text/csv',
                        )
                    with col2:
                        st.sidebar.download_button(
                            label="📥 Скачать как Excel",
                            data=excel_data,
                            file_name=f"predictions_{uploaded_file.name.replace('.csv', '.xlsx')}",
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        )

                else:
                    st.error("Ошибка: API не вернуло предсказания в ожидаемом формате.")

            except requests.exceptions.ConnectionError:
                st.error(f"Ошибка подключения: Не удалось подключиться к API по адресу {API_URL}. Убедитесь, что FastAPI сервер запущен.")
            except requests.exceptions.HTTPError as e:
                st.error(f"Ошибка от API: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                st.error(f"Произошла непредвиденная ошибка при обращении к API: {e}")

    except Exception as e:
        st.error(f"Не удалось обработать файл. Убедитесь, что это корректный CSV. Ошибка: {e}")