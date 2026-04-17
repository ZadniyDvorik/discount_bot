from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from database import Session, Shop, Product, Promotion, User, add_promotion
from database import get_user_favorite_products_with_promotions
from datetime import datetime
import uvicorn

app = FastAPI(title="DiscountBot Admin Panel")

HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>DiscountBot Админ</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        a { display: block; margin: 10px 0; font-size: 18px; }
    </style>
</head>
<body>
    <h1>Админ-панель DiscountBot</h1>
    <ul>
        <li><a href="/add_promotion">Добавить акцию</a></li>
        <li><a href="/promotions_list">Список акций</a></li>
        <li><a href="/user_promotions">Акции на любимые товары пользователя</a></li>
    </ul>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def admin_home():
    return HTML_INDEX

@app.get("/add_promotion", response_class=HTMLResponse)
async def add_promotion_form():
    session = Session()
    shops = session.query(Shop).all()
    products = session.query(Product).all()
    session.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Добавить акцию</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            input, select { margin-bottom: 10px; padding: 5px; width: 300px; display: block; }
            button { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; margin-top: 10px; }
        </style>
    </head>
    <body>
        <h1>Добавить новую акцию</h1>
        <form method="post" action="/add_promotion">
            <label>Магазин:</label>
            <select name="shop_id">
    """
    
    for shop in shops:
        html += f'<option value="{shop.id}">{shop.name} — {shop.address}</option>'
    
    html += """
            </select>
            
            <label>Товар:</label>
            <select name="product_id">
    """
    
    for product in products:
        html += f'<option value="{product.id}">{product.name}</option>'
    
    html += """
            </select>
            
            <label>Старая цена (₽):</label>
            <input type="number" step="0.01" name="old_price" required>
            
            <label>Новая цена (₽):</label>
            <input type="number" step="0.01" name="new_price" required>
            
            <label>Дата окончания:</label>
            <input type="date" name="end_date" required>
            
            <button type="submit">Добавить акцию</button>
        </form>
        <br>
        <a href="/">На главную</a>
    </body>
    </html>
    """
    
    return HTMLResponse(html)

@app.post("/add_promotion")
async def add_promotion_submit(
    shop_id: int = Form(...),
    product_id: int = Form(...),
    old_price: float = Form(...),
    new_price: float = Form(...),
    end_date: str = Form(...)
):
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    add_promotion(shop_id, product_id, old_price, new_price, end_date_obj)
    
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Успешно</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            a { display: block; margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>Акция успешно добавлена!</h1>
        <a href="/add_promotion">Добавить ещё</a>
        <br>
        <a href="/">На главную</a>
    </body>
    </html>
    """)

@app.get("/promotions_list", response_class=HTMLResponse)
async def promotions_list():
    session = Session()
    promotions = session.query(Promotion, Shop, Product).\
        join(Shop, Promotion.shop_id == Shop.id).\
        join(Product, Promotion.product_id == Product.id).\
        order_by(Promotion.end_date).\
        all()
    session.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Список акций</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            a { display: inline-block; margin-top: 20px; }
            .delete-btn { color: red; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>Все акции</h1>
        <a href="/add_promotion">Добавить акцию</a>
        <a href="/" style="margin-left: 20px;">На главную</a>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Магазин</th>
                    <th>Товар</th>
                    <th>Старая цена</th>
                    <th>Новая цена</th>
                    <th>Дата окончания</th>
                    <th>Удалить</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for promo, shop, product in promotions:
        html += f"""
            <tr>
                <td>{promo.id}</td>
                <td>{shop.name}</td>
                <td>{product.name}</td>
                <td>{promo.old_price:.0f} ₽</td>
                <td>{promo.new_price:.0f} ₽</td>
                <td>{promo.end_date.strftime('%d.%m.%Y')}</td>
                <td><a href="/delete_promotion/{promo.id}" class="delete-btn" onclick="return confirm('Удалить акцию?')">Удалить</a></td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    return HTMLResponse(html)


@app.get("/delete_promotion/{promotion_id}")
async def delete_promotion(promotion_id: int):
    from database import Session, Promotion
    session = Session()
    promo = session.query(Promotion).filter_by(id=promotion_id).first()
    if promo:
        session.delete(promo)
        session.commit()
    session.close()
    return RedirectResponse(url="/promotions_list", status_code=303)

@app.get("/user_promotions", response_class=HTMLResponse)
async def user_promotions(user_id: int = None):
    session = Session()
    users = session.query(User).all()
    session.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Акции на любимые товары пользователя</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            select, button { padding: 8px; font-size: 16px; margin-top: 10px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            a { display: inline-block; margin-top: 20px; }
            .error { color: red; }
            .info { color: blue; }
        </style>
    </head>
    <body>
        <h1>Акции на любимые товары пользователя</h1>
        <form method="get" action="/user_promotions">
            <label>Выберите пользователя:</label>
            <select name="user_id">
    """
    
    for user in users:
        selected = "selected" if user_id == user.telegram_id else ""
        html += f'<option value="{user.telegram_id}" {selected}>{user.first_name} (@{user.username})</option>'
    
    html += """
            </select>
            <button type="submit">Показать</button>
        </form>
        <hr>
    """
    
    if user_id:
        try:
            promotions, user = get_user_favorite_products_with_promotions(user_id)
            
            if user is None:
                html += '<p>Пользователь не найден</p>'
            elif not promotions:
                html += f'<p>У пользователя {user.first_name} нет любимых товаров или нет акций на них.</p>'
            else:
                html += f"<h3>Пользователь: {user.first_name} (@{user.username})</h3>"
                html += """
                <table>
                    <thead>
                        <tr>
                            <th>Товар</th>
                            <th>Магазин</th>
                            <th>Старая цена</th>
                            <th>Новая цена</th>
                            <th>Скидка</th>
                            <th>Дата окончания</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for promo, shop, product in promotions:
                    discount = int((1 - promo.new_price / promo.old_price) * 100) if promo.old_price else 0
                    html += f"""
                        <tr>
                            <td>{product.name}</td>
                            <td>{shop.name} ({shop.address})</td>
                            <td>{promo.old_price:.0f} ₽</td>
                            <td>{promo.new_price:.0f} ₽</td>
                            <td>-{discount}%</td>
                            <td>{promo.end_date.strftime('%d.%m.%Y')}</td>
                        </tr>
                    """
                html += "</tbody></table>"
        except Exception as e:
            html += f'<p>Ошибка: {str(e)}</p>'
    
    html += """
        <br>
        <a href="/">На главную</a>
    </body>
    </html>
    """
    
    return HTMLResponse(html)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)