import asyncio
import logging.config
import os
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from logging_conf import log_config
from restaurant_space import TablesStorage, Table
from validators import validate_date

logging.config.dictConfig(log_config)

_logger = logging.getLogger(__name__)

api_token = os.getenv("TELEGRAM_API_TOKEN")

group_chat_id = os.getenv("GROUP_CHAT_ID")

dist_tables = os.getenv("TABLES_FILE")

tables_storage = TablesStorage.from_csv_file(Path(dist_tables))
bot = Bot(token=api_token)
ds = Dispatcher()

# Define the FSM states for each step
class OrderStates(StatesGroup):
    waiting_for_seats = State()
    waiting_for_date_client = State()
    waiting_for_name = State()
    waiting_for_time = State()
    waiting_for_confirmation = State()
    waiting_for_date_manager = State()


"""
This part defines client oriented part which might be used by account to book table in the restaurant
Open chat with bot and type /book-table to start booking process
"""

@ds.message(Command("book-table"))
async def book_table(message: types.Message, state: FSMContext):
    _logger.info("Start booking table")
    _logger.debug(message)
    await message.answer("Please provide date you want to reserve table for. Format: DD.MM")
    await state.set_state(OrderStates.waiting_for_date_client)

@ds.message(OrderStates.waiting_for_date_client)
async def process_date(message: types.Message, state: FSMContext):
    _logger.info("Processing request particular date for booking")
    date = message.text
    chosen_date = await validate_date(date)
    if not chosen_date:
        await message.answer("Please enter a valid date and time in the format DD.MM")
        await state.set_state(OrderStates.waiting_for_date_client)
        return
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    await state.set_data({"tables": tables_for_date})
    await message.answer("Please provide the number of seats you need")
    await state.set_state(OrderStates.waiting_for_seats)


@ds.message(OrderStates.waiting_for_seats)
async def process_seats(message: types.Message, state: FSMContext):
    _logger.info("Processing request for number of seats")
    seats = message.text
    if not seats.isdigit():
        await message.answer("Please enter a valid number. Number should be digit")
        await state.set_state(OrderStates.waiting_for_seats)
        return
    seats = int(seats)
    _logger.info(f"User requested table for {seats} seats")
    data = await state.get_data()
    tables = data["tables"]
    table = tables_storage.search_for_table(seats, tables)
    await state.set_data({"table": table})
    if not table:
        await message.answer("Sorry, we don't have a table for this number of seats")
        await state.set_state(OrderStates.waiting_for_seats)
        return
    await state.update_data({"table": table})
    await message.answer("Please provide name you want to book the table for")
    await state.set_state(OrderStates.waiting_for_name)

@ds.message(OrderStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    _logger.info("Processing user name")
    name = message.text
    _logger.info(f"User name: {name}")
    data = await state.get_data()
    table = data["table"]
    table.user_name = name
    await message.answer("Please provide time you want to book the table for. Format: HH:MM")
    await message.answer("NOTE. Booking will be kept only for 1 hour after time you provided")
    await state.set_state(OrderStates.waiting_for_time)

@ds.message(OrderStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    _logger.info("Processing booking time")
    time = message.text
    try:
        booking_time = datetime.strptime(time, "%H:%M")
    except ValueError:
        await message.answer("Please enter a valid date and time in the format HH:MM")
        await state.set_state(OrderStates.waiting_for_time)
        return
    _logger.info(f"Booking time: {booking_time}")
    data = await state.get_data()
    table = data["table"]
    table.booking_time = booking_time
    await message.answer(f"Table for {table.capacity} seats for "
                         f"{table.user_name} at {table.readable_booking_time}")
    await message.answer("Please confirm the booking. Answer Yes/No")
    await state.set_state(OrderStates.waiting_for_confirmation)

@ds.message(OrderStates.waiting_for_confirmation)
async def process_confirmation(message: types.Message, state: FSMContext):
    _logger.info("Processing confirmation")
    data = await state.get_data()
    table = data["table"]
    confirmation = message.text.upper()
    if confirmation == "YES":
        table.is_reserved = True
        await message.answer(f"Table {table.table_id} for {table.capacity} "
                             f"seats is booked for {table.user_name} at {table.readable_booking_time}")
        await message.answer("Table is booked. Manager will contact you soon to confirm booking")
        await send_request_to_chat(message, table)
    else:
        await message.answer("Booking is rejected")
        await state.set_state(OrderStates.waiting_for_seats)
    await state.clear()

async def send_request_to_chat(message: types.Message, table: Table) -> None:
    _logger.info(f"Sending booking detail to separate chat {group_chat_id}")
    user = message.from_user.username
    await bot.send_message(chat_id=group_chat_id,
                     text=f"\nUser name: {user} "
                          f"\nTable №: {table.table_id},"
                          f"\nNumber of seats: {table.capacity},"
                          f"\nBooking time: {table.readable_booking_time},"
                          f"\nName: {table.user_name}")


"""
This part defines manager oriented part which might be used by manager to check bookings
"""

@ds.message(Command("booked-tables"))
async def booked_tables(message: types.Message, state: FSMContext):
    _logger.info("Start checking booked tables")
    await message.answer("Please provide date you want to check bookings for. Format: DD.MM")
    await state.set_state(OrderStates.waiting_for_date_manager)

@ds.message(OrderStates.waiting_for_date_manager)
async def processing_date_manager(message: types.Message, state: FSMContext):
    _logger.info("Processing request particular date for checking bookings")
    date = message.text
    chosen_date = await validate_date(date)
    if not chosen_date:
        await message.answer("Please enter a valid date and time in the format DD.MM")
        await state.set_state(OrderStates.waiting_for_date_manager)
        return
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    reserved_tables = [table for table in tables_for_date if table.is_reserved]
    if not booked_tables:
        await message.answer("No tables are booked for this date")
        await state.clear()
        return
    for index, table in enumerate(reserved_tables):
        await message.answer(f"{index + 1}. Table {table.table_id} for {table.capacity} "
                             f"seats is booked for {table.user_name} at {table.readable_booking_time}")

async def main():
    try:
        await ds.start_polling(bot)
    except Exception as e:
        _logger.exception("Error while polling")
        raise e

if __name__ == "__main__":
    asyncio.run(main())