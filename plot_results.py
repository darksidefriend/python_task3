import pandas as pd
import matplotlib.pyplot as plt

# history = pd.read_csv('light_stats_history.csv')
# stats = pd.read_csv('light_stats.csv')

history = pd.read_csv('stability_stats_history.csv')
stats = pd.read_csv('stability_stats.csv')

# Удаляем строки с NaN в процентилях (первые секунды без данных)
history = history.dropna(subset=['95%', '99%'])

# Преобразуем timestamp в читаемое время (секунды от начала теста)
history['Time_sec'] = history['Timestamp'] - history['Timestamp'].iloc[0]

# 2. График RPS и числа пользователей
fig, ax1 = plt.subplots(figsize=(10,5))

ax1.set_xlabel('Время, с')
ax1.set_ylabel('RPS', color='tab:blue')
ax1.plot(history['Time_sec'], history['Total Request Count'].diff().fillna(0), color='tab:blue', label='RPS')
ax1.tick_params(axis='y', labelcolor='tab:blue')

ax2 = ax1.twinx()
ax2.set_ylabel('Число пользователей', color='tab:red')
ax2.plot(history['Time_sec'], history['User Count'], color='tab:red', label='Users')
ax2.tick_params(axis='y', labelcolor='tab:red')

plt.title('Динамика нагрузки')
fig.tight_layout()
plt.savefig('rps_users.png', dpi=150)
plt.show()

# 3. График времени ответа (среднее и процентили)
plt.figure(figsize=(10,5))
plt.plot(history['Time_sec'], history['Total Average Response Time'], label='Avg', color='green')
plt.plot(history['Time_sec'], history['95%'], label='p95', color='orange')
plt.plot(history['Time_sec'], history['99%'], label='p99', color='red')
plt.xlabel('Время, с')
plt.ylabel('Время ответа, мс')
plt.title('Время ответа (агрегированное)')
plt.legend()
plt.grid(True)
plt.savefig('response_times.png', dpi=150)
plt.show()

# 4. Сравнение времени ответа по типам запросов (из stats.csv)
# Отфильтруем только строки с конкретными типами (не Aggregated)
endpoints = stats[stats['Type'] != 'Aggregated'].copy()

# Уберём дублирующую строку "GET /terms" с type=GET (оставим только с именем)
endpoints = endpoints[~((endpoints['Type']=='GET') & (endpoints['Name']=='/terms'))]

# После создания endpoints
endpoints = stats[stats['Type'] != 'Aggregated'].copy()

# Диагностика
print("Типы данных в колонке Name:", endpoints['Name'].dtype)
print("Уникальные значения Name:", endpoints['Name'].unique())
print("Количество пропусков в Name:", endpoints['Name'].isna().sum())
print("Пустые строки в Name:", (endpoints['Name'] == '').sum())

# Удаляем строки с пропущенным или пустым Name
endpoints = endpoints.dropna(subset=['Name'])
endpoints = endpoints[endpoints['Name'] != '']

# Если после этого остались проблемы, можно принудительно преобразовать в строку
endpoints['Name'] = endpoints['Name'].astype(str)


# 3. Среднее время по эндпоинтам
# Отфильтровываем агрегированную строку по Name
endpoints = stats[stats['Name'] != 'Aggregated'].copy()
# Убираем дублирующую строку с именем '/terms' (оставляем только 'GET /terms')
endpoints = endpoints[~((endpoints['Type']=='GET') & (endpoints['Name']=='/terms'))]

# Диагностика (можно удалить после проверки)
print("Очищенные данные:")
print(endpoints[['Type', 'Name']])

x = range(len(endpoints))
fig, ax = plt.subplots(figsize=(12,6))
ax.bar(x, endpoints['Average Response Time'], tick_label=endpoints['Type'] + ' ' + endpoints['Name'])
ax.set_ylabel('Среднее время ответа, мс')
ax.set_title('Среднее время ответа по эндпоинтам')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('avg_by_endpoint.png', dpi=150)
plt.close(fig)
print("Сохранён avg_by_endpoint.png")

# 4. Процентили по эндпоинтам
fig, ax = plt.subplots(figsize=(12,6))
bar_width = 0.25
x = range(len(endpoints))
ax.bar([i - bar_width for i in x], endpoints['95%'], bar_width, label='p95')
ax.bar(x, endpoints['99%'], bar_width, label='p99')
ax.bar([i + bar_width for i in x], endpoints['100%'], bar_width, label='max')
ax.set_xticks(x)
ax.set_xticklabels(endpoints['Type'] + ' ' + endpoints['Name'], rotation=45, ha='right')
ax.set_ylabel('Время ответа, мс')
ax.set_title('Процентили по эндпоинтам')
ax.legend()
plt.tight_layout()
plt.savefig('percentiles_by_endpoint.png', dpi=150)
plt.close(fig)
print("Сохранён percentiles_by_endpoint.png")