# Консольний бот помічник

import re
import pickle
from collections import UserDict
from datetime import datetime, timedelta
from functools import wraps


# декоратор input_error для обробки помилок
def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            return str(error)
        except IndexError as error:
            return str(error) if str(error) else "Введіть ім'я."
        except KeyError:
            return "Контакт не знайдено."
    return inner


class Field:
    # Батьківський клас для полів Name і Phone
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    # Клас наслідує конструктор і методи Field
    pass


class Phone(Field):
    # Клас наслідує конструктор і методи Field
    # екземпляр Field створюється тільки після валідації
    def __init__(self, value):
        if self.phone_validation(value):
            super().__init__(value)
        else:
            raise ValueError("Телефон повинен мати 10 цифр.")

    # перевірка на 10 цифр
    def phone_validation(self, phone_number: str) -> bool:
        return bool(re.fullmatch(r"\d{10}", phone_number))


class Birthday(Field):
    def __init__(self, value: str):
        try:
            birthday = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Некоректна дата. Введіть DD.MM.YYYY")

        super().__init__(birthday)
        # Рядок перетворено в об`єкт date, який передано в Field
        # Якщо формат даних не правильний - виведеться ValueError


class Record:
    # Клас для зберігання інформації про контакт, включно з іменем та списком телефонів.
    def __init__(self, name: str):
        # Магічний метод конструктор нового екземпляра
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def __str__(self) -> str:
        # Магічний метод представлення строкою
        return f"Ім'я контакта: {self.name.value}, номер: {'; '.join(p.value for p in self.phones)}"

    def add_birthday(self, birthday: str) -> None:
        # метод створення об'єкта Birthday та додавання дати народження до запису
        self.birthday = Birthday(birthday)

    def add_phone(self, phone_number: str) -> None:
        # метод додавання номера телефона
        self.phones.append(Phone(phone_number))


    def find_phone(self, phone_number: str) -> Phone | None:
        # метод пошуку об'єктів Phone
        for phone_el in self.phones:
            if phone_el.value == phone_number:
                return phone_el
        return None


    def edit_phone(self, current_phone_number: str, new_phone_number: str) -> None:
        # метод редагування номера телефона
        phone_record = self.find_phone(current_phone_number)
        if phone_record:
            phone_index = self.phones.index(phone_record)
            self.phones[phone_index] = Phone(new_phone_number)
        else:
            raise ValueError(f"Номер телефона {current_phone_number} відсутній.")


    def remove_phone(self, phone_number: str) -> None:
        # метод видалення номера телефона
        phone_record = self.find_phone(phone_number)
        if phone_record:
            self.phones.remove(phone_record)
        else:
            raise ValueError(f"Номер телефона {phone_number} відсутній.")


class AddressBook(UserDict):
    # Клас для зберігання записів та керування ними

    def add_record(self, record: Record) -> None:
        # Метод додає запис до self.data
        self.data[record.name.value] = record

    def find(self, name: str) -> Record | None:
        # Метод пошуку запису за ім'ям
        return self.data.get(name)

    def delete(self, name: str) -> None:
        # Метод видалення запису за ім'ям
        if name in self.data:
            del self.data[name]
        else:
            raise ValueError(f"Запис {name} відсутній.")

    # метод отримання дат днів народження адаптований для роботи з об'єктами
    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        congratulation_list = []

        for record in self.data.values():
            # Пропускаємо контакти без дати народження
            if record.birthday is None:
                continue
            birthday_date = record.birthday.value

            # Дата дня народження у поточному році
            congratulation_date = datetime(year=today.year, month=birthday_date.month,
                                           day=birthday_date.day).date()

            # Якщо день народження цього року вже минув переносимо перевірку на наступний рік
            if congratulation_date < today:
                congratulation_date = datetime(year=today.year+1, month=birthday_date.month,
                                               day=birthday_date.day).date()

            # Перевіряємо, чи входить дата у наступні 7 днів
            if congratulation_date - today <= timedelta(days=7):

                # Якщо субота — переносимо привітання на понеділок
                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)

                # Якщо неділя — переносимо привітання на понеділок
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                congratulation_list.append({
                    "name": record.name.value,
                    "birthday": birthday_date.strftime("%d.%m.%Y"),
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                })

        return congratulation_list   # повертаємо список словників


# save_data функція зберігання даних у файл addressbook.pkl
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


# load_data функція завантаження даних з файла addressbook.pkl
def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено


# парсинг вводу користувача на команду і список аргументів
def parse_input(user_input):

    if not user_input.strip():
        return "", []

    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


# add_contact функція додавання нового контакта AddressBook
@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Введіть ім'я і номер телефона.")
    name, phone, *_ = args
    record = book.find(name)
    message = "Контакт оновлено."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Контакт додано."
    if phone:
        record.add_phone(phone)
    return message


# change_contact функція зміни номера телефона вказаного контакта AddressBook
@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise ValueError("Введіть ім'я, старий номер телефона, новий номер телефона.")
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    else:
        record.edit_phone(old_phone, new_phone)
    return "Контакт оновлено."


# функція виводу номера телефона по заданому імені контакта AddressBook
@input_error
def show_phone(args, book: AddressBook):
    if not args:
        raise IndexError
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    if not record.phones:
        return "Номерів телефона не знайдено."
    return "; ".join(phone.value for phone in record.phones)


# функція виводу всіх номерів телефонів
@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "Контакти не знайдено."
    return "\n".join(str(record) for record in book.data.values())


# функція запису дня народження контакта
@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Введіть ім'я і дату в форматі DD.MM.YYYY.")
    name, birthday = args[0], args[1]
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(birthday)
    return "День народження додано."


# функція виводу дня народження
@input_error
def show_birthday(args, book: AddressBook):
    if not args:
        raise IndexError
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday is None:
        return "День народження не знайдено."
    return record.birthday.value.strftime("%d.%m.%Y")


# функція виводу днів народження на наступний тиждень
@input_error
def birthdays(args, book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "Днів народження нема."
    birthday_list = []
    for item in upcoming_birthdays:
        line = f"{item['name']}: {item['congratulation_date']}"
        birthday_list.append(line)
    return "\n".join(birthday_list)


# головна функція
def main():
    # contacts = {}
    book = load_data()
    # debugging(book)

    print("Бот-асистент Вас вітає!")
    while True:
        user_input = input("Введіть команду: ")
        command, *args = parse_input(user_input)

        # обробка заданих команд
        if command in ["close", "exit"]:
            save_data(book)  # Викликати перед виходом з програми
            print("Роботу завершено!")
            break

        elif command == "hello":
            print("Чим можу допомогти?")

            # Довідка по командам бота для користувача
        elif command == "help":
            print(
                "Список і формат команд: \n\n"
                "help                       - вивести список команд\n"
                "add username phone         - додати номер телефона контакта\n"
                "change username phone new_phone - змінити номер телефона контакта\n"
                "phone username             - показати номер телефона контакта\n"
                "all                        - показати всі номери телефонів\n"
                "add-birthday name DD.MM.YYYY - додати день народження контакта \n"
                "show-birthday username     - показати день народження контакта\n"
                "birthdays                  - показати дні народження на наступний тиждень\n"
                "close                      - закрити програму\n"
                "exit                       - вийти з програми\n"
            )


            # Команда "add [ім'я] [номер телефона]"
        elif command == "add":
            # Виконати add_contact() і вивести підтвердження
            print(add_contact(args, book))

            # Команда "change [ім'я] [новий номер телефона]"
        elif command == "change":
            # Виконати change_contact()) і вивести підтвердження
            print(change_contact(args, book))

            # Команда "phone [ім'я]"
        elif command == "phone":
            # Виконати show_phone() і вивести підтвердження
            print(show_phone(args, book))

            # Команда "all"
        elif command == "all":
            # Виконати show_all() і вивести підтвердження
            print(show_all(book))

            # Команда "add-birthday"
        elif command == "add-birthday":
            print(add_birthday(args, book))

            # Команда "show-birthday"
        elif command == "show-birthday":
            print(show_birthday(args, book))

            # Команда "birthdays"
        elif command == "birthdays":
            print(birthdays(args, book))

        else: # неправильно введені команди
            print("Invalid command.")


if __name__ == "__main__":
    main()
