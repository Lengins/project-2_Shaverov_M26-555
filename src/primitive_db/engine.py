def welcome() -> None:
    """Первая попытка запустить проект: баннер и цикл команд."""
    print("Первая попытка запустить проект!")
    print()

    while True:
        print("***")
        print("<command> exit - выйти из программы")
        print("<command> help - справочная информация")

        command = input("Введите команду: ").strip()

        if command == "exit":
            print("Выход из программы.")
            break
        elif command == "help":
            print("Справка: доступны команды help и exit.")
        else:
            print(f"Неизвестная команда: {command}")