import asyncio
import datetime
import os

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from ml import get_answer_gpt
from sklearn.preprocessing import LabelEncoder

app = FastAPI()
db_client = AsyncIOMotorClient(
    f"{os.environ['MONGO_HOST']}:27018",
    username=os.environ["MONGO_USER"],
    password=os.environ["MONGO_PASSWORD"],
)
db = db_client[os.environ["MONGO_DB_NAME"]]

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ML


def load_dataframe(path: str) -> pd.DataFrame:
    df = None

    try:
        df = pd.read_csv(path)
        if len(df.columns) == 1 and ";" in df.columns[0]:
          df = pd.read_csv(path, sep=";")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="cp1251")
        if len(df.columns) == 1 and ";" in df.columns[0]:
          df = pd.read_csv(path, sep=";", encoding="cp1251")

    if df is None:
        raise UnicodeDecodeError

    return df


async def correlation_hypothesis_brief(main_text: str, sub_hypothesis: dict):
    title = await get_answer_gpt(f"{main_text}. Приведи краткое описание гипотезы, 5-10 слов")
    sub_hypothesis["title"] = title


async def correlation_hypothesis_full(main_text: str, sub_hypothesis: dict):
    main = await get_answer_gpt(f"{main_text}. Дай подробное описание гипотезы с обоснованием, примерами и способами проверки. Ответ дай в виде HTML-разметки")
    sub_hypothesis["main"] = main or ""


async def correlation_hypothesis(
    info_data: str, col1: str, col2: str, corr: float, result: dict, res_index: int
):
    try:
        sub_hypothesis = {}
        main_text = f"У нас есть {info_data}. Сформулируй гипотезу, зная, что корреляция между колонками {col1} и {col2} составляет {round(corr, 2)}"
        await asyncio.gather(
            asyncio.create_task(correlation_hypothesis_brief(main_text, sub_hypothesis)),
            asyncio.create_task(correlation_hypothesis_full(main_text, sub_hypothesis))
        )
        print(sub_hypothesis)
        result[res_index] = "\n\n".join([sub_hypothesis["title"], sub_hypothesis["main"]])
    except Exception as exep:
        print(f"Load hypothesis failed: {exep}")
        result[res_index] = None


async def random_hypothesis(
    df: pd.DataFrame, result: dict, res_index: int
):
    try:
        sub_hypothesis = {}
        main_text = f"Расскажи что-нибудь о данных, статистика которых выглядит следущим образом: {df.describe()}\n\n"
        await asyncio.gather(
            asyncio.create_task(correlation_hypothesis_brief(main_text, sub_hypothesis)),
            asyncio.create_task(correlation_hypothesis_full(main_text, sub_hypothesis))
        )
        print(sub_hypothesis)
        result[res_index] = "\n\n".join([sub_hypothesis["title"], sub_hypothesis["main"]])
    except Exception as exep:
        print(f"Load hypothesis failed: {exep}")
        result[res_index] = None


async def get_columns_info(columns: list[str], results):
    columns_as_str = ", ".join(columns)
    results["columns"] = await get_answer_gpt(
        f"В наборе данных есть колонки: {columns_as_str}. О чём эти данные? Расскажи об их смысле и возможных связях. В новой строке придумай, какие ещё фичи можно сгененрировать на основании имеющихся данных. Ответ сделай в виде HTML-разметки (размечай списки, абзацы, курсив)"
    )


async def get_brief_info(columns: list[str], results):
    columns_as_str = ", ".join(columns)
    results["brief"] = await get_answer_gpt(
        f"В наборе данных есть колонки: {columns_as_str}. О чём эти данные? Дай ответ в одном предложении"
    )


async def get_correlations(df_corr: pd.DataFrame, results) -> list[str]:
    le = LabelEncoder()
    for non_num_field in df_corr.select_dtypes(exclude=np.number).columns.tolist():
      df_corr[non_num_field] = le.fit_transform(df_corr[non_num_field])
    c = df_corr.corr()
    s = c.unstack()
    corrs_list = list(s.to_dict().items())
    print(corrs_list[:10])
    sorted_corrs_list = sorted(
        corrs_list, key=lambda el: abs(el[1]), reverse=True
    )
    already_saved = set()
    clean_sorted_corrs_list = []
    print(sorted_corrs_list[:10])
    corr_upper_bound = 1.0
    if len(sorted_corrs_list) > 10:
        corr_upper_bound = 0.76
    for (c1, c2), corr in sorted_corrs_list:
      if (c1, c2) not in already_saved and (c2, c1) not in already_saved and 0.4 <= abs(corr) < corr_upper_bound:
        clean_sorted_corrs_list.append(((c1, c2), corr))
        already_saved.add((c1, c2))
    print(clean_sorted_corrs_list)
    results["corr"] = clean_sorted_corrs_list


def generate_plot(df: pd.DataFrame, column1: str, column2: str):
    step = 1
    if df.shape[0] >= 1500:
        step = df.shape[0] // 500
    plot = df[[column1, column2]][::step]
    if len(plot[column1].unique()) == 1 and len(plot[column2].unique()) == 1:
        return {}
        # if len(plot[column1].unique()) < len(plot[column2].unique()):
        #     x_col, y_col = column1, column2
        # else:
        #     x_col, y_col = column2, column1
        # xy_plot = json.loads(plot.dropna().groupby(x_col).mean().reset_index().to_json())
        # xy_plot["x"] = [str(el) for el in xy_plot.pop(x_col).values()]
        # xy_plot["x_title"] = x_col
        # xy_plot["y"] = list(xy_plot.pop(y_col).values())
        # xy_plot["y_title"] = y_col
        # plot_type = "hist"
    else:
        xy_plot = plot.reset_index(drop=True).dropna().to_dict(orient="list")
        xy_plot["x"] = xy_plot.pop(column1)
        xy_plot["x_title"] = column1
        xy_plot["y"] = xy_plot.pop(column2)
        xy_plot["y_title"] = column2
        plot_type = "scatter"

    return {"plot": xy_plot, "plot_type": plot_type,}


async def get_hypotheses(data_path: str, dataset_id: str, filename: str) -> dict:
    df = load_dataframe(data_path)
    tasks = []
    results = {}
    formatted_results = {
        "meta": {
            "id": dataset_id,
            "filename": filename,
            "upload_ts": datetime.datetime.now(),
        },
        "hypotheses": [],
    }

    t_corrs = asyncio.create_task(get_correlations(df, results))
    t_colls_info = asyncio.create_task(get_columns_info(list(df.columns), results))
    t_dataset_brief = asyncio.create_task(get_brief_info(list(df.columns), results))
    await asyncio.gather(t_corrs, t_colls_info, t_dataset_brief)

    formatted_results["meta"]["columns_info"] = results["columns"]

    brief_info = results["brief"]

    correlations_info = results["corr"]

    for n, corr_data in enumerate(correlations_info):
        (column1, column2), corr = corr_data
        tasks.append(
            asyncio.create_task(
                correlation_hypothesis(brief_info, column1, column2, corr, results, n)
            )
        )

    tasks.append(
        asyncio.create_task(
            random_hypothesis(df, results, len(tasks))
        )
    )

    await asyncio.gather(*tasks)

    for n in range(len(tasks)):
        if results[n] is None:
            continue

        current_header = results[n].split("\n")[0]
        current_content = "\n".join(results[n].split("\n")[1:])

        if n == len(tasks) - 1:
            formatted_results["hypotheses"].append(
                {
                    "title": current_header,
                    "content": current_content,
                }
            )
            continue

        (column1, column2), corr = correlations_info[n]

        formatted_results["hypotheses"].append(
            {
                "title": current_header,
                "content": current_content,
                **generate_plot(df, column1, column2)
            }
        )

    return formatted_results
