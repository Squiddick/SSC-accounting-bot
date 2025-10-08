#unique user id
import time
import uuid
from google import genai
from fastapi import FastAPI
#for env vars
import dotenv
#tg
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes
#json
import json
from typing import Union
import asyncio
import fastapi_poe as fp

app = FastAPI()
dotenv.load_dotenv()
config = dotenv.dotenv_values(".env")
gemini = genai.Client(api_key=config["TOKEN"])

def set_format(json_string: str) -> str:
    string_dict = json.loads(json_string)
    f_string = ["{} {}".format(key, value) for key, value in string_dict.items()]
    return "\n".join(f_string)

async def save_to_json(name:str, json_string: str) -> None:
    string_dict = json.loads(json_string)
    async with open("reports.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data["report"]["name"] = string_dict
    async with open("reports.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


async def get_ai_query(name: str, query: str) -> str:
    with open("reports.json", "r", encoding="utf-8") as f:
        report = json.load(f)["reports"][name]

    temp = "Твоя задача — точно воспроизвести структуру предоставленного шаблона отчета, заполнив его данными из указанных далее расходников. Действуй строго по следующим правилам: Формат: Выведи ТОЛЬКО заполненный шаблон. Типы данных: КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО заключать числовые значения (целые или дробные) в кавычки. Они должны быть представлены КАК ЕСТЬ. Текстовые значения должны быть заключены в кавычки, если это предусмотрено оригинальным шаблоном. Ключи: ключи ДОЛЖНЫ быть закрыты только в двойные кавычки типа, и КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО закрывать ключи в одинарные кавычки. Структура: СОХРАНИ оригинальную структуру и порядок разделов шаблона. Содержимое: Заполни все соответствующие поля, используя предоставленные расходники. Оформление: КАТЕГОРИЧЕСКИ запрещено добавлять любые пояснения, вводные фразы, приписки, форматирующие блоки (например, json, text) или любые другие символы/текст, кроме самого заполненного отчета."
    #temp="Тебе дан правильный шаблон отчета. Без лишних объяснений, вышли такую же структура шаблона в таком виде,в котором тебе был дан, заполни его с учетом следующих расходников(ОБЯЗАТЕЛЬНО убери всякие приписки форматов типа ```json ```): "
    prompt= str(report) + temp + query

    try:
        response = gemini.models.generate_content(model=config["MODEL"],contents=prompt)

        return response.text.replace("'", '"')

    except Exception as e:
        raise e
"""внезапные соображения: можно обернуть response в таску, и планировать его вызов, каждый раз, когда в функцию поступает обновление о новом сообщение.
Буду тащить в аргумент update: Update. Update тащится из модуля telegram Update.inline_query.query.from_user.id
"""



async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query

    if not query:
        return

    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title='Green',
            input_message_content=InputTextMessageContent(await get_ai_query('Green', query.lower())),
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title='E-City',
            input_message_content=InputTextMessageContent(await get_ai_query('E-City', query.lower())),
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title='Zlatoust',
            input_message_content=InputTextMessageContent(await get_ai_query('Zlatoust', query.lower())),
        )
    ]
    await update.inline_query.answer(results)




def main() -> None:
    application = Application.builder().token(config["BOT_TOKEN"]).build()
    application.add_handler(InlineQueryHandler(inline_query))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()



#функция get_api_query будет возвращать ответ в виде строки, а сохранять в файл json. gemini пускай возвращает json формат,
#а я создам отдельную функцию конвертация в строку.
#использую концецию debouncing