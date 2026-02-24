import random
import string
from locust import HttpUser, task, between, tag
from locust.exception import RescheduleTask

class GlossaryUser(HttpUser):
    """
    Пользователь, работающий с API глоссария.
    Основная активность: чтение терминов, реже — создание/изменение/удаление.
    """
    wait_time = between(0.5, 3)  # Пауза между задачами от 0.5 до 3 секунд

    def on_start(self):
        """
        Выполняется при старте каждой сессии пользователя.
        Получаем список существующих терминов для последующих операций.
        """
        self.terms_list = []
        self.update_terms_list()

    def update_terms_list(self):
        """Обновляет локальный список терминов с сервера."""
        with self.client.get("/terms", catch_response=True) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.terms_list = [item['term'] for item in data]
            else:
                # Если не удалось получить список, временно сохраняем пустой массив
                self.terms_list = []
                resp.failure(f"Не удалось получить список терминов: {resp.status_code}")

    def random_term(self):
        """Возвращает случайный существующий термин или None, если список пуст."""
        if self.terms_list:
            return random.choice(self.terms_list)
        return None

    @tag("read")
    @task(10)  # Вес 10 – высокая частота
    def get_all_terms(self):
        """Получение всех терминов (упрощённый вид)"""
        self.client.get("/terms", name="GET /terms")

    @tag("read")
    @task(8)
    def get_specific_term(self):
        """Получение детальной информации о случайном термине"""
        term = self.random_term()
        if term:
            self.client.get(f"/terms/{term}", name="GET /terms/{term}")
        else:
            # Если нет терминов, пропускаем задачу, но можно залогировать
            pass

    @tag("write")
    @task(3)
    def create_term(self):
        """Создание нового термина с уникальным именем"""
        # Генерируем уникальное имя
        new_term = "test_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        definition = f"Определение для {new_term}"
        sources = ["https://example.com", "https://test.org"]
        related = []  # Можно связать со случайными существующими терминами

        payload = {
            "term": new_term,
            "definition": definition,
            "sources": sources,
            "related_terms": related
        }
        with self.client.post("/terms", json=payload, catch_response=True, name="POST /terms") as resp:
            if resp.status_code == 201:
                # Добавляем новый термин в локальный список
                self.terms_list.append(new_term)
                resp.success()
            elif resp.status_code == 400 and "already exists" in resp.text:
                # Иногда имя может совпасть (очень редко), тогда пропускаем как успех без добавления
                resp.success()
            else:
                resp.failure(f"Ошибка создания термина: {resp.status_code}")

    @tag("write")
    @task(2)
    def update_term(self):
        """Обновление случайного существующего термина"""
        term = self.random_term()
        if not term:
            return

        # Не обновляем тестовые термины, чтобы не потерять предопределённые данные?
        # Можно обновлять только те, которые были созданы нами (начинаются с test_)
        # или обновлять любые, но потом восстанавливать. Для простоты обновляем любые.
        new_definition = f"Обновлённое определение для {term} в {random.randint(1,1000)}"
        payload = {
            "term": term,  # имя не меняем
            "definition": new_definition,
            "sources": ["https://updated.com"],
            "related_terms": []
        }
        with self.client.put(f"/terms/{term}", json=payload, catch_response=True, name="PUT /terms/{term}") as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Ошибка обновления: {resp.status_code}")

    @tag("write")
    @task(1)
    def delete_term(self):
        """Удаление случайного термина (только из созданных тестовых, чтобы не удалить важные)"""
        # Фильтруем только термины, начинающиеся с test_
        test_terms = [t for t in self.terms_list if t.startswith("test_")]
        if not test_terms:
            # Если нет тестовых терминов, создадим один перед удалением
            self.create_term()
            test_terms = [t for t in self.terms_list if t.startswith("test_")]
            if not test_terms:
                return  # всё ещё нет – выходим

        term_to_delete = random.choice(test_terms)
        with self.client.delete(f"/terms/{term_to_delete}", catch_response=True, name="DELETE /terms/{term}") as resp:
            if resp.status_code == 204:
                # Удаляем из локального списка
                self.terms_list.remove(term_to_delete)
                resp.success()
            else:
                resp.failure(f"Ошибка удаления: {resp.status_code}")

    def on_stop(self):
        """При завершении пользователя можно ничего не делать"""
        pass