# Сервис обработки заказов

Стек:

```Python```
```FastAPI```
```PostgreSQL```
```SQLAlchemy```
```Docker```

Схема БД



#### Получение информации о сумме товаров заказанных под каждого клиента (Наименование клиента, сумма):

```sql
WITH order_sums AS (
  SELECT oi.order_id, oi.created_at, SUM(oi.amount * oi.price) AS order_sum
  FROM orderitem oi
  GROUP BY oi.order_id, oi.created_at
)
SELECT c.name, COALESCE(SUM(os.order_sum), 0) AS total_sum
FROM customer c
LEFT JOIN "order" o ON c.id = o.customer_id
LEFT JOIN order_sums os ON o.id = os.order_id AND o.created_at = os.created_at
GROUP BY c.id
ORDER BY total_sum DESC;
```
CTE order_sums для каждой позиции заказа (Orderitem) считает сумму заказа и агрегирует по уникальным заказам, определяемым сочетанием (order_id, created_at). Почему агрегируем по (order_id, created_at): таблица Order имеет составной ключ (id, created_at) и orderitem ссылается на оба поля. Поэтому чтобы корректно сопоставить агрегатную сумму с записью заказа, группируем по этим двум полям.

#### Найти количество дочерних элементов первого уровня вложенности для категорий номенклатуры:

```sql
SELECT c.id, c.name, (SELECT COUNT(*) 
FROM category child 
WHERE subpath(child.path, 0, nlevel(c.path)) = c.path 
AND nlevel(child.path) = nlevel(c.path) + 1
) AS direct_children_count 
FROM category c 
ORDER BY c.id;
```
child является непосредственным дочерним элементом, когда: 
+ subpath(child.path, 0, nlevel(c.path)) = c.path — префикс пути child длиной равной длине пути родителя совпадает с путём родителя;
+ nlevel(child.path) = nlevel(c.path) + 1 — глубина child ровно на единицу больше глубины родителя

Запрос использует Index Scan по nlevel(path)

#### Запрос для отчета «Топ-5 самых покупаемых товаров за последний месяц» (по количеству штук в заказах). В отчете должны быть: Наименование товара, Категория 1-го уровня, Общее количество проданных штук.

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS top_5_month_sellers AS
WITH sums AS (
SELECT oi.nomenclature_id, SUM(oi.amount) AS total_amount 
FROM orderitem oi 
JOIN "order" o ON o.id = oi.order_id 
WHERE o.created_at >= date_trunc('month', now()) - INTERVAL '1 month' 
AND o.created_at < date_trunc('month', now()) 
GROUP BY oi.nomenclature_id 
)
SELECT n.name, top_c.name AS category_name, s.total_amount 
FROM sums s 
JOIN nomenclature n ON n.id = s.nomenclature_id 
JOIN productcategory pc ON pc.nomenclature_id = n.id 
JOIN category c ON c.id = pc.category_id 
JOIN category top_c ON subpath(c.path,0,1)=top_c.path 
GROUP BY n.id, n.name, top_c.name, s.total_amount 
ORDER BY s.total_amount DESC 
LIMIT 5;
```
Что сделано для оптимизации этого запроса:
Партицианирование таблицы Order по месяцам.
Использовани LTree для хранения категорий ускоряет получение категории 1 уровня в отличие от других способов
Что еще можно сделать:
Партицианировать OrderItem вместе с Order, т.к узким местом запроса является агрегация OrderItem
Денормализация: хранить top_category_id в Nomenclature и индексировать его

## Установка

Клонировать репозиторий:
```
git clone https://github.com/kh199/add_product_to_order
```
Создать и заполнить файл .env на основе .env.template

Запустить docker-compose:
```
docker-compose up -d
```
:warning: Миграции могут занять несколько минут, т.к. происходит заполнение таблиц тестовыми данными

Документация доступна по адресу ```http://127.0.0.1:8001/docs```


## Методы API

+ **POST**   ```orders/add_product``` добавление товара в заказ
