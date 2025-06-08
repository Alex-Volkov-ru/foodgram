from django.core.management.base import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Create test users with real names'

    def handle(self, *args, **kwargs):
        test_users = [
            {"email": "vasya@example.com",
             "username": "vasya", "first_name": "Вася",
             "last_name": "Иванов"},
            {"email": "alla@example.com",
             "username": "alla", "first_name": "Алла",
             "last_name": "Гручнева"},
            {"email": "petr@example.com",
             "username": "petr", "first_name": "Пётр",
             "last_name": "Сидоров"},
            {"email": "elena@example.com",
             "username": "elena", "first_name": "Елена",
             "last_name": "Кузнецова"},
            {"email": "igor@example.com",
             "username": "igor", "first_name": "Игорь",
             "last_name": "Дьяков"},
            {"email": "maria@example.com",
             "username": "maria", "first_name": "Мария",
             "last_name": "Лебедева"},
            {"email": "nikolay@example.com",
             "username": "nikolay", "first_name": "Николай",
             "last_name": "Поляков"},
            {"email": "sveta@example.com",
             "username": "sveta", "first_name": "Светлана",
             "last_name": "Орлова"},
            {"email": "andrey@example.com",
             "username": "andrey", "first_name": "Андрей",
             "last_name": "Волков"},
            {"email": "olga@example.com",
             "username": "olga", "first_name": "Ольга",
             "last_name": "Фролова"},
        ]

        password = 'qweasdzxc'

        for data in test_users:
            if not CustomUser.objects.filter(email=data['email']).exists():
                user = CustomUser.objects.create_user(
                    email=data['email'],
                    username=data['username'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(
                    f'User {user.email} created.'))
            else:
                self.stdout.write(self.style.WARNING(
                    f'User {data["email"]} already exists.'))
