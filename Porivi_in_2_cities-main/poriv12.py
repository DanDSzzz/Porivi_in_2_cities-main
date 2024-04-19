from datetime import time
import numpy as np
import tensorflow as tf
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import openpyxl
from sklearn.tree import plot_tree

# Загрузка данных и предварительная обработка (необходимо адаптировать пути к файлам)
data = pd.read_excel('Poriv.xlsx', engine='openpyxl')
data2 = pd.read_excel('Poriv2.xlsx', engine='openpyxl')

common_columns = list(set(data.columns) & set(data2.columns))

for column in common_columns:
    data[column] = data[column].astype(str)
    data2[column] = data2[column].astype(str)

merged_data_by_common_columns = pd.merge(data, data2, how='outer', on=common_columns)

selected_columns = [
    "Утонение стенки, %",
    "Наличие других порывов на участке, К2",
    "Коррозионная активность грунта, К3",
    "Наличие/отсутсвие затопления (следов затопления) канала, К4",
    "Наличие пересечений с коммуникациями, К5",
    "Ki (действ)"
]

df_common = merged_data_by_common_columns[selected_columns].copy()
# df_common['Утонение стенки, %'] = df_common['Утонение стенки, %'].astype(float).round().astype(int)
# print(df_common['Утонение стенки, %'])
# Превращаем колонки в числовой тип
df_common['Утонение стенки, %'] = pd.to_numeric(df_common['Утонение стенки, %'], errors='coerce')
# df_common['Утонение стенки, %'].fillna(df_common['Утонение стенки, %'].mean(), inplace=True)
# df_common['Утонение стенки, %'] = df_common['Утонение стенки, %'].round().astype('int8')
df = df_common.dropna(subset=['Утонение стенки, %'], inplace=True)
df_common['Ki (действ)'] = pd.to_numeric(df_common['Ki (действ)'], errors='coerce')
# Кодируем строковые признаки
df_common['Наличие других порывов на участке, К2'] = df_common['Наличие других порывов на участке, К2'].astype('category')
df_common['Наличие других порывов на участке, К2'] = df_common['Наличие других порывов на участке, К2'].cat.codes
df_common['Коррозионная активность грунта, К3'] = df_common['Коррозионная активность грунта, К3'].astype('category')
df_common['Коррозионная активность грунта, К3'] = df_common['Коррозионная активность грунта, К3'].cat.codes
df_common['Наличие/отсутсвие затопления (следов затопления) канала, К4'] = df_common['Наличие/отсутсвие затопления (следов затопления) канала, К4'].astype('category')
df_common['Наличие/отсутсвие затопления (следов затопления) канала, К4'] = df_common['Наличие/отсутсвие затопления (следов затопления) канала, К4'].cat.codes
df_common['Наличие пересечений с коммуникациями, К5'] = df_common['Наличие пересечений с коммуникациями, К5'].astype('category')
df_common['Наличие пересечений с коммуникациями, К5'] = df_common['Наличие пересечений с коммуникациями, К5'].cat.codes
print(df_common['Наличие других порывов на участке, К2'])

for column in df_common.columns:
        df_common[column] = pd.to_numeric(df_common[column], errors='ignore')
for column in df_common.columns:
    if df_common[column].dtype in ['int64', 'float64'] and df_common[column].isnull().any():
        mean_value = df_common[column].mean()
        df_common.loc[:, column] = df_common[column].fillna(mean_value)
    elif df_common[column].dtype == 'object' and df_common[column].isnull().any():
        mode_value = df_common[column].mode()[0]
        df_common.loc[:, column] = df_common[column].fillna(mode_value)

for column in df_common.columns:
    if df_common[column].dtype == 'object':
        df_common.loc[:, column] = df_common[column].astype('category')


print(df_common.info())
print(df_common.shape)

corr_matrix = df_common.corr()
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(14, 10))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm', cbar=True)
plt.title('Матрица корреляции')
plt.show()
# Гистограммы для непрерывных признаков
df_common.hist(bins=15, figsize=(15, 10))
plt.suptitle('Гистограммы распределения признаков')
plt.show()

# Ящики с усами для категориальных признаков
plt.figure(figsize=(10, 6))
for index, feature in enumerate(["Утонение стенки, %", "Наличие других порывов на участке, К2", "Коррозионная активность грунта, К3", "Наличие/отсутсвие затопления (следов затопления) канала, К4", "Наличие пересечений с коммуникациями, К5"]):
    plt.subplot(2, 3, index + 1)
    sns.boxplot(x=df_common[feature])
plt.tight_layout

X = df_common.drop('Ki (действ)'  , axis=1)  # 'y' замените на имя вашей целевой колонки
y = df_common['Ki (действ)']  # 'y' замените на имя вашей целевой колонки


scaler = MinMaxScaler()
features_scaled = scaler.fit_transform(df_common)
# Разделение на обучающий и тестовый наборы
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Дополнительное разделение обучающего набора на обучающий и валидационный наборы
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=42)  # 0.25 x 0.8 = 0.2

model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation='relu', input_dim=5),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(1)
])
model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae', 'mape'])
# model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.2)

history = model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_val, y_val))

# Получение истории потерь и MAE
loss = history.history['loss']
val_loss = history.history['val_loss']
mae = history.history['mae']
val_mae = history.history['val_mae']
epochs = range(1, len(loss) + 1)

# График потерь
plt.figure(figsize=(14, 5))
plt.subplot(1, 2, 1)
plt.plot(epochs, loss, 'bo', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()

# График MAE
plt.subplot(1, 2, 2)
plt.plot(epochs, mae, 'ro', label='Training MAE')
plt.plot(epochs, val_mae, 'r', label='Validation MAE')
plt.title('Training and validation MAE')
plt.xlabel('Epochs')
plt.ylabel('MAE')
plt.legend()

# plt.tight_layout()
plt.show()
single_row = X.iloc[0]
print(single_row)
# Задаем средние значения для каждой колонки
means = {
    "Утонение стенки, %": 2.300000,
    "Наличие других порывов на участке, К2": 2.000000,
    "Коррозионная активность грунта, К3": 2.000000,
    "Наличие/отсутсвие затопления (следов затопления) канала, К4": 2.000000,
    "Наличие пересечений с коммуникациями, К5": 2.000000
}

# Задаем небольшое стандартное отклонение для генерации близких значений
std_dev = 0.1

# Создаем датафрейм с 5 строками, значения каждой колонки генерируются вокруг среднего
df = pd.DataFrame({col: np.random.normal(mean, std_dev, 5) for col, mean in means.items()})

# Создание датафрейма с данными
data = {
    "Утонение стенки, %": np.random.normal(2.3, 0.1, 5),
    "Наличие других порывов на участке, К2": np.random.normal(2, 0.1, 5),
    "Коррозионная активность грунта, К3": np.random.normal(2, 0.1, 5),
    "Наличие/отсутсвие затопления (следов затопления) канала, К4": np.random.normal(2, 0.1, 5),
    "Наличие пересечений с коммуникациями, К5": np.random.normal(2, 0.1, 5),
}

df_predict = pd.DataFrame(data)

# Выводим созданный датафрейм
print(df)
predictions = model.predict(df_predict)

# Вывод предсказаний
print(predictions)
# Оценка производительности модели на тестовых данных
test_loss, test_mae, test_mape = model.evaluate(X_test, y_test)

# from sklearn.metrics import mean_absolute_percentage_error
#
# mape = mean_absolute_percentage_error(y_test, predictions)
# print('MAPE:', mape)
print(f'Test Loss: {test_loss}, Test MAE: {test_mae}, Test MAPE: {test_mape}')

model = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', Ridge())  # Изначально выбран Ridge, можно менять
])

# Параметры для GridSearchCV
params = {
    'regressor': [Lasso(), Ridge(), ElasticNet()],
    'regressor__alpha': [0.01, 0.1, 1, 10, 100],  # alpha - гиперпараметр для регуляризации
    # 'regressor__l1_ratio': [0.1, 0.5, 0.9]  # Только для ElasticNet
}

# Создание GridSearchCV
# Настройка GridSearchCV с несколькими метриками
scoring = {
    'MAE': 'neg_mean_absolute_error',
    'MAPE': 'neg_mean_absolute_percentage_error'
}
grid = GridSearchCV(model, params, cv=5, scoring=scoring, refit='MAE', return_train_score=True)
grid.fit(X_train, y_train)

# Вывод результатов
best_params = grid.best_params_
best_score = -grid.best_score_

print("Лучшие параметры:", best_params)
print("Лучшая оценка (MSE):", best_score)
for scorer in scoring:
    key = f"mean_test_{scorer}"
    print(f"{scorer}: {-grid.cv_results_[key][grid.best_index_]}")

# Пайплайн для Gradient Boosting
gb_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', GradientBoostingRegressor())
])

# Пайплайн для Random Forest
rf_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', RandomForestRegressor())
])

# Параметры для GridSearchCV Gradient Boosting
gb_params = {
    'regressor__n_estimators': [100, 200, 300],
    'regressor__learning_rate': [0.01, 0.1, 0.2],
    'regressor__max_depth': [3, 5, 7]
}

# Параметры для GridSearchCV Random Forest
rf_params = {
    'regressor__n_estimators': [100, 200, 300],
    'regressor__max_features': ['auto', 'sqrt', 'log2'],
    'regressor__max_depth': [5, 10, 15]
}

# Создание и выполнение GridSearchCV для Gradient Boosting
gb_grid = GridSearchCV(gb_pipeline, gb_params, cv=5, scoring='neg_mean_absolute_percentage_error')
gb_grid.fit(X_train, y_train)

# Создание и выполнение GridSearchCV для Random Forest
rf_grid = GridSearchCV(rf_pipeline, rf_params, cv=5, scoring='neg_mean_absolute_percentage_error')
rf_grid.fit(X_train, y_train)

# Вывод результатов для Gradient Boosting
print("Лучшие параметры для Gradient Boosting:", gb_grid.best_params_)
print("Лучшая оценка MAPE для Gradient Boosting:", -gb_grid.best_score_)

# Вывод результатов для Random Forest
print("Лучшие параметры для Random Forest:", rf_grid.best_params_)
print("Лучшая оценка MAPE для Random Forest:", -rf_grid.best_score_)

# Извлекаем лучшую модель
best_rf = rf_grid.best_estimator_.named_steps['regressor']
# Предполагаем, что вы уже имеете переменные gb_best_score и rf_best_score с результатами
models = ['Gradient Boosting', 'Random Forest']
mape_scores = [-gb_grid.best_score_, -rf_grid.best_score_]  # используйте реальные значения из вашего GridSearchCV

plt.figure(figsize=(10, 6))
plt.bar(models, mape_scores, color=['blue', 'green'])
plt.xlabel('Model')
plt.ylabel('MAPE')
plt.title('Best MAPE Scores for Gradient Boosting and Random Forest')
plt.ylim(min(mape_scores) - 0.01, max(mape_scores) + 0.01)  # Небольшое пространство для лучшей визуализации
plt.show()
# Отрисовка первого дерева из лучшей модели
fig, ax = plt.subplots(figsize=(200, 200))
plot_tree(best_rf.estimators_[0], filled=True, feature_names=df_common.columns.tolist(), ax=ax, fontsize=10, max_depth=4, node_ids=True)
plt.show()

# ridge_weights = ridge.coef_
# lasso_weights = lasso.coef_
# elastic_net_weights = elastic_net.coef_
# rf_feature_importances = random_forest.feature_importances_
# gb_feature_importances = gradient_boosting.feature_importances_
# print("Ridge weights:", ridge_weights)
# print("Lasso weights:", lasso_weights)
# print("ElasticNet weights:", elastic_net_weights)
# print("Random Forest feature importances:", rf_feature_importances)
# print("Gradient Boosting feature importances:", gb_feature_importances)
# def plot_feature_importances(importances, feature_names):
#     indices = np.argsort(importances)
#     plt.figure(figsize=(8, 6))
#     plt.title('Feature Importances')
#     plt.barh(range(len(indices)), importances[indices], color='b', align='center')
#     plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
#     plt.xlabel('Relative Importance')
#     plt.show()
#
# plot_feature_importances(rf_feature_importances, X.columns)
# plot_feature_importances(gb_feature_importances, X.columns)