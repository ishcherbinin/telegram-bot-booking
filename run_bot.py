import asyncio
import logging.config
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from logging_conf import log_config
from restaurant_space import TablesStorage, Table

logging.config.dictConfig(log_config)

_logger = logging.getLogger(__name__)

api_token = os.getenv("TELEGRAM_API_TOKEN")

group_chat_id = os.getenv("GROUP_CHAT_ID")


tables_storage = TablesStorage.from_csv_file("./tables.csv")
bot = Bot(token=api_token)
ds = Dispatcher()

# noinspection PyTypeChecker
CURRENT_TABLE: Table = None

# Define the FSM states for each step
class OrderStates(StatesGroup):
    waiting_for_seats = State()
    waiting_for_name = State()
    waiting_for_time = State()
    waiting_for_confirmation = State()


@ds.message(Command("book-table"))
async def book_table(message: types.Message, state: FSMContext):
    _logger.info("Start booking table")
    _logger.debug(message)
    await message.answer("Please provide the number of seats you need")
    await state.set_state(OrderStates.waiting_for_seats)

@ds.message(OrderStates.waiting_for_seats)
async def process_seats(message: types.Message, state: FSMContext):
    _logger.info("Processing request for number of seats")
    seats = message.text
    if not seats.isdigit():
        await message.answer("Please enter a valid number.")
        await state.set_state(OrderStates.waiting_for_seats)
        return
    seats = int(seats)
    _logger.info(f"User requested table for {seats} seats")
    table = tables_storage.search_for_table(seats)
    if not table:
        await message.answer("Sorry, we don't have a table for this number of seats")
        await state.set_state(OrderStates.waiting_for_seats)
        return
    global CURRENT_TABLE
    CURRENT_TABLE = table
    await message.answer("Please provide name you want to book the table for")
    await state.set_state(OrderStates.waiting_for_name)

@ds.message(OrderStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    _logger.info("Processing user name")
    name = message.text
    _logger.info(f"User name: {name}")
    global CURRENT_TABLE
    CURRENT_TABLE.user_name = name
    await message.answer("Please provide time you want to book the table for. Format: YYYY-MM-DD HH:MM")
    await state.set_state(OrderStates.waiting_for_time)

@ds.message(OrderStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    _logger.info("Processing booking time")
    time = message.text
    try:
        booking_time = datetime.strptime(time, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Please enter a valid date and time in the format YYYY-MM-DD HH:MM")
        await state.set_state(OrderStates.waiting_for_time)
        return
    _logger.info(f"Booking time: {booking_time}")
    global CURRENT_TABLE
    CURRENT_TABLE.booking_time = booking_time
    await message.answer(f"Table for {CURRENT_TABLE.capacity} seats for "
                         f"{CURRENT_TABLE.user_name} at {CURRENT_TABLE.booking_time}")
    await message.answer("Please confirm the booking. Answer Yes/No")
    await state.set_state(OrderStates.waiting_for_confirmation)

@ds.message(OrderStates.waiting_for_confirmation)
async def process_confirmation(message: types.Message, state: FSMContext):
    _logger.info("Processing confirmation")
    global CURRENT_TABLE
    table = CURRENT_TABLE
    confirmation = message.text.upper()
    if confirmation == "YES":
        CURRENT_TABLE.is_reserved = True
        await message.answer(f"Table {table.table_id} for {table.capacity} "
                             f"seats is booked for {table.user_name} at {table.booking_time}")
        await message.answer("Table is booked. Manager will contact you soon to confirm booking")
        await send_request_to_chat(message, CURRENT_TABLE)
    else:
        await message.answer("Booking is rejected")
        await state.set_state(OrderStates.waiting_for_seats)
    await state.clear()

def send_request_to_chat(message: types.Message, table: Table) -> types.Message:
    _logger.info(f"Sending booking detail to separate chat {group_chat_id}")
    user = message.from_user
    bot.send_message(chat_id=group_chat_id,
                     text=f"User: @{user} "
                          f"Request: \n{table}")
    return message

async def main():
    try:
        await ds.start_polling(bot)
    except Exception as e:
        _logger.exception("Error while polling")
        raise e

if __name__ == "__main__":
    asyncio.run(main())