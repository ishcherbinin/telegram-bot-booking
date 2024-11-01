import asyncio
import logging.config
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from logging_conf import log_config
from restaurant_space import TablesStorage, Table
from validators import validate_date, validate_time, validate_seats

logging.config.dictConfig(log_config)

_logger = logging.getLogger(__name__)

# assign environment variables to variables
api_token = os.getenv("TELEGRAM_API_TOKEN")

group_chat_id = str(os.getenv("GROUP_CHAT_ID"))

dist_tables = os.getenv("TABLES_FILE")
allowed_chat_ids = {os.getenv("ALLOWED_CHAT_IDS")} | {group_chat_id}

# create relevant objects
tables_storage = TablesStorage.from_csv_file(Path(dist_tables))

bot = Bot(token=api_token)
storage = MemoryStorage()
ds = Dispatcher(storage=storage)


# Define the FSM states for each step
class OrderStates(StatesGroup):
    waiting_for_seats = State()
    waiting_for_date_client = State()
    waiting_for_name = State()
    waiting_for_time = State()
    waiting_for_confirmation = State()
    # TODO add ability to manage reservation thru requests



class ManagerStates(StatesGroup):
    waiting_for_date_manager = State()
    wait_for_number_for_cancel = State()
    waiting_cancel_reservation = State()
    waiting_for_number_for_reserve = State()
    waiting_for_name_for_reserve = State()
    waiting_reserve_table = State()


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
    chosen_date = await get_requested_date(message, state)
    if chosen_date is None:
        return
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    await state.set_data({"tables": tables_for_date})
    await message.answer("Please provide the number of seats you need")
    await state.set_state(OrderStates.waiting_for_seats)


@ds.message(OrderStates.waiting_for_seats)
async def process_seats(message: types.Message, state: FSMContext):
    _logger.info("Processing request for number of seats")
    seats = message.text
    seats = await validate_seats(seats)
    if seats is None:
        await message.answer("Please enter a valid number. Number should be digit")
        await state.set_state(OrderStates.waiting_for_seats)
        return
    _logger.info(f"User requested table for {seats} seats")
    data = await state.get_data()
    tables = data["tables"]
    table = tables_storage.search_for_table(seats, tables)
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
    booking_time, text = await validate_time(time)
    if booking_time is None:
        await message.answer(text)
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
    _logger.info("Processing confirmation from client")
    data = await state.get_data()
    table = data["table"]
    confirmation = message.text.upper()
    if confirmation == "YES":
        table.is_reserved = True
        await message.answer(f"Table {table.table_id} for {table.capacity} "
                             f"seats is booked for {table.user_name} at {table.readable_booking_time}")
        validation = await validate_chat_id(str(message.chat.id), message)
        if validation:
            # TODO add mechanism to confirm from manager
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

async def validate_chat_id(chat_id: str, message: types.Message) -> bool:
    _logger.info(f"Chat id: {chat_id}")
    _logger.info(f"Allowed chat ids: {allowed_chat_ids}")
    if chat_id not in allowed_chat_ids:
        await message.answer("You are not allowed to use this command")
        return True
    return False

@ds.message(Command("check-bookings"))
async def check_bookings(message: types.Message, state: FSMContext):
    _logger.info("Start checking bookings")
    if await validate_chat_id(str(message.chat.id), message):
        return
    await message.answer("Please provide date you want to check bookings for. Format: DD.MM")
    await state.set_state(ManagerStates.waiting_for_date_manager)


@ds.message(ManagerStates.waiting_for_date_manager)
async def process_date_manager(message: types.Message, state: FSMContext):
    _logger.info("Processing request particular date for checking bookings")
    chosen_date = await get_requested_date(message, state)
    if chosen_date is None:
        return
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    tables = [table for table in tables_for_date if table.is_reserved]
    if not tables:
        await message.answer("There are no bookings for this date")
        await state.clear()
        return
    for table in tables:
        await message.answer(f"Table №: {table.table_id},"
                             f"\nNumber of seats: {table.capacity},"
                             f"\nBooking time: {table.readable_booking_time},"
                             f"\nName: {table.user_name}")
    await state.clear()

@ds.message(Command("reserve-table"))
async def reserve_table(message: types.Message, state: FSMContext):
    _logger.info("Start reserving table")
    if await validate_chat_id(str(message.chat.id), message):
        return
    await message.answer("Please provide date you want to reserve table for. Format: DD.MM")
    await state.set_state(OrderStates.waiting_for_date_client)

@ds.message(Command("cancel-reservation"))
async def cancel_reservation(message: types.Message, state: FSMContext):
    _logger.info("Start cancelling reservation")
    if await validate_chat_id(str(message.chat.id), message):
        return
    await message.answer("Please provide date you want to cancel reservation for. Format: DD.MM")
    await state.set_state(ManagerStates.wait_for_number_for_cancel)

@ds.message(ManagerStates.wait_for_number_for_cancel)
async def process_number_for_reservation_cancel(message: types.Message, state: FSMContext):
    _logger.info("Processing request for table number to cancel reservation")
    chosen_date = await get_requested_date(message, state)
    if chosen_date is None:
        return
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    tables = [table for table in tables_for_date if table.is_reserved]
    if not tables:
        await message.answer("There are no bookings for this date")
        await state.clear()
        return
    await message.answer(f"Please provide table number you want to cancel reservation for. "
                         f"Available tables: {[table.table_id for table in tables]}")
    await state.set_data({"tables": tables})
    await state.set_state(ManagerStates.waiting_cancel_reservation)

@ds.message(ManagerStates.waiting_cancel_reservation)
async def process_cancel_reservation(message: types.Message, state: FSMContext):
    _logger.info("Processing request for table number to cancel reservation")
    table_number = message.text
    data = await state.get_data()
    tables = data["tables"]
    table = next((table for table in tables if table.table_id == int(table_number)), None)
    if table is None:
        await message.answer("Table with this number is not found")
        await state.set_state(ManagerStates.waiting_cancel_reservation)
        return
    table.is_reserved = False
    table.booking_time = None
    table.user_name = None
    await message.answer(f"Reservation for table №{table.table_id} is cancelled")
    await state.clear()

async def get_requested_date(message: types.Message, state: FSMContext) -> Optional[datetime]:
    date = message.text
    chosen_date, text = await validate_date(date)
    if chosen_date is None:
        await message.answer(text)
        await state.set_state(ManagerStates.waiting_for_date_manager)
        return
    return chosen_date

@ds.message(Command("get-id"))
async def get_id(message: types.Message):
    if str(message.chat.id) in allowed_chat_ids:
        await message.answer("You are not allowed to use this command")
        return
    ids = str(message.chat.id)
    _logger.info(f"Chat id: {ids}")
    await message.answer(ids)

async def main():
    try:
        await ds.start_polling(bot)
    except Exception as e:
        _logger.exception("Error while polling")
        raise e


if __name__ == "__main__":
    asyncio.run(main())
