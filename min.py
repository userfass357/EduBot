import logging
import os
import pyodbc
import smtplib
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from email.message import EmailMessage
from dotenv import load_dotenv

# Уровень логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)    

@dp.message_handler(commands=['asis','a'])
async def asis_menu(message: types.Message):
    """
    Обработчик команды /asis.
    Отображает меню для команды /asis.
    """
    await asis_actions_menu(message)


async def asis_actions_menu(message: types.Message):
    """
    Отображает меню действий для команды /asis.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    button11 = types.InlineKeyboardButton(text="Самые часто задоваемые вопросы ❓❔", callback_data="asis_action1")
    button22 = types.InlineKeyboardButton(text="Отправить документы на поступление 📬", callback_data="asis_action2")
    keyboard.add(button11)
    keyboard.add(button22)
    await message.answer("Добро пожаловать в Музыкальный колледж! Мы рады видеть вас здесь.\n"
                        "Мы поможем вам получить информацию о поступлении, ответим на ваши вопросы "
                        "и предоставим необходимую поддержку.\n"
                        "Если у вас возникли вопросы, не стесняйтесь задавать их. Удачи в поступлении!", reply_markup=keyboard)

@dp.message_handler(commands=['start','s'])
async def start(message: types.Message):
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение с кнопкой для отправки контакта с номером телефона.
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton(text="Отправить контакт", request_contact=True)
    keyboard.add(button)

    await message.answer("Добро пожаловать! Этот бот поможет вам получить доступ к личной информации, такой как сроки защиты курсовых работ, результаты экзаменов, сроки сессий и прохождения практик. Для абитурьентов он предоставит ответы на типовые вопросы о поступлении, возможность отправить в приемную комиссию заявление и документы на поступление, а также узнать результаты вступительных испытаний и экзаменов.\n\nЭто персональная информация, поэтому для идентификации вам потребуется поделиться своим контактом. Нажмите кнопку ниже для этого:", reply_markup=keyboard)


@dp.message_handler(content_types=types.ContentType.CONTACT)
async def handle_contact(message: types.Message):
    """
    Обработчик получения контакта.
    Проверяет наличие номера телефона в базе данных Access и отправляет соответствующее сообщение.
    """
    await message.answer("Идет поиск...")
    contact = message.contact
    phone_number = contact.phone_number
    user_id = message.from_user.id

    # Подключение к базе данных Access
    conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=C:\dev\progect_telega\База Данных Коледжа.accdb;')
    conn = pyodbc.connect(conn_str)


# Поиск номера телефона в базе данных
    cursor = conn.cursor()
    cursor.execute("SELECT ФИО, Группа FROM Студенты WHERE [Номер телефона] = ?", (phone_number,))
    result = cursor.fetchone()

    
    if result:
        # Номер найден, отправляем сообщение с данными студента
        full_name = result[0]  # Получаем ФИО студента
        group = result[1]  # Получаем группу студента

        response_message = f"Нашёл вас, вы являетесь студентом: \n {full_name}, группы {group}."
        await message.answer(response_message)
    else:
        # Номер не найден
        await message.answer("Номер не найден в базе данных.")
        await asis_menu(message)
        
    # Проверка, существует ли пользователь с данным номером телефона в базе данных
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Студенты WHERE [Номер телефона]=?", (phone_number,))
    result = cursor.fetchone()
    
    if result:
        # Пользователь существует, проверяем значение ID
        existing_id = result.ID
        if existing_id:
            # У пользователя уже есть значение ID, выводим сообщение об успешной авторизации
            await message.answer("Авторизация прошла успешно. Добро пожаловать!")
            await menu(message)
        else:
            # Обновляем значение ID для найденной строки
            cursor.execute("UPDATE Студенты SET ID=? WHERE [Номер телефона]=?", (user_id, phone_number))
            conn.commit()
            await message.answer("Вы успешно зарегистрированы. Добро пожаловать!")
            await menu(message)

      
    # Закрытие соединения с базой данных
    cursor.close()
    conn.close()

@dp.message_handler(commands=['menu','m'])
async def menu(message: types.Message):
    """
    Обработчик команды /menu.
    Проверяет наличие пользователя с указанным ID в базе данных и показывает меню, если пользователь существует.
    Если пользователь не найден, выполняет команду /start.
    """
    user_id = message.from_user.id
    # Подключение к базе данных Access
    conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=C:\dev\progect_telega\База Данных Коледжа.accdb;')
    conn = pyodbc.connect(conn_str)

    # Проверка наличия пользователя в базе данных
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Студенты WHERE ID=?", (user_id,))
    result = cursor.fetchone()

    if result:
     # Создание главного меню
        menu_keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Создание кнопок
        button1 = InlineKeyboardButton("Общяя Информация 🗃", callback_data="button1")
        button2 = InlineKeyboardButton("Расписание 📋", callback_data="button2")
        button3 = InlineKeyboardButton("Успеваемость 📕", callback_data="button3")
        button4 = InlineKeyboardButton("Договоры 📝", callback_data="button4")
        button5 = InlineKeyboardButton("Приказы 📂", callback_data="button5")

        # Добавление кнопок в меню
        menu_keyboard.add(button1)
        menu_keyboard.add(button2,button3,button4,button5)

        # Отправка меню пользователю
        await message.answer("Чтобы вызвать это меню напишите /menu или /m\n\nВыберите пункт меню:", reply_markup=menu_keyboard)
    else:
        # Пользователь не найден, выполняем команду /start
        await start(message)

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'button4')
async def handle_button1(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Подключение к базе данных Access
    conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=C:\dev\progect_telega\База Данных Коледжа.accdb;')
    conn = pyodbc.connect(conn_str)

    # Проверка наличия пользователя в таблице "Студенты"
    cursor = conn.cursor()
    cursor.execute("SELECT [Номер телефона] FROM Студенты WHERE ID=?", (user_id,))
    result = cursor.fetchone()

    if result:
        # Пользователь найден, получение номера телефона
        phone_number = result[0]
        # Проверка номера телефона в таблице "Общая информация"
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Контракты WHERE [Номер телефона] = ?", (phone_number,))
        info_result = cursor.fetchone()

        if info_result:
            # Извлечение данных из строки
            data1 = info_result[2]
            data2 = info_result[3]
            data3 = info_result[4]
            data4 = info_result[5]
            data5 = info_result[6]
            data6 = info_result[7]
            

            # Отправка данных пользователю
            response = f"🔖 Ваш действующий контракт:\n\nОрганизация: {data1}\n\nСпециальность: {data2}\n\nДата начала контракта: {data3}\n\nДата оканчания контракта: {data4}\n\nПериод оплаты: {data5}\n\nСтоимость оплаты: {data6}(теньге) "

            await bot.send_message(callback_query.from_user.id, response)
        else:
            await bot.send_message(callback_query.from_user.id, "Номер телефона не найден в таблице 'Общая информация'.")
    else:
        await bot.send_message(callback_query.from_user.id, "Пользователь не найден в таблице 'Студенты'.")

    # Завершаем обработку callback_query
    await callback_query.answer()

    cursor.close()
    conn.close()




@dp.callback_query_handler(lambda callback_query: callback_query.data == 'button5')
async def handle_button5(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Подключение к базе данных Access
    conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=C:\dev\progect_telega\База Данных Коледжа.accdb;')
    conn = pyodbc.connect(conn_str)

    # Проверка наличия пользователя в таблице "Студенты"
    cursor = conn.cursor()
    cursor.execute("SELECT [ФИО] FROM Студенты WHERE ID=?", (user_id,))
    result = cursor.fetchone()

    if result:
        # Пользователь найден, получение номера телефона
        phone_number = result[0]
        # Проверка номера телефона в таблице "Приказы"
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Приказы WHERE [ФИО] = ?", (phone_number,))
        orders = cursor.fetchall()

        if orders:
            # Извлечение данных из строк и формирование сообщения
            response = "🗄 Список приказов:\n\n"
            for order in orders:
                order_data = f"{order[1]}-{order[2]}\n{order[3]}({order[4]})\n\n"
                response += order_data

            await bot.send_message(callback_query.from_user.id, response)
        else:
            await bot.send_message(callback_query.from_user.id, "Номер телефона не найден в таблице 'Приказы'.")
    else:
        await bot.send_message(callback_query.from_user.id, "Пользователь не найден в таблице 'Студенты'.")

    # Завершаем обработку callback_query
    await callback_query.answer()

    cursor.close()
    conn.close()

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'button1')
async def handle_button1(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Подключение к базе данных Access
    conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=C:\dev\progect_telega\База Данных Коледжа.accdb;')
    conn = pyodbc.connect(conn_str)

    # Проверка наличия пользователя в таблице "Студенты"
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Студенты WHERE ID=?", (user_id,))
    result = cursor.fetchone()

    if result:
        # Извлечение данных из строки
        fio = result[1]
        group = result[2]
        specialization = result[3]
        department = result[4]
        organization = result[5]
        education_form = result[6]
        student_card_number = result[7]
        student_id_number = result[8]

        # Формирование сообщения с информацией о студенте
        response = f"📖 Информация о студенте:\n\n" \
                   f"ФИО: {fio}\n\n" \
                   f"Группа: {group}\n\n" \
                   f"Специальность: {specialization}\n\n" \
                   f"Отделение: {department}\n\n" \
                   f"Организация: {organization}\n\n" \
                   f"Форма обучения: {education_form}\n\n" \
                   f"Номер зачётки: {student_card_number}\n\n" \
                   f"Номер студенческого билета: {student_id_number}"

        await bot.send_message(callback_query.from_user.id, response)
    else:
        await bot.send_message(callback_query.from_user.id, "Пользователь не найден в таблице 'Студенты'.")

    # Завершаем обработку callback_query
    await callback_query.answer()

    cursor.close()
    conn.close()

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'button3')
async def handle_button3(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Подключение к базе данных Access
    conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=C:\dev\progect_telega\База Данных Коледжа.accdb;')
    conn = pyodbc.connect(conn_str)

    # Проверка наличия пользователя в таблице "Студенты"
    cursor = conn.cursor()
    cursor.execute("SELECT [ФИО] FROM Студенты WHERE ID=?", (user_id,))
    result = cursor.fetchone()

    if result:
        # Пользователь найден, получение номера телефона и ФИО
        fio = result[0]

        # Поиск строк с соответствующим ФИО в таблице "Успеваемость"
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Успеваемость WHERE [ФИО] = ?", (fio,))
        rows = cursor.fetchall()

        if rows:
            # Извлечение данных из строк
            response = ""
            semester_displayed = False  # Flag variable to track if "1 семестр 2022|2023" has been displayed

            for row in rows:
                # Форматирование данных из строки
                if not semester_displayed:
                    response += "🔔1 семестр 2022|2023\n"
                    semester_displayed = True

                order_data = f"{row[1]} ({row[2]})\n{row[3]}\n\n{row[4]}\n\n"
                response += order_data

            # Отправка данных пользователю
            await bot.send_message(callback_query.from_user.id, response)
        else:
            await bot.send_message(callback_query.from_user.id, f"ФИО '{fio}' не найдено в таблице 'Успеваемость'.")
    else:
        await bot.send_message(callback_query.from_user.id, "Пользователь не найден в таблице 'Студенты'.")

    # Завершаем обработку callback_query
    await callback_query.answer()

    cursor.close()
    conn.close()

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'button2')
async def handle_button3(callback_query: types.CallbackQuery):
    # Path to the PDF file
    file_path = r'C:\dev\progect_telega\Расписание занятий_2полугодие.pdf'

    # Check if the file exists
    if os.path.exists(file_path):
        # Send the PDF file as a document
        await bot.send_document(callback_query.from_user.id, open(file_path, 'rb'), caption="Расписание занятий")
    else:
        await bot.send_message(callback_query.from_user.id, "The schedule file is not available.")

    # Complete the callback_query processing
    await callback_query.answer()

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'asis_action1')
async def handle_button11(callback_query: types.CallbackQuery):
    response_text = """
    При поступлении в "Музыкальный колледж музыкальная школа-интернат для одаренных детей" возникают различные вопросы. Вот некоторые из самых часто задаваемых вопросов и ответы на них:

    1. Какие программы обучения доступны в колледже?
       В нашем колледже доступны различные программы обучения, включая профессиональное музыкальное образование, специализированные курсы по инструментам, вокалу, композиции и дирижированию, а также общее среднее образование с углубленным изучением музыки.

    2. Каковы требования для поступления?
       Требования для поступления могут различаться в зависимости от выбранной программы обучения. Обычно они включают предварительное исполнение музыкального произведения на выбранном инструменте или вокале, а также сдачу вступительных экзаменов по музыкальной теории и слуху.

    3. Какие возможности для развития музыкальных навыков предоставляет колледж?
       В колледже мы предлагаем студентам широкий спектр возможностей для развития и совершенствования музыкальных навыков. Это включает индивидуальные занятия с опытными преподавателями, участие в оркестрах, ансамблях и хорах, проведение концертов и мастер-классов с известными музыкантами.

    4. Каковы условия проживания в школе-интернате?
       Школа-интернат предоставляет комфортные условия проживания для студентов. Все ученики имеют возможность проживать в общежитии, где они получают необходимый комфорт и заботу. Общежитие оснащено всем необходимым для комфортного проживания, включая общие зоны отдыха, столовую и спортивные площадки.

    5. Какие дополнительные возможности доступны студентам?
       Наш колледж предлагает студентам различные дополнительные возможности для расширения их музыкальных горизонтов. Это включает участие в конкурсах и фестивалях, концертные выступления за пределами колледжа, участие в мастер-классах и семинарах с приглашенными специалистами, а также доступ к библиотеке и ресурсам для изучения музыки.

    Обратите внимание, что конкретные вопросы и ответы могут различаться в зависимости от политики и программ обучения в вашем конкретном колледже. Рекомендуется обратиться в официальные источники информации или связаться с администрацией колледжа для получения точной и актуальной информации о поступлении и обучении.
    """

    await bot.send_message(callback_query.from_user.id, response_text)

    # Завершаем обработку callback_query
    await callback_query.answer()


# Define the states for the conversation
class ApplicationForm(StatesGroup):
    NAME = State()
    BIRTHDATE = State()
    PHONE = State()
    EMAIL = State()
    INSTRUMENT = State()
    EDUCATION = State()
    ACHIEVEMENTS = State()
    MOTIVATION = State()

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'asis_action2')
async def handle_button22(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()

    # Access the message from the callback query
    message = callback_query.message
    await message.answer(
        "Чтобы подать заявление о приеме, пожалуйста, предоставьте следующую информацию:"
        "\n\n1. Полное имя (имя,фамилия и отчество):"
    )
    await ApplicationForm.NAME.set()


@dp.message_handler(state=ApplicationForm.NAME)
async def collect_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["name"] = message.text

    await message.answer("2. Дата рождения (Год-Месяц-День):")
    await ApplicationForm.BIRTHDATE.set()


@dp.message_handler(state=ApplicationForm.BIRTHDATE)
async def collect_birthdate(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["birthdate"] = message.text

    await message.answer("3. Номер контактного телефона:")
    await ApplicationForm.PHONE.set()


@dp.message_handler(state=ApplicationForm.PHONE)
async def collect_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["phone"] = message.text

    await message.answer("4. Адрес электронной почты (необязательно):")
    await ApplicationForm.EMAIL.set()


@dp.message_handler(state=ApplicationForm.EMAIL)
async def collect_email(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["email"] = message.text

    await message.answer("5. Предпочитаемая профессия поступления:")
    await ApplicationForm.INSTRUMENT.set()


@dp.message_handler(state=ApplicationForm.INSTRUMENT)
async def collect_instrument(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["instrument"] = message.text

    await message.answer("6. Образование:")
    await ApplicationForm.EDUCATION.set()


@dp.message_handler(state=ApplicationForm.EDUCATION)
async def collect_education(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["education"] = message.text

    await message.answer("7. Музыкальные или другие достижения:")
    await ApplicationForm.ACHIEVEMENTS.set()


@dp.message_handler(state=ApplicationForm.ACHIEVEMENTS)
async def collect_achievements(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["achievements"] = message.text

    await message.answer("8. Мотивационное письмо (необязательно):")
    await ApplicationForm.MOTIVATION.set()


@dp.message_handler(state=ApplicationForm.MOTIVATION)
async def collect_motivation(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["motivation"] = message.text

    # Process the collected data (optional step)
    collected_data = "\n".join([f"{key}: {value}" for key, value in data.items()])

    # Sending the collected data via email (optional)
    # Replace the placeholder values with your own email configuration
    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = "smtp.mail.ru"
    email_subject = "Application Data"

    msg = EmailMessage()
    msg.set_content(collected_data)
    msg["Subject"] = email_subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL(smtp_server, 465) as server:
            server.login(sender_email, email_password)
            server.send_message(msg)

        await state.finish()
        await message.answer(
            "Спасибо за предоставленную информацию. Ваше заявление было подано!"
        )

    except smtplib.SMTPException:
        await message.answer(
            "При отправке сообщения произошла ошибка. Пожалуйста, повторите попытку позже."
        )

    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

    # Finish the conversation and reset the state
    await state.finish()
# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
