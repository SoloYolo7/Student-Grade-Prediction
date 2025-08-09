import gradio as gr
import pandas as pd
import requests
import os
from datetime import datetime

# 1) Сделаем адреса конфигурируемыми через env (удобно для dev/prod)  ←
API_URL = os.getenv("API_URL", "http://api-student-grade-prediction/predict-single")
ROOT_PATH = os.getenv("GRADIO_ROOT_PATH", "/ui-student-grade-prediction")  # ←

def get_predictions(uploaded_file):
    """
    Основная функция, которая обрабатывает загруженный файл, отправляет данные на API,
    получает предсказания и готовит файлы для скачивания.
    """
    if uploaded_file is None:
        raise gr.Error("Пожалуйста, сначала загрузите CSV файл.")

    # 2) Надёжное получение пути к файлу из gr.File (поддержит разные режимы)  ←
    file_path = getattr(uploaded_file, "name", None)
    if file_path is None and isinstance(uploaded_file, dict):
        file_path = uploaded_file.get("name")
    if file_path is None:
        file_path = str(uploaded_file)

    try:
        # 3) UTF-8 с BOM тоже прочитается (часто из Excel)  ←
        df_original = pd.read_csv(file_path, encoding="utf-8-sig")
    except Exception as e:
        raise gr.Error(f"Не удалось прочитать файл. Убедитесь, что это корректный CSV. Ошибка: {e}")

    records_for_api = df_original.to_dict(orient='records')
    payload = {"features": records_for_api}

    try:
        response = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        predictions = response.json().get('predictions')
    except requests.exceptions.ConnectionError:
        raise gr.Error(f"Не удалось подключиться к API. Убедитесь, что FastAPI сервер доступен по адресу {API_URL}")
    except requests.exceptions.HTTPError as e:
        raise gr.Error(f"API вернуло ошибку: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise gr.Error(f"Произошла непредвиденная ошибка при запросе к API: {e}")

    if predictions is None:
        raise gr.Error("API не вернуло предсказания в ожидаемом формате.")

    df_with_predictions = df_original.copy()
    df_with_predictions['Predicted_Grade'] = predictions

    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = os.path.splitext(os.path.basename(file_path))[0]  # ←
    csv_path = os.path.join(output_dir, f"{base_filename}_{timestamp}.csv")
    excel_path = os.path.join(output_dir, f"{base_filename}_{timestamp}.xlsx")

    df_with_predictions.to_csv(csv_path, index=False)

    # 4) Если в образе нет openpyxl — чтобы не падало, можно убрать engine или оставить как есть  ←
    df_with_predictions.to_excel(excel_path, index=False)  # engine='openpyxl' можно удалить

    return df_with_predictions, gr.update(visible=True, value=csv_path), gr.update(visible=True, value=excel_path)

with gr.Blocks(theme=gr.themes.Soft(), title="Предсказание оценок") as demo:
    gr.Markdown("# 🔮 Сервис предсказания оценок студентов")
    gr.Markdown("Загрузите CSV файл с данными студентов, чтобы получить предсказания их итоговых оценок.")

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(label="Загрузите ваш CSV файл", file_types=[".csv"])
            btn_predict = gr.Button("Получить предсказание", variant="primary")

            btn_download_csv = gr.File(label="Скачать CSV", visible=False)
            btn_download_excel = gr.File(label="Скачать Excel", visible=False)

        with gr.Column(scale=2):
            df_output = gr.DataFrame(label="Результаты с предсказаниями")

    btn_predict.click(
        fn=get_predictions,
        inputs=file_input,
        outputs=[df_output, btn_download_csv, btn_download_excel]
    )

if __name__ == "__main__":
    # 5) Используем переменную окружения или дефолтный префикс  ←
    demo.launch(server_name="0.0.0.0", server_port=8002, root_path=ROOT_PATH)