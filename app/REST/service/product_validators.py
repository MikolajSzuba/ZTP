from app.REST.data.product_repository import get_product_by_id, get_product_by_name_and_category
from app.REST.data.banned_names_repository import get_banned_names_phrases
from app.REST.data.category_repository import get_category_by_id

class ValidationError(Exception):
    pass

class ConflictError(Exception):
    pass

class ResourceNotFoundError(Exception):
    pass

def validate_price_not_negative(price: int):
    if price <0:
        raise ValidationError("Cena nie moze byc ujemna")
    
def validate_category_exist(db, category_id: int):
    category = get_category_by_id(db, category_id)
    if category is None:
        raise ResourceNotFoundError("Kategoria nie istnieje")
    return category


def validate_product_banned_names(db, name: str):
    phrases= get_banned_names_phrases(db)
    name_lower=name.lower()
    for phrase in phrases:
        if phrase.lower() in name_lower:
            raise ValidationError("Nazwa zawiera zakazana fraze")


def validate_product_unique_name_in_category(
    db,
    name: str,
    category_id: int,
    product_id: int | None = None,
):
    existing_product = get_product_by_name_and_category(db, name, category_id)
    if existing_product is None:
        return

    if product_id is not None and existing_product.id == product_id:
        return

    raise ConflictError("Produkt o tej nazwie w tej kategorii juz istnieje")
