import aiohttp
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types.message_entity import MessageEntityType
import aiohttp
import json
import os
import typing as tp
import logging

bot = Bot(token=os.environ['BOT_TOKEN'])
api_token = os.environ['API_TOKEN']
dp = Dispatcher(bot)
logger = logging.getLogger('Cinemabot')
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """
        Replies with About message
    """
    await message.reply(f"Привет! Я Cinemabot. \n"
                        f"Просто введи название фильма и я покажу тебе информацию о нем и ссылку на просмотр.")


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    """
        Replies with help message
    """
    await message.reply(f"Просто введи название фильма и я покажу тебе информацию о нем и ссылку на просмотр.")


@dp.message_handler()
async def send_movie_info(message: types.Message):
    """
        Process user requests and replies with movie info (or with failure message)
    """
    logger.log(logging.INFO, f'Movie with title {message.text} requested.')
    async with aiohttp.ClientSession() as session:
        async with session.get("https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword",
                               params={'keyword': message.text},
                               headers={'X-API-KEY': api_token}) as response:
            current_query = await response.json()
        if current_query['pagesCount'] == 0:
            logger.log(logging.INFO, f'Couldn\'t find movie with title {message.text}.')
            await message.reply("К сожалению, такой фильм не найден :(")
            return

        async with session.get(
                "https://kinopoiskapiunofficial.tech/api/v2.1/films/" + str(current_query['films'][0][
                                                                                'filmId']),
                params={"append_to_response": "RATING"},
                headers={'X-API-KEY': api_token}) as response:
            current_movie = await response.json()
            current_movie_data = current_movie['data']

        if 'rating' not in current_movie:
            current_movie = await response.json()
            current_movie_data = current_movie['data']

        reply_message = f"*Название*: {get_field_or_dash(current_movie_data, 'nameRu')} " \
                        f"({get_field_or_dash(current_movie_data, 'nameEn')})\n\n" \
                        f"*Год выпуска*: {get_field_or_dash(current_movie_data, 'year')}\n\n" \
                        f"*Длительность*: {get_field_or_dash(current_movie_data, 'filmLength')}\n" \
                        f"*Возрастной рейтинг*: {get_field_or_dash(current_movie_data, 'ratingAgeLimits')}+\n\n" \
                        f"*Описание*:\n" \
                        f"{get_field_or_dash(current_movie_data, 'description')}\n\n" \
                        f"*Оценка*: Кинопоиск  {get_field_or_dash(current_movie['rating'], 'rating')}, " \
                        f"IMDB {get_field_or_dash(current_movie['rating'], 'ratingImdb')}\n\n" \
                        f"*Ссылка*: {get_field_or_dash(current_movie_data, 'webUrl')}"
        if len(reply_message) >= 1024:
            sent_message = await message.answer_photo(current_movie_data['posterUrl'])
            await sent_message.answer(reply_message, parse_mode='markdown')
        else:
            await message.answer_photo(current_movie_data['posterUrl'], caption=reply_message, parse_mode='markdown')
        logger.log(logging.INFO, f'Message to request with title {message.text} sent.')


def get_field_or_dash(container: tp.Dict[str, tp.Any], key: str) -> str:
    """
    Returns value stored in container by key or returns '-'
    """
    if key in container and container[key] is not None:
        return container[key]
    else:
        return '-'


if __name__ == '__main__':
    executor.start_polling(dp)
