import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    email = Column(String, unique=True, index=True)

    orders = relationship("Order", back_populates="user")


class Food(Base):
    __tablename__ = "food"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    price = Column(Float)

    orders = relationship("Order", back_populates="food")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    food_id = Column(Integer, ForeignKey("food.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="orders")
    food = relationship("Food", back_populates="orders")


DATABASE_URL = "sqlite:///example.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    users = [
        User(name="Alice", age=30, email="alice@example.com"),
        User(name="Bob", age=25, email="bob@example.com"),
        User(name="Charlie", age=35, email="charlie@example.com"),
    ]
    session.add_all(users)
    session.commit()

    foods = [
        Food(name="Pizza Margherita", price=12.5),
        Food(name="Spaghetti Carbonara", price=15.0),
        Food(name="Lasagne", price=14.0),
    ]
    session.add_all(foods)
    session.commit()

    orders = [
        Order(food_id=1, user_id=1),
        Order(food_id=2, user_id=1),
        Order(food_id=3, user_id=2),
    ]
    session.add_all(orders)
    session.commit()

    session.close()
    print("Datenbank wurde erfolgreich erweitert und mit Beispieldaten gefüllt.")


if __name__ == "__main__":
    if not os.path.exists("example.db"):
        init_db()
    else:
        print("Die Datenbank 'example.db' existiert bereits.")
