import uuid
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert
from sqlalchemy import event

# Ensure tests can import `main` when pytest runs from parent directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Use local sqlite database for tests to avoid external DB dependency.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
# Avoid background worker thread in tests.
os.environ["DISABLE_NOTIFICATION_WORKER"] = "1"

from main import app
from app.REST.data.database import engine, get_db, SessionLocal
from app.REST.model.banned_names_orm import BannedNamesORM
from app.REST.model.category_orm import CategoryORM
from app.REST.model.product_history_orm import ProductHistoryORM
from app.REST.model.product_orm import ProductORM
from app.REST.data.database import Base


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
	Base.metadata.drop_all(bind=engine)
	Base.metadata.create_all(bind=engine)
	with SessionLocal() as db:
		db.execute(
			insert(CategoryORM),
			[
				{"id": 1, "name": "Elektronika"},
				{"id": 2, "name": "Spozywcze"},
				{"id": 3, "name": "Meble"},
			],
		)
		db.execute(
			insert(BannedNamesORM),
			[
				{"name": "Zakazany produkt"},
				{"name": "Nielegalne"},
				{"name": "Fake"},
			],
		)
		db.commit()
	yield
	Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
	"""
	Przygotowuje sesję bazy danych dla testu.
	Każdy test działa w jednej transakcji, która na końcu zostaje cofnięta.
	Dzięki temu testy nie zostawiają danych w bazie.
	"""
	connection = engine.connect()
	outer_transaction = connection.begin()
	session = SessionLocal(bind=connection)
	nested_transaction = connection.begin_nested()

	@event.listens_for(session, "after_transaction_end")
	def restart_savepoint(sess, transaction):
		nonlocal nested_transaction

		if not nested_transaction.is_active:
			nested_transaction = connection.begin_nested()

	try:
		yield session

	finally:
		session.close()
		outer_transaction.rollback()
		connection.close()


@pytest.fixture(scope="function")
def client(db_session):
	"""
	Nadpisuje zależność get_db tak, aby endpointy FastAPI używały sesji testowej.
	Dzięki temu również wewnętrzne commit() wykonywane przez repozytorium
	pozostają zamknięte w transakcji testowej i zostaną cofnięte po teście.
	"""

	def override_get_db():
		try:
			yield db_session
		finally:
			pass

	app.dependency_overrides[get_db] = override_get_db

	try:
		yield TestClient(app)
	finally:
		app.dependency_overrides.clear()


@pytest.fixture
def unique_product_name() -> str:
	"""Generuje unikalną nazwę produktu dla testów."""
	return f"TestProduct-{uuid.uuid4().hex[:8]}".upper()

