from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta

engine = create_engine('sqlite:///discount_bot.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    registered_at = Column(DateTime, default=datetime.now)

class Shop(Base):
    __tablename__ = 'shops'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)

class UserShop(Base):
    __tablename__ = 'user_shops'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    shop_id = Column(Integer, ForeignKey('shops.id'))
    added_at = Column(DateTime, default=datetime.now)

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)

class FavoriteProduct(Base):
    __tablename__ = 'favorite_products'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    added_at = Column(DateTime, default=datetime.now)

class Promotion(Base):
    __tablename__ = 'promotions'
    
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey('shops.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    old_price = Column(Float)
    new_price = Column(Float)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Integer, default=1)

Base.metadata.create_all(engine)

def get_user(telegram_id: int):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user

def add_user(telegram_id: int, username: str, first_name: str):
    print(f"✔️ add_user вызван: id={telegram_id}, name={first_name}")
    session = Session()
    try:
        existing = session.query(User).filter_by(telegram_id=telegram_id).first()
        if existing:
            print(f"✔️ Пользователь уже существует: {existing.id}")
            session.close()
            return existing
        
        user = User(telegram_id=telegram_id, username=username, first_name=first_name)
        session.add(user)
        session.commit()
        print(f"✔️ Пользователь добавлен! ID в БД: {user.id}")
    except Exception as e:
        print(f"✔️ Ошибка при добавлении пользователя: {e}")
        session.rollback()
    finally:
        session.close()
    
    check_session = Session()
    check_user = check_session.query(User).filter_by(telegram_id=telegram_id).first()
    check_session.close()
    print(f"✔️ Проверка после добавления: {check_user}")
    
    return check_user

def find_shops_by_name(query: str):
    session = Session()
    shops = session.query(Shop).filter(Shop.name.contains(query)).all()
    session.close()
    return shops

def delete_user_shop(user_id: int, shop_id: int):
    session = Session()
    session.query(UserShop).filter_by(user_id=user_id, shop_id=shop_id).delete()
    session.commit()
    session.close()

def add_shop(name: str, address: str, lat: float, lon: float):
    session = Session()
    shop = Shop(name=name, address=address, latitude=lat, longitude=lon)
    session.add(shop)
    session.commit()
    session.close()
    return shop

def get_all_shops():
    session = Session()
    shops = session.query(Shop).all()
    session.close()
    return shops

def add_user_shop(user_id: int, shop_id: int):
    session = Session()
    existing = session.query(UserShop).filter_by(user_id=user_id, shop_id=shop_id).first()
    if not existing:
        user_shop = UserShop(user_id=user_id, shop_id=shop_id)
        session.add(user_shop)
        session.commit()
    session.close()

def get_user_shops(user_id: int):
    session = Session()
    shops = session.query(Shop).join(UserShop).filter(UserShop.user_id == user_id).all()
    session.close()
    return shops

def get_all_products():
    session = Session()
    products = session.query(Product).all()
    session.close()
    return products

def find_products_by_name(query: str):
    session = Session()
    products = session.query(Product).filter(Product.name.contains(query)).all()
    session.close()
    return products

def add_product(name: str, category: str = ""):
    session = Session()
    product = Product(name=name, category=category)
    session.add(product)
    session.commit()
    session.close()
    return product

def add_user_product(user_id: int, product_id: int):
    session = Session()
    existing = session.query(FavoriteProduct).filter_by(user_id=user_id, product_id=product_id).first()
    if not existing:
        fav = FavoriteProduct(user_id=user_id, product_id=product_id)
        session.add(fav)
        session.commit()
    session.close()

def get_user_products(user_id: int):
    session = Session()
    products = session.query(Product).join(FavoriteProduct).filter(FavoriteProduct.user_id == user_id).all()
    session.close()
    return products

def delete_user_product(user_id: int, product_id: int):
    session = Session()
    session.query(FavoriteProduct).filter_by(user_id=user_id, product_id=product_id).delete()
    session.commit()
    session.close()

def get_user_shops_with_coords(user_id: int):
    session = Session()
    shops = session.query(Shop).join(UserShop).filter(UserShop.user_id == user_id).all()
    session.close()
    return [s for s in shops if s.latitude and s.longitude]

def add_promotion(shop_id: int, product_id: int, old_price: float, new_price: float, end_date: datetime):
    session = Session()
    promo = Promotion(
        shop_id=shop_id,
        product_id=product_id,
        old_price=old_price,
        new_price=new_price,
        end_date=end_date
    )
    session.add(promo)
    session.commit()
    session.close()
    return promo

def get_active_promotions():
    session = Session()
    promotions = session.query(Promotion).filter(Promotion.is_active == 1).all()
    session.close()
    return promotions

def get_promotions_for_user(user_id: int):
    session = Session()
    user_shops = session.query(Shop).join(UserShop).filter(UserShop.user_id == user_id).all()
    shop_ids = [s.id for s in user_shops]
    
    promotions = session.query(Promotion, Shop, Product).\
        join(Shop, Promotion.shop_id == Shop.id).\
        join(Product, Promotion.product_id == Product.id).\
        filter(Promotion.shop_id.in_(shop_ids)).\
        filter(Promotion.is_active == 1).\
        all()
    session.close()
    return promotions

def get_users_by_product(product_id: int):
    session = Session()
    users = session.query(User).join(FavoriteProduct).filter(FavoriteProduct.product_id == product_id).all()
    session.close()
    return users

def get_new_promotions_since(last_check_time: datetime):
    session = Session()
    new_promotions = session.query(Promotion, Shop, Product).\
        join(Shop, Promotion.shop_id == Shop.id).\
        join(Product, Promotion.product_id == Product.id).\
        filter(Promotion.created_at > last_check_time).\
        filter(Promotion.is_active == 1).\
        all()
    session.close()
    return new_promotions

def get_users_for_product(product_id: int):
    session = Session()
    users = session.query(User).join(FavoriteProduct).filter(FavoriteProduct.product_id == product_id).all()
    session.close()
    return users

def get_expiring_promotions():
    session = Session()
    now = datetime.now()
    tomorrow_date = (now + timedelta(days=1)).date()
    
    expiring = session.query(Promotion, Shop, Product).\
        join(Shop, Promotion.shop_id == Shop.id).\
        join(Product, Promotion.product_id == Product.id).\
        filter(Promotion.end_date >= tomorrow_date).\
        filter(Promotion.end_date < tomorrow_date + timedelta(days=1)).\
        filter(Promotion.is_active == 1).\
        all()
    session.close()
    return expiring

def get_user_favorite_products_with_promotions(user_telegram_id: int):
    session = Session()
    
    user = session.query(User).filter_by(telegram_id=user_telegram_id).first()
    if not user:
        session.close()
        return [], None
    
    favorite_products = session.query(Product).join(FavoriteProduct).filter(FavoriteProduct.user_id == user.id).all()
    product_ids = [p.id for p in favorite_products]
    
    if not product_ids:
        session.close()
        return [], user
    
    promotions = session.query(Promotion, Shop, Product).\
        join(Shop, Promotion.shop_id == Shop.id).\
        join(Product, Promotion.product_id == Product.id).\
        filter(Promotion.product_id.in_(product_ids)).\
        filter(Promotion.is_active == 1).\
        all()
    
    session.close()
    return promotions, user