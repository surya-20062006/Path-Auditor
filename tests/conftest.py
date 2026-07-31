import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.models.schema import Base, User, UserRole
from backend.auth.jwt import create_access_token, get_password_hash
from database.postgres import get_db
from backend.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(db_session):
    user = User(
        email="test_admin@traceai.enterprise",
        role=UserRole.ADMIN.value,
        password_hash=get_password_hash("Admin123!")
    )
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": user.id, "role": user.role})


@pytest.fixture
def auditor_token(db_session):
    user = User(
        email="test_auditor@traceai.enterprise",
        role=UserRole.AUDITOR.value,
        password_hash=get_password_hash("Auditor123!")
    )
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": user.id, "role": user.role})


@pytest.fixture
def customer_token(db_session):
    user = User(
        email="test_customer@traceai.enterprise",
        role=UserRole.CUSTOMER.value,
        password_hash=get_password_hash("Customer123!")
    )
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": user.id, "role": user.role})
