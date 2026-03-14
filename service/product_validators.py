from data.product_repository import get_product_by_id
from data.banned_names_repository import get_banned_names_phrases
from data.category_repository import get_category_by_id

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
