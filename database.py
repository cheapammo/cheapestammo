from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import logging
from config import DATABASE_URL

Base = declarative_base()

class Retailer(Base):
    __tablename__ = 'retailers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    website = Column(String(255), nullable=False)
    base_url = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    products = relationship("Product", back_populates="retailer")

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    retailer_id = Column(Integer, ForeignKey('retailers.id'), nullable=False)
    
    # Product Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    caliber = Column(String(50), nullable=False)
    grain_weight = Column(Integer)
    bullet_type = Column(String(50))  # FMJ, HP, SP, etc.
    manufacturer = Column(String(100))
    
    # Pricing Information
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)  # rounds per box/case
    price_per_round = Column(Float, nullable=False)
    
    # Availability
    in_stock = Column(Boolean, default=False)
    stock_quantity = Column(Integer)
    
    # Metadata
    product_url = Column(String(500))
    image_url = Column(String(500))
    sku = Column(String(100))
    
    # Tracking
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    last_scraped = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    retailer = relationship("Retailer", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")

class PriceHistory(Base):
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    price = Column(Float, nullable=False)
    price_per_round = Column(Float, nullable=False)
    in_stock = Column(Boolean, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    product = relationship("Product", back_populates="price_history")

class ScrapingLog(Base):
    __tablename__ = 'scraping_logs'
    
    id = Column(Integer, primary_key=True)
    retailer_id = Column(Integer, ForeignKey('retailers.id'), nullable=False)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(50))  # success, failed, partial
    products_found = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    products_new = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Relationship
    retailer = relationship("Retailer")

class DatabaseManager:
    def __init__(self, database_url=DATABASE_URL):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.logger = logging.getLogger(__name__)
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def add_retailer(self, name, website, base_url):
        """Add a new retailer to the database"""
        session = self.get_session()
        try:
            # Check if retailer already exists
            existing = session.query(Retailer).filter_by(name=name).first()
            if existing:
                return existing
            
            retailer = Retailer(
                name=name,
                website=website,
                base_url=base_url
            )
            session.add(retailer)
            session.commit()
            self.logger.info(f"Added retailer: {name}")
            return retailer
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error adding retailer {name}: {e}")
            raise
        finally:
            session.close()
    
    def upsert_product(self, product_data):
        """Insert or update product data"""
        session = self.get_session()
        try:
            # Try to find existing product
            existing = session.query(Product).filter_by(
                retailer_id=product_data['retailer_id'],
                name=product_data['name'],
                caliber=product_data['caliber']
            ).first()
            
            if existing:
                # Update existing product
                for key, value in product_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.last_updated = datetime.utcnow()
                existing.last_scraped = datetime.utcnow()
                
                # Add price history entry
                price_history = PriceHistory(
                    product_id=existing.id,
                    price=product_data['price'],
                    price_per_round=product_data['price_per_round'],
                    in_stock=product_data['in_stock']
                )
                session.add(price_history)
                
            else:
                # Create new product
                product = Product(**product_data)
                session.add(product)
                session.flush()  # Get the ID
                
                # Add initial price history
                price_history = PriceHistory(
                    product_id=product.id,
                    price=product_data['price'],
                    price_per_round=product_data['price_per_round'],
                    in_stock=product_data['in_stock']
                )
                session.add(price_history)
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error upserting product: {e}")
            return False
        finally:
            session.close()
    
    def log_scraping_session(self, retailer_id, status, products_found=0, products_updated=0, products_new=0, error_message=None):
        """Log scraping session results"""
        session = self.get_session()
        try:
            log_entry = ScrapingLog(
                retailer_id=retailer_id,
                completed_at=datetime.utcnow(),
                status=status,
                products_found=products_found,
                products_updated=products_updated,
                products_new=products_new,
                error_message=error_message
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error logging scraping session: {e}")
        finally:
            session.close()
    
    def get_products_by_caliber(self, caliber, limit=100):
        """Get products by caliber"""
        session = self.get_session()
        try:
            products = session.query(Product).filter_by(caliber=caliber).limit(limit).all()
            return products
        finally:
            session.close()
    
    def get_best_prices(self, caliber=None, limit=50):
        """Get best prices, optionally filtered by caliber"""
        session = self.get_session()
        try:
            query = session.query(Product).filter_by(in_stock=True)
            if caliber:
                query = query.filter_by(caliber=caliber)
            products = query.order_by(Product.price_per_round).limit(limit).all()
            return products
        finally:
            session.close()

# Initialize database manager
db_manager = DatabaseManager() 